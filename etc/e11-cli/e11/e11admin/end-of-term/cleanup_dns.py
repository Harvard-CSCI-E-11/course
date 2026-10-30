#!/usr/bin/env python3
# Plan end-of-course DNS deletions from the protected Route 53 export.
# The keep-list contains DNS names and shell globs; every other name is selected.
# Complete AWS record sets are retained so aliases and routing fields survive.
# Planning is offline and saves exactly the changes displayed to the operator.
# Applying rechecks the keep-list, account, zone, and current records before writes.
# Bounded Route 53 batches are submitted and awaited until they become INSYNC.
# Progress counts completed deletions; a fresh inventory gives the zone remainder.
"""Plan and delete Route 53 records not matched by the DNS keep-list."""

from __future__ import annotations

import argparse
from fnmatch import fnmatchcase
import json
import sys
from pathlib import Path
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from pydantic import BaseModel, ConfigDict, ValidationError

NAME = "Name"
TYPE = "Type"
TTL = "TTL"
RECORDS = "ResourceRecords"
ALIAS = "AliasTarget"
VALUE = "Value"
ACTION = "Action"
RESOURCE_RECORD_SET = "ResourceRecordSet"
RESOURCE_RECORD_SETS = "ResourceRecordSets"
SET_IDENTIFIER = "SetIdentifier"
TRAFFIC_POLICY_INSTANCE_ID = "TrafficPolicyInstanceId"
CHANGE_INFO = "ChangeInfo"
ID = "Id"
ACCOUNT = "Account"
HOSTED_ZONE = "HostedZone"
CHANGES = "Changes"
IS_TRUNCATED = "IsTruncated"
NEXT_TOKEN = "NextToken"
MAX_ELEMENTS = 1000
MAX_VALUE_CHARS = 32000


class CleanupError(ValueError):
    """The proposed DNS cleanup is incomplete or unsafe."""


class CleanupPlan(BaseModel):
    """Reviewed metadata and exact Route 53 API changes."""

    model_config = ConfigDict(extra="forbid")
    domain: str
    zone_id: str
    account_id: str
    keep_patterns: list[str]
    changes: list[dict[str, Any]]


def normalize(name: str) -> str:
    return name.strip().lower().rstrip(".") + "."


