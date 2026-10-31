# Exercise rollover deletion against real DynamoDB Local tables.
# Each test creates isolated tables with representative course key schemas.
# Small scan pages force pagination independently of item byte sizes.
# More than 25 records exercise complete-batch progress across request boundaries.
# Inventory must retain data; deletion must retain schema and indexes.
# A missing table must fail preflight before any records are removed.
# CLI subprocesses verify that missing authorization fails before AWS access.
"""Integration tests for the course-table reset utility."""

import os
from pathlib import Path
import subprocess
import sys
import uuid

import boto3
import pytest
from botocore.exceptions import ClientError

from empty_course_tables import empty_tables, inventory


@pytest.fixture
def course_tables():
    """Create simple/composite tables and remove them even after test failures."""
    endpoint = os.environ["AWS_ENDPOINT_URL_DYNAMODB"]
    assert endpoint.startswith(("http://localhost:", "http://127.0.0.1:"))
    database = boto3.resource("dynamodb", endpoint_url=endpoint, region_name="us-east-1")
    names = []
    schemas = []
    try:
        for keys in (("sid",), ("user_id", "sk")):
            name = "reset-test-" + uuid.uuid4().hex
            table = database.create_table(
                TableName=name,
                KeySchema=[{"AttributeName": key, "KeyType": "HASH" if i == 0 else "RANGE"}
                           for i, key in enumerate(keys)],
                AttributeDefinitions=[{"AttributeName": key, "AttributeType": "S"} for key in keys],
                BillingMode="PAY_PER_REQUEST",
            )
            names.append(name)
            table.wait_until_exists()
            schemas.append(table.key_schema)
            with table.batch_writer() as batch:
                for i in range(57):
                    batch.put_item(Item={**{key: str(i) for key in keys}, "payload": "private data"})
        yield database, names, schemas
    finally:
        for name in names:
            database.Table(name).delete()


def test_inventory_and_reset_paginate_and_preserve_tables(course_tables, capsys):
    database, names, schemas = course_tables
    plans = inventory(database, names, page_size=7)
    assert [plan.count for plan in plans] == [57, 57]
    # Inventory itself must never remove records.
    assert [plan.count for plan in inventory(database, names)] == [57, 57]
    empty_tables(database, plans, page_size=7)
    progress = capsys.readouterr().out.splitlines()
    for name in names:
        assert [line for line in progress if line.startswith(f"{name}: batch ")] == [
            f"{name}: batch 1 complete, 25 records deleted (25 total)",
            f"{name}: batch 2 complete, 25 records deleted (50 total)",
            f"{name}: batch 3 complete, 7 records deleted (57 total)",
        ]
    assert [plan.count for plan in inventory(database, names)] == [0, 0]
    assert [database.Table(name).key_schema for name in names] == schemas
    # Restarting after a completed or partial reset must be harmless.
    empty_tables(database, inventory(database, names), page_size=7)


def test_missing_table_aborts_preflight_without_deleting(course_tables):
    database, names, _ = course_tables
    with pytest.raises(ClientError):
        inventory(database, [*names, "missing-" + uuid.uuid4().hex], page_size=7)
    assert [plan.count for plan in inventory(database, names)] == [57, 57]


@pytest.mark.parametrize("value", [None, "0", "yes", ""])
def test_apply_requires_environment_opt_in_before_aws(value):
    env = os.environ.copy()
    env.pop("DDB_EMPTY", None)
    if value is not None:
        env["DDB_EMPTY"] = value
    # Argument validation must reject deletion before resolving the pinned profile.
    result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parents[1] / "empty_course_tables.py"), "--apply"],
        env=env,
        capture_output=True, text=True, check=False, timeout=10,
    )
    assert result.returncode == 2
    assert "deletion requires DDB_EMPTY=1" in result.stderr
