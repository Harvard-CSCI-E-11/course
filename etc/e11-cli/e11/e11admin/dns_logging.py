#!/usr/bin/env python3
# Manage public Route 53 query logging without importing the course application.
# Setup reuses the zone's log group, enforces Standard and 180-day retention,
# and grants Route 53 access through a policy scoped to the account and zone.
# Read-only commands show configuration, individual queries, or hostname totals.
# CloudWatch performs bounded historical queries; terminal output supports CSV.
# Verification sends one unique DNS query and waits for its actual log event.
# Existing AWS credentials are used; no login or course-data changes are performed.
"""Enable and inspect E11 public DNS query logging."""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import boto3
import dns.exception
import dns.resolver
from botocore.exceptions import BotoCoreError, ClientError
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from tabulate import tabulate

REGION = "us-east-1"
RETENTION_DAYS = 180
ACCOUNT = "Account"
HOSTED_ZONE = "HostedZone"
NAME = "Name"
CONFIG = "Config"
PRIVATE_ZONE = "PrivateZone"
DELEGATION_SET = "DelegationSet"
NAME_SERVERS = "NameServers"
QUERY_CONFIGS = "QueryLoggingConfigs"
LOG_GROUP_ARN = "CloudWatchLogsLogGroupArn"
LOG_GROUPS = "logGroups"
LOG_GROUP_NAME = "logGroupName"
LOG_GROUP_CLASS = "logGroupClass"
RETENTION = "retentionInDays"
STORED_BYTES = "storedBytes"
POLICIES = "resourcePolicies"
POLICY_NAME = "policyName"
POLICY_DOCUMENT = "policyDocument"
VERSION = "Version"
STATEMENT = "Statement"
SID = "Sid"
EFFECT = "Effect"
PRINCIPAL = "Principal"
SERVICE = "Service"
ACTION = "Action"
RESOURCE = "Resource"
CONDITION = "Condition"
ARN_EQUALS = "ArnEquals"
STRING_EQUALS = "StringEquals"
SOURCE_ARN = "aws:SourceArn"
SOURCE_ACCOUNT = "aws:SourceAccount"
QUERY_ID = "queryId"
STATUS = "status"
RESULTS = "results"
FIELD = "field"
VALUE = "value"
STATISTICS = "statistics"
BYTES_SCANNED = "bytesScanned"
EVENTS = "events"
MESSAGE = "message"
NEXT_TOKEN = "nextToken"


class LoggingError(ValueError):
    """Configuration or query results do not satisfy the requested operation."""


class Target(BaseModel):
    """Verified AWS destination, independent of environment-specific globals."""

    account_id: str
    zone_id: str
    domain: str
    log_group: str
    name_servers: list[str] = Field(default_factory=list)

    @property
    def log_arn(self) -> str:
        return f"arn:aws:logs:{REGION}:{self.account_id}:log-group:{self.log_group}"


class LoggingStatus(BaseModel):
    enabled: bool
    account_id: str
    zone_id: str
    domain: str
    region: str = REGION
    log_group: str
    log_class: str | None = None
    retention_days: int | None = None
    stored_bytes: int = 0


class QueryEvent(BaseModel):
    timestamp: datetime
    hostname: str
    query_type: str
    response_code: str
    resolver_ip: str


class HostnameReport(BaseModel):
    hostname: str
    last_seen: datetime
    queries: int
    nxdomain: int


class QueryOutput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    rows: list[QueryEvent | HostnameReport] = Field(default_factory=list)
    bytes_scanned: float = 0


def hostname(value: str, domain: str) -> str:
    """Accept a short name or an explicit name in this zone; reject query syntax."""
    value = value.strip().lower().rstrip(".")
    if "." not in value:
        value += "." + domain
    if not re.fullmatch(r"[a-z0-9_-]+(?:\.[a-z0-9_-]+)*", value):
        raise LoggingError("hostname contains invalid characters")
    if value != domain and not value.endswith("." + domain):
        raise LoggingError("hostname is outside the requested zone")
    return value