def keep_patterns(path: Path, domain: str) -> list[str]:
    suffix = normalize(domain)
    patterns = sorted({
        normalize(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    })
    if any(pattern != suffix and not pattern.endswith("." + suffix) for pattern in patterns):
        raise CleanupError("keep-list patterns must belong to the requested zone")
    if not _kept(suffix, patterns):
        raise CleanupError("keep-list must protect the zone apex (including its NS and SOA records)")
    return patterns


def _kept(name: str, patterns: list[str]) -> bool:
    return any(fnmatchcase(normalize(name), pattern) for pattern in patterns)


def _validate_record(record: dict[str, Any], domain: str) -> None:
    name = record.get(NAME)
    record_type = record.get(TYPE)
    if not isinstance(name, str) or not isinstance(record_type, str):
        raise CleanupError("record lacks a name or type")
    suffix = normalize(domain)
    if normalize(name) == suffix or not normalize(name).endswith("." + suffix):
        raise CleanupError(f"record is outside deletable subdomains: {name}")
    if record_type == "SOA" or TRAFFIC_POLICY_INSTANCE_ID in record:
        raise CleanupError(f"record needs separate handling: {name} {record_type}")
    if (ALIAS in record) == (RECORDS in record):
        raise CleanupError(f"record needs exactly one alias or value list: {name}")
    if RECORDS in record and (TTL not in record or not record[RECORDS]):
        raise CleanupError(f"record needs TTL and values: {name}")


def build_plan(
    records: list[dict[str, Any]], patterns: list[str], domain: str,
    zone_id: str, account_id: str,
) -> CleanupPlan:
    """Keep complete record sets so Route 53 can delete routed and alias records."""
    suffix = normalize(domain)
    for record in records:
        name = normalize(record[NAME])
        if name != suffix and not name.endswith("." + suffix):
            raise CleanupError(f"zone export contains a record outside {suffix}: {name}")
    selected = [record for record in records if not _kept(record[NAME], patterns)]
    for record in selected:
        _validate_record(record, domain)
    selected.sort(key=lambda record: (normalize(record[NAME]), record[TYPE], record.get(SET_IDENTIFIER, "")))
    keys = [(normalize(record[NAME]), record[TYPE], record.get(SET_IDENTIFIER)) for record in selected]
    if len(keys) != len(set(keys)):
        raise CleanupError("zone export contains duplicate record sets")
    changes = [{ACTION: "DELETE", RESOURCE_RECORD_SET: record} for record in selected]
    plan = CleanupPlan(domain=suffix, zone_id=zone_id.removeprefix("/hostedzone/"),
                       account_id=account_id, keep_patterns=patterns, changes=changes)
    batches(plan.changes)
    return plan


def batches(changes: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    """Honor both Route 53 request limits, including multi-value records."""
    result: list[list[dict[str, Any]]] = []
    batch: list[dict[str, Any]] = []
    elements = characters = 0
    for change in changes:
        record = change[RESOURCE_RECORD_SET]
        values = record.get(RECORDS, [])
        count = len(values) if values else 1
        length = sum(len(value[VALUE]) for value in values)
        if count > MAX_ELEMENTS or length > MAX_VALUE_CHARS:
            raise CleanupError(f"record exceeds Route 53 batch limits: {record[NAME]}")
        if batch and (elements + count > MAX_ELEMENTS or characters + length > MAX_VALUE_CHARS):
            result.append(batch)
            batch = []
            elements = characters = 0
        batch.append(change)
        elements += count
        characters += length
    if batch:
        result.append(batch)
    return result


def _list_records(client: Any, zone_id: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for page in client.get_paginator("list_resource_record_sets").paginate(HostedZoneId=zone_id):
        records.extend(page[RESOURCE_RECORD_SETS])
    return records


def _client(profile: str | None, zone_id: str, domain: str, account_id: str) -> Any:
    session = boto3.Session(profile_name=profile)
    actual_account = session.client("sts").get_caller_identity()[ACCOUNT]
    if actual_account != account_id:
        raise CleanupError(f"AWS account mismatch: expected {account_id}, got {actual_account}")
    client = session.client("route53")
    zone = client.get_hosted_zone(Id=zone_id)[HOSTED_ZONE]
    if normalize(zone[NAME]) != normalize(domain) or zone[ID].split("/")[-1] != zone_id:
        raise CleanupError("hosted zone name or ID does not match the request")
    return client


def _read_plan(path: Path, patterns: list[str]) -> CleanupPlan:
    plan = CleanupPlan.model_validate_json(path.read_bytes())
    if plan.keep_patterns != patterns:
        raise CleanupError("keep-list changed; run dns-plan again before deleting")
    for change in plan.changes:
        if set(change) != {ACTION, RESOURCE_RECORD_SET} or change[ACTION] != "DELETE":
            raise CleanupError("plan contains a non-delete or incomplete change")
        record = change[RESOURCE_RECORD_SET]
        _validate_record(record, plan.domain)
        if _kept(record[NAME], patterns):
            raise CleanupError(f"plan would delete a kept name: {record[NAME]}")
    rebuilt = build_plan([change[RESOURCE_RECORD_SET] for change in plan.changes],
                         patterns, plan.domain, plan.zone_id, plan.account_id)
    if plan != rebuilt:
        raise CleanupError("plan is inconsistent; run dns-plan again before deleting")
    return plan


def _matching_records(plan: CleanupPlan, current: list[dict[str, Any]]) -> None:
    names = {normalize(change[RESOURCE_RECORD_SET][NAME]) for change in plan.changes}
    planned = [change[RESOURCE_RECORD_SET] for change in plan.changes]
    live = [record for record in current if normalize(record[NAME]) in names]
    def canonical(records: list[dict[str, Any]]) -> list[str]:
        return sorted(json.dumps(record, sort_keys=True) for record in records)

    if canonical(planned) != canonical(live):
        raise CleanupError("live records changed after the plan was written; export the zone and plan again")


def apply_plan(client: Any, plan: CleanupPlan) -> None:
    """Validate all planned names before submitting the first deletion batch."""
    current = _list_records(client, plan.zone_id)
    _matching_records(plan, current)
    change_batches = batches(plan.changes)
    total = len(plan.changes)
    deleted = 0
    batch_label = "batch" if len(change_batches) == 1 else "batches"
    print(f"Deleting {total} record sets in {len(change_batches)} {batch_label}; "
          f"{len(current) - total} expected to remain in zone.", flush=True)
    for batch in change_batches:
        response = client.change_resource_record_sets(
            HostedZoneId=plan.zone_id, ChangeBatch={CHANGES: batch}
        )
        change_id = response[CHANGE_INFO][ID]
        print(f"Submitted change {change_id}: {len(batch)} record sets; waiting for INSYNC", flush=True)
        client.get_waiter("resource_record_sets_changed").wait(Id=change_id)
        deleted += len(batch)
        print(f"INSYNC {change_id}; deleted {deleted}/{total}; "
              f"{total - deleted} remaining to delete.", flush=True)
    remaining = len(_list_records(client, plan.zone_id))
    print(f"Done: deleted {deleted} record sets; {remaining} remain in zone.", flush=True)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--domain", required=True)
    parser.add_argument("--zone-id", required=True)
    parser.add_argument("--account-id", required=True)
    parser.add_argument("--profile", help="AWS profile; defaults to normal AWS resolution")
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--plan", type=Path, help="write the displayed deletion plan")
    actions.add_argument("--apply-plan", type=Path, help="delete records in the saved plan")
    parser.add_argument("--keep", type=Path, required=True, help="names and shell globs to preserve")
    parser.add_argument("--zone-export", type=Path, help="offline Route 53 zone export for planning")
    return parser.parse_args()


def main() -> int:
    args = _arguments()
    try:
        args.zone_id = args.zone_id.removeprefix("/hostedzone/")
        patterns = keep_patterns(args.keep, args.domain)
        if args.plan:
            if not args.zone_export:
                raise CleanupError("planning requires --zone-export from step 3")
            if args.plan.resolve() in {args.zone_export.resolve(), args.keep.resolve()}:
                raise CleanupError("plan path must not overwrite the zone export or keep-list")
            export = json.loads(args.zone_export.read_text(encoding="utf-8"))
            if export.get(IS_TRUNCATED) or export.get(NEXT_TOKEN):
                raise CleanupError("zone export is truncated; export the complete zone before planning")
            plan = build_plan(export[RESOURCE_RECORD_SETS], patterns,
                              args.domain, args.zone_id, args.account_id)
            args.plan.write_text(plan.model_dump_json(indent=2) + "\n", encoding="utf-8")
            print(f"Plan: {args.plan}; record sets to delete: {len(plan.changes)}; "
                  f"record sets to keep: {len(export[RESOURCE_RECORD_SETS]) - len(plan.changes)}")
            for change in plan.changes:
                record = change[RESOURCE_RECORD_SET]
                identifier = record.get(SET_IDENTIFIER, "")
                print(f"WILL DELETE {record[NAME]} {record[TYPE]} {identifier}".rstrip())
            return 0
        if args.zone_export:
            raise CleanupError("deletion uses the saved plan; --zone-export is for planning only")
        plan = _read_plan(args.apply_plan, patterns)
        if (plan.domain, plan.zone_id, plan.account_id) != (
            normalize(args.domain), args.zone_id, args.account_id
        ):
            raise CleanupError("plan domain, hosted zone, or AWS account does not match")
        if not plan.changes:
            print("No record sets to delete.")
            return 0
        client = _client(args.profile, args.zone_id, args.domain, args.account_id)
        apply_plan(client, plan)
        return 0
    except (CleanupError, OSError, ValueError, KeyError, TypeError,
            ValidationError, BotoCoreError, ClientError) as error:
        print(f"DNS cleanup failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
