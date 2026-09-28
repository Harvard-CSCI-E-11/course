#!/usr/bin/env python3
"""Plan and apply explicitly reviewed Route 53 student-record deletions."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from pydantic import BaseModel, ConfigDict, Field, ValidationError

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
    changes: list[dict[str, Any]] = Field(min_length=1)


def normalize(name: str) -> str:
    return name.strip().lower().rstrip(".") + "."


def student_names(path: Path, domain: str) -> set[str]:
    suffix = normalize(domain)
    names = {
        normalize(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    if not names or any(
        name == suffix or not name.endswith("." + suffix) or "*" in name
        for name in names
    ):
        raise CleanupError("names file must contain only student subdomains of the zone")
    return names


def _validate_record(record: dict[str, Any], domain: str) -> None:
    name = record.get(NAME)
    record_type = record.get(TYPE)
    if not isinstance(name, str) or not isinstance(record_type, str):
        raise CleanupError("record lacks a name or type")
    suffix = normalize(domain)
    if normalize(name) == suffix or not normalize(name).endswith("." + suffix):
        raise CleanupError(f"record is outside student subdomains: {name}")
    if record_type in {"NS", "SOA"} or TRAFFIC_POLICY_INSTANCE_ID in record:
        raise CleanupError(f"record needs separate handling: {name} {record_type}")
    if (ALIAS in record) == (RECORDS in record):
        raise CleanupError(f"record needs exactly one alias or value list: {name}")
    if RECORDS in record and (TTL not in record or not record[RECORDS]):
        raise CleanupError(f"record needs TTL and values: {name}")


def build_plan(
    records: list[dict[str, Any]], names: set[str], domain: str,
    zone_id: str, account_id: str,
) -> CleanupPlan:
    """Keep complete record sets so Route 53 can delete routed and alias records."""
    found = {normalize(record[NAME]) for record in records if normalize(record[NAME]) in names}
    missing = sorted(names - found)
    if missing:
        raise CleanupError(f"student names have no records: {', '.join(missing)}")
    selected = [record for record in records if normalize(record[NAME]) in names]
    for record in selected:
        _validate_record(record, domain)
    selected.sort(key=lambda record: (normalize(record[NAME]), record[TYPE], record.get(SET_IDENTIFIER, "")))
    keys = [(normalize(record[NAME]), record[TYPE], record.get(SET_IDENTIFIER)) for record in selected]
    if len(keys) != len(set(keys)):
        raise CleanupError("zone export contains duplicate record sets")
    changes = [{ACTION: "DELETE", RESOURCE_RECORD_SET: record} for record in selected]
    plan = CleanupPlan(domain=normalize(domain), zone_id=zone_id,
                       account_id=account_id, changes=changes)
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


def _read_plan(path: Path, expected_hash: str) -> CleanupPlan:
    content = path.read_bytes()
    actual_hash = hashlib.sha256(content).hexdigest()
    if actual_hash != expected_hash:
        raise CleanupError("plan SHA-256 does not match the reviewed file")
    plan = CleanupPlan.model_validate_json(content)
    names: set[str] = set()
    for change in plan.changes:
        if set(change) != {ACTION, RESOURCE_RECORD_SET} or change[ACTION] != "DELETE":
            raise CleanupError("plan contains a non-delete or incomplete change")
        record = change[RESOURCE_RECORD_SET]
        _validate_record(record, plan.domain)
        names.add(normalize(record[NAME]))
    if len(names) == 0:
        raise CleanupError("plan is empty")
    batches(plan.changes)
    return plan


def _matching_records(plan: CleanupPlan, current: list[dict[str, Any]]) -> None:
    names = {normalize(change[RESOURCE_RECORD_SET][NAME]) for change in plan.changes}
    planned = [change[RESOURCE_RECORD_SET] for change in plan.changes]
    live = [record for record in current if normalize(record[NAME]) in names]
    canonical = lambda records: sorted(json.dumps(record, sort_keys=True) for record in records)
    if canonical(planned) != canonical(live):
        raise CleanupError("live student records changed after the plan was written")


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--domain", required=True)
    parser.add_argument("--zone-id", required=True)
    parser.add_argument("--account-id", required=True)
    parser.add_argument("--profile", help="AWS profile; defaults to normal AWS resolution")
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--plan", type=Path, help="write a new dry-run plan file")
    actions.add_argument("--apply-plan", type=Path, help="apply an approved plan")
    parser.add_argument("--names", type=Path, help="explicit student names to delete")
    parser.add_argument("--zone-export", type=Path, help="offline Route 53 zone export for planning")
    parser.add_argument("--sha256", help="approved SHA-256 of the plan file")
    return parser.parse_args()


def main() -> int:
    args = _arguments()
    try:
        if args.plan:
            if not args.names or args.sha256:
                raise CleanupError("planning requires --names and forbids --sha256")
            if args.zone_export:
                export = json.loads(args.zone_export.read_text(encoding="utf-8"))
                records = export[RESOURCE_RECORD_SETS]
            else:
                client = _client(args.profile, args.zone_id, args.domain, args.account_id)
                records = _list_records(client, args.zone_id)
            plan = build_plan(records, student_names(args.names, args.domain),
                              args.domain, args.zone_id, args.account_id)
            with args.plan.open("x", encoding="utf-8") as stream:
                stream.write(plan.model_dump_json(indent=2) + "\n")
            digest = hashlib.sha256(args.plan.read_bytes()).hexdigest()
            print(f"Plan: {args.plan}; changes: {len(plan.changes)}; SHA-256: {digest}")
            for change in plan.changes:
                record = change[RESOURCE_RECORD_SET]
                print(f"DELETE {record[NAME]} {record[TYPE]}")
            return 0
        if args.zone_export or args.names or not args.sha256:
            raise CleanupError("apply requires --sha256 and forbids --zone-export/--names")
        plan = _read_plan(args.apply_plan, args.sha256)
        if (plan.domain, plan.zone_id, plan.account_id) != (
            normalize(args.domain), args.zone_id, args.account_id
        ):
            raise CleanupError("plan domain, hosted zone, or AWS account does not match")
        client = _client(args.profile, args.zone_id, args.domain, args.account_id)
        _matching_records(plan, _list_records(client, args.zone_id))
        for batch in batches(plan.changes):
            response = client.change_resource_record_sets(
                HostedZoneId=args.zone_id, ChangeBatch={CHANGES: batch}
            )
            change_id = response[CHANGE_INFO][ID]
            print(f"Submitted change {change_id}; waiting for INSYNC", flush=True)
            client.get_waiter("resource_record_sets_changed").wait(Id=change_id)
            print(f"INSYNC {change_id}", flush=True)
        return 0
    except (CleanupError, OSError, ValueError, KeyError, TypeError,
            ValidationError, BotoCoreError, ClientError) as error:
        print(f"DNS cleanup failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
