"""Maintain 180-day retention for E11 Lambda logs without replacing log groups.

CloudFormation identifies the current functions in the selected course stacks.
CloudWatch prefix discovery also finds their historical log groups.
The default scope includes the legacy home-app namespace as well.
Planning is read-only; --apply creates missing groups and sets retention.
Account verification precedes all writes, and settings are read back afterward.
AWS expires old events asynchronously; this tool never purges recent history.
"""

import argparse
from datetime import datetime, timedelta, timezone
from typing import Any

import boto3
from botocore.exceptions import ClientError
from pydantic import BaseModel

STACKS = ("home-app-prod", "home-app-stage", "leaderboard")
ACCOUNT = "586794483136"
REGION = "us-east-1"
RETENTION_DAYS = 180
RESOURCES = "StackResourceSummaries"
RESOURCE_TYPE = "ResourceType"
PHYSICAL_ID = "PhysicalResourceId"
GROUPS = "logGroups"
GROUP_NAME = "logGroupName"
RETENTION = "retentionInDays"
ERROR = "Error"
CODE = "Code"


class LogGroupPlan(BaseModel):
    """One existing or newly required log group and its observed retention."""

    name: str
    exists: bool
    before_days: int | None = None
    after_days: int | None = None


class RetentionReport(BaseModel):
    """Selected changes and the event-expiration cutoff, without log contents."""

    account: str
    region: str
    applied: bool
    expires_before: datetime
    groups: list[LogGroupPlan]


def discover_groups(cloudformation: Any, logs: Any, stacks: list[str]) -> list[LogGroupPlan]:
    """Include old groups while ensuring new functions get retention before use."""
    desired = set()
    observed = {}
    for stack in stacks:
        for page in cloudformation.get_paginator("list_stack_resources").paginate(StackName=stack):
            for resource in page[RESOURCES]:
                if resource[RESOURCE_TYPE] == "AWS::Lambda::Function" and resource.get(PHYSICAL_ID):
                    desired.add("/aws/lambda/" + resource[PHYSICAL_ID])
    prefixes = [f"/aws/lambda/{stack}-" for stack in stacks]
    if set(stacks) == set(STACKS):
        prefixes.append("/aws/lambda/home-app-")
    for prefix in prefixes:
        for page in logs.get_paginator("describe_log_groups").paginate(logGroupNamePrefix=prefix):
            for group in page[GROUPS]:
                observed[group[GROUP_NAME]] = group.get(RETENTION)
    return [LogGroupPlan(name=name, exists=name in observed, before_days=observed.get(name))
            for name in sorted(desired | observed.keys())]


def apply_retention(logs: Any, groups: list[LogGroupPlan]):
    """Set and verify retention without deleting any group or recent event."""
    for group in groups:
        if not group.exists:
            try:
                logs.create_log_group(logGroupName=group.name)
            except ClientError as exc:
                if exc.response.get(ERROR, {}).get(CODE) != "ResourceAlreadyExistsException":
                    raise
        logs.put_retention_policy(logGroupName=group.name, retentionInDays=RETENTION_DAYS)
        response = logs.describe_log_groups(logGroupNamePrefix=group.name)
        exact = next((g for g in response[GROUPS] if g[GROUP_NAME] == group.name), None)
        if exact is None or exact.get(RETENTION) != RETENTION_DAYS:
            raise RuntimeError(f"Retention readback failed for {group.name}")
        group.after_days = RETENTION_DAYS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default="fas")
    parser.add_argument("--region", default=REGION)
    parser.add_argument("--account-id", default=ACCOUNT)
    parser.add_argument("--stack", action="append", choices=STACKS)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    account = session.client("sts").get_caller_identity()["Account"]
    if account != args.account_id:
        raise RuntimeError("AWS account does not match the requested course account")
    logs = session.client("logs")
    groups = discover_groups(session.client("cloudformation"), logs, args.stack or list(STACKS))
    if args.apply:
        apply_retention(logs, groups)
    result = RetentionReport(account=account, region=args.region, applied=args.apply,
                             expires_before=datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS), groups=groups)
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