def query_text(target: Target, *, report: bool, name: str | None = None,
               student: str | None = None, limit: int = 100) -> str:
    clauses = [f"filter hostZoneId = {json.dumps(target.zone_id)}"]
    if name:
        pattern = re.escape(hostname(name, target.domain))
    elif student:
        stem = hostname(student, target.domain).removesuffix("." + target.domain)
        if "." in stem:
            raise LoggingError("student must be a single hostname stem")
        pattern = re.escape(stem) + r"(-lab[0-9]+)?\." + re.escape(target.domain)
    else:
        pattern = None
    if pattern:
        clauses.append(f"filter tolower(queryName) like /^{pattern}\\.?$/")
    if report:
        clauses.extend([
            'fields rtrim(tolower(queryName), ".") as hostname',
            "stats count(*) as queries, latest(queryTimestamp) as last_seen, "
            'sum(strcontains(responseCode, "NXDOMAIN")) as nxdomain by hostname',
            "sort last_seen desc",
        ])
    else:
        clauses.extend([
            "fields queryTimestamp as timestamp, queryName as hostname, queryType as query_type, "
            "responseCode as response_code, resolverIp as resolver_ip",
            "sort @timestamp desc",
        ])
    return " | ".join([*clauses, f"limit {limit}"])


class DnsLogging:
    """AWS operations with explicit clients for local contract tests."""

    def __init__(self, target: Target, route53: Any, logs: Any):
        self.target = target
        self.route53 = route53
        self.logs = logs

    def configuration(self) -> dict[str, Any] | None:
        configs = self.route53.list_query_logging_configs(HostedZoneId=self.target.zone_id)[QUERY_CONFIGS]
        if len(configs) > 1:
            raise LoggingError("hosted zone has multiple query logging configurations")
        return configs[0] if configs else None

    def group(self) -> dict[str, Any] | None:
        for page in self.logs.get_paginator("describe_log_groups").paginate(
            logGroupNamePrefix=self.target.log_group
        ):
            for group in page[LOG_GROUPS]:
                if group[LOG_GROUP_NAME] == self.target.log_group:
                    return group
        return None

    def _check_destination(self, config: dict[str, Any] | None) -> None:
        if config and config[LOG_GROUP_ARN] != self.target.log_arn:
            raise LoggingError("existing query logging uses a different destination; no changes made")

    def status(self) -> LoggingStatus:
        config = self.configuration()
        self._check_destination(config)
        group = self.group()
        return LoggingStatus(
            enabled=config is not None, account_id=self.target.account_id,
            zone_id=self.target.zone_id, domain=self.target.domain, log_group=self.target.log_group,
            log_class=group.get(LOG_GROUP_CLASS, "STANDARD") if group else None,
            retention_days=group.get(RETENTION) if group else None,
            stored_bytes=group.get(STORED_BYTES, 0) if group else 0,
        )

    def _ensure_policy(self) -> None:
        name = f"E11Route53-{self.target.zone_id}"
        existing = None
        for page in self.logs.get_paginator("describe_resource_policies").paginate():
            for policy in page[POLICIES]:
                if policy[POLICY_NAME] == name:
                    existing = json.loads(policy[POLICY_DOCUMENT])
        document = existing if existing is not None else {VERSION: "2012-10-17", STATEMENT: []}
        statements = document.get(STATEMENT, [])
        if isinstance(statements, dict):
            statements = [statements]
        managed = {
            SID: "E11DnsQueryLogging", EFFECT: "Allow",
            PRINCIPAL: {SERVICE: "route53.amazonaws.com"},
            ACTION: ["logs:CreateLogStream", "logs:PutLogEvents"],
            RESOURCE: self.target.log_arn + ":*",
            CONDITION: {
                ARN_EQUALS: {SOURCE_ARN: f"arn:aws:route53:::hostedzone/{self.target.zone_id}"},
                STRING_EQUALS: {SOURCE_ACCOUNT: self.target.account_id},
            },
        }
        updated = {**document, STATEMENT: [s for s in statements if s.get(SID) != managed[SID]] + [managed]}
        if updated != existing:
            self.logs.put_resource_policy(policyName=name, policyDocument=json.dumps(updated))

    def enable(self) -> LoggingStatus:
        config = self.configuration()
        self._check_destination(config)
        group = self.group()
        if group and group.get(LOG_GROUP_CLASS, "STANDARD") != "STANDARD":
            raise LoggingError("existing log group is not Standard; its class cannot be changed")
        if group is None:
            self.logs.create_log_group(logGroupName=self.target.log_group, logGroupClass="STANDARD")
            print(f"Created log group {self.target.log_group}", file=sys.stderr)
        if group is None or group.get(RETENTION) != RETENTION_DAYS:
            self.logs.put_retention_policy(logGroupName=self.target.log_group, retentionInDays=RETENTION_DAYS)
        self._ensure_policy()
        if config is None:
            self.route53.create_query_logging_config(
                HostedZoneId=self.target.zone_id, CloudWatchLogsLogGroupArn=self.target.log_arn
            )
        status = self.status()
        if not status.enabled or status.log_class != "STANDARD" or status.retention_days != RETENTION_DAYS:
            raise LoggingError("logging configuration did not verify; rerun status before retrying")
        return status

    def query(self, *, report: bool, since: datetime, until: datetime,
              name: str | None = None, student: str | None = None, limit: int = 100,
              timeout: float = 60) -> QueryOutput:
        self._check_destination(self.configuration())
        text = query_text(self.target, report=report, name=name, student=student, limit=limit)
        query_id = self.logs.start_query(
            logGroupName=self.target.log_group, startTime=int(since.timestamp()),
            endTime=int(until.timestamp()), queryString=text, limit=limit,
        )[QUERY_ID]
        deadline = time.monotonic() + timeout
        while True:
            result = self.logs.get_query_results(queryId=query_id)
            if result[STATUS] == "Complete":
                model = HostnameReport if report else QueryEvent
                rows = [model.model_validate({cell[FIELD]: cell[VALUE] for cell in row})
                        for row in result[RESULTS]]
                return QueryOutput(rows=rows, bytes_scanned=result.get(STATISTICS, {}).get(BYTES_SCANNED, 0))
            if result[STATUS] not in {"Running", "Scheduled"}:
                raise LoggingError(f"CloudWatch query ended with status {result[STATUS]}")
            if time.monotonic() >= deadline:
                self.logs.stop_query(queryId=query_id)
                raise LoggingError("CloudWatch query timed out and was stopped")
            time.sleep(1)

    def verify(self, *, timeout: float = 180) -> str:
        status = self.status()
        if not status.enabled:
            raise LoggingError("DNS query logging is not enabled")
        probe = f"e11-log-check-{uuid4().hex}.{self.target.domain}"
        start = int(datetime.now(timezone.utc).timestamp() * 1000)
        if not self.target.name_servers:
            raise LoggingError("public hosted zone has no authoritative name servers for verification")
        deadline = time.monotonic() + timeout
        attempt = 0
        while True:
            try:
                server = self.target.name_servers[attempt % len(self.target.name_servers)]
                dns.resolver.resolve_at(server, probe, "A", lifetime=10)
            except dns.resolver.NXDOMAIN:
                pass  # Query the authority directly: recursive negative caches cannot hide this probe.
            except dns.exception.DNSException as error:
                print(f"DNS probe through {server} failed: {error}; checking logs before retrying.",
                      file=sys.stderr, flush=True)
            attempt += 1
            for page in self.logs.get_paginator("filter_log_events").paginate(
                logGroupName=self.target.log_group, startTime=start, filterPattern=f'"{probe}"'
            ):
                for event in page[EVENTS]:
                    parts = event[MESSAGE].split()
                    if len(parts) >= 6 and parts[2] == self.target.zone_id and parts[3].rstrip(".") == probe:
                        return f"Verified: observed DNS query for {probe} in {self.target.log_group}"
            if time.monotonic() >= deadline:
                raise LoggingError("configuration is enabled, but the test DNS query was not observed before timeout")
            print("Waiting for the test DNS query to reach CloudWatch...", file=sys.stderr, flush=True)
            time.sleep(5)


