# Empty course records while preserving DynamoDB tables and their indexes.
# This operator utility belongs to the end-of-course rollover procedure.
# Its command-line entry point pins the production account and AWS endpoints.
# Inventory is read-only; deletion requires both --apply and DDB_EMPTY=1.
# All tables are preflighted before deletion; scans paginate over primary keys.
# Each completed batch reports progress; SDK retries precede zero-count checks.
# Application writers must be stopped; a failed reset can be resumed safely.
"""Inventory or empty the four production course tables."""

import argparse
import os
from collections.abc import Iterator, Sequence
from itertools import batched
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from pydantic import BaseModel

ACCOUNT = "586794483136"
REGION = "us-east-1"
TABLES = ("e11-users", "home-app-prod-sessions", "home-app-stage-sessions", "Leaderboard")
ATTRIBUTE_NAME = "AttributeName"
ITEMS = "Items"
COUNT = "Count"
LAST_KEY = "LastEvaluatedKey"
START_KEY = "ExclusiveStartKey"
LIMIT = "Limit"


class TablePlan(BaseModel):
    """Preflighted table identity, primary key, and observed record count."""

    name: str
    keys: list[str]
    count: int


def pages(table: Any, keys: list[str], page_size: int) -> Iterator[dict[str, Any]]:
    """Read all primary keys, without loading student record contents."""
    aliases = {f"#k{i}": key for i, key in enumerate(keys)}
    options: dict[str, Any] = {LIMIT: page_size}
    while True:
        page = table.scan(
            ConsistentRead=True,
            ProjectionExpression=", ".join(aliases),
            ExpressionAttributeNames=aliases,
            **options,
        )
        yield page
        if not page.get(LAST_KEY):
            return
        options[START_KEY] = page[LAST_KEY]


def inventory(database: Any, names: Sequence[str], page_size: int = 1000) -> list[TablePlan]:
    """Validate every table and count every page before any destructive work."""
    plans = []
    for name in names:
        table = database.Table(name)
        keys = [key[ATTRIBUTE_NAME] for key in table.key_schema]
        total = sum(page[COUNT] for page in pages(table, keys, page_size))
        plans.append(TablePlan(name=name, keys=keys, count=total))
    return plans


def empty_tables(database: Any, plans: Sequence[TablePlan], page_size: int = 1000) -> None:
    """Delete all primary keys and verify every table, retaining table schemas."""
    for plan in plans:
        table = database.Table(plan.name)
        deleted = 0
        items = (item for page in pages(table, plan.keys, page_size) for item in page[ITEMS])
        for number, group in enumerate(batched(items, 25), start=1):
            with table.batch_writer() as batch:
                for item in group:
                    batch.delete_item(Key={key: item[key] for key in plan.keys})
            deleted += len(group)
            print(
                f"{plan.name}: batch {number} complete, {len(group)} records deleted "
                f"({deleted} total)", flush=True,
            )
        print(f"{plan.name}: deletion pass complete", flush=True)
    remaining = inventory(database, [plan.name for plan in plans], page_size)
    for plan in remaining:
        print(f"{plan.name}: {plan.count} records remaining", flush=True)
    if any(plan.count for plan in remaining):
        raise RuntimeError("Reset incomplete; keep writers stopped and rerun after investigation")


def main() -> None:
    """Run a read-only inventory or explicitly authorized course reset."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Delete all records; stop course writers first")
    args = parser.parse_args()
    if args.apply and os.environ.get("DDB_EMPTY") != "1":
        parser.error("deletion requires DDB_EMPTY=1")
    session = boto3.Session(profile_name="fas", region_name=REGION)
    try:
        sts = session.client("sts", endpoint_url=f"https://sts.{REGION}.amazonaws.com")
        if sts.get_caller_identity()["Account"] != ACCOUNT:
            raise RuntimeError("Wrong AWS account; refusing to continue")
        database = session.resource("dynamodb", endpoint_url=f"https://dynamodb.{REGION}.amazonaws.com")
        plans = inventory(database, TABLES)
        print(f"Account {ACCOUNT}, region {REGION}", flush=True)
        for plan in plans:
            print(f"{plan.name}: {plan.count} records", flush=True)
        if args.apply:
            empty_tables(database, plans)
        else:
            print("Inventory only. Use --apply to delete all records from these four tables.")
    except (BotoCoreError, ClientError) as error:
        raise SystemExit(f"AWS operation failed ({type(error).__name__}); reset may be partial") from None
    except RuntimeError as error:
        raise SystemExit(str(error)) from None


if __name__ == "__main__":
    main()