def connect(args: argparse.Namespace) -> DnsLogging:
    session = boto3.Session(profile_name=args.profile)
    account = session.client("sts", region_name=REGION).get_caller_identity()[ACCOUNT]
    if args.account_id and args.account_id != account:
        raise LoggingError(f"AWS account mismatch: expected {args.account_id}, got {account}")
    route53 = session.client("route53", region_name=REGION)
    zone_id = args.zone_id.removeprefix("/hostedzone/")
    zone_response = route53.get_hosted_zone(Id=zone_id)
    zone = zone_response[HOSTED_ZONE]
    domain = args.domain.lower().rstrip(".")
    if zone[NAME].lower().rstrip(".") != domain or zone.get(CONFIG, {}).get(PRIVATE_ZONE, True):
        raise LoggingError("hosted zone must be public and match the requested domain")
    config = route53.list_query_logging_configs(HostedZoneId=zone_id)[QUERY_CONFIGS]
    group = args.log_group
    if not group and config:
        prefix = f"arn:aws:logs:{REGION}:{account}:log-group:"
        arn = config[0][LOG_GROUP_ARN]
        if not arn.startswith(prefix):
            raise LoggingError("existing logging destination is outside this account or us-east-1")
        group = arn.removeprefix(prefix)
    target = Target(account_id=account, zone_id=zone_id, domain=domain,
                    log_group=group or f"/aws/route53/{domain}",
                    name_servers=zone_response.get(DELEGATION_SET, {}).get(NAME_SERVERS, []))
    return DnsLogging(target, route53, session.client("logs", region_name=REGION))


def render(rows: list[BaseModel], output_format: str, model: type[BaseModel]) -> str:
    if output_format == "json":
        return json.dumps([row.model_dump(mode="json") for row in rows], indent=2)
    headers = list(model.model_fields)
    values = [row.model_dump(mode="json") for row in rows]
    if output_format == "csv":
        stream = io.StringIO()
        writer = csv.DictWriter(stream, fieldnames=headers)
        writer.writeheader()
        writer.writerows({key: "'" + value if isinstance(value, str) and value.startswith(("=", "+", "-", "@", "\t", "\r", "\n")) else value
                          for key, value in row.items()} for row in values)
        return stream.getvalue().rstrip()
    return tabulate([[row.get(key, "") for key in headers] for row in values], headers=headers)


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["enable", "status", "events", "report", "verify"])
    parser.add_argument("--zone-id", required=True)
    parser.add_argument("--domain", default="csci-e-11.org")
    parser.add_argument("--account-id", help="optional expected AWS account ID")
    parser.add_argument("--profile", help="override normal AWS credential/profile resolution")
    parser.add_argument("--log-group", help="default: existing destination or /aws/route53/DOMAIN")
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--name", help="one hostname, either short or fully qualified")
    selection.add_argument("--student", help="student hostname stem, including its -labN names")
    parser.add_argument("--since", help="lookback such as 1h or 30d; default 1h for events, 30d for report")
    parser.add_argument("--until", help="ISO 8601 end time with time zone; default now")
    parser.add_argument("--limit", type=int, help="maximum rows: default 100 events or 10000 report rows")
    parser.add_argument("--format", choices=["table", "csv", "json"], default="table")
    return parser.parse_args()


def main() -> int:
    args = arguments()
    try:
        if args.action in {"events", "report"}:
            lookback = args.since or ("30d" if args.action == "report" else "1h")
            match = re.fullmatch(r"([1-9][0-9]*)([mhd])", lookback)
            if not match:
                raise LoggingError("--since must be a positive duration such as 30m, 1h, or 30d")
            seconds = int(match[1]) * {"m": 60, "h": 3600, "d": 86400}[match[2]]
            until = datetime.fromisoformat(args.until) if args.until else datetime.now(timezone.utc)
            if until.tzinfo is None:
                raise LoggingError("--until requires an explicit time zone")
            since = until - timedelta(seconds=seconds)
            limit = args.limit if args.limit is not None else (10000 if args.action == "report" else 100)
            if not 1 <= limit <= 10000:
                raise LoggingError("--limit must be between 1 and 10000")
            service = connect(args)
            result = service.query(report=args.action == "report", since=since, until=until,
                                   name=args.name, student=args.student, limit=limit)
            model = HostnameReport if args.action == "report" else QueryEvent
            print(render(list(result.rows), args.format, model))
            print(f"Rows: {len(result.rows)}; scanned {result.bytes_scanned / 1_000_000:.3f} MB", file=sys.stderr)
            if len(result.rows) == limit:
                print("Row limit reached; narrow the time window or selection for complete results.", file=sys.stderr)
        else:
            service = connect(args)
            if args.action == "verify":
                print(service.verify())
            else:
                status = service.enable() if args.action == "enable" else service.status()
                print(render([status], args.format, LoggingStatus), flush=True)
                if args.action == "enable":
                    print(service.verify(), file=sys.stderr)
        return 0
    except (LoggingError, BotoCoreError, ClientError, ValidationError, dns.exception.DNSException,
            OSError, ValueError, KeyError, TypeError) as error:
        print(f"DNS logging failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
