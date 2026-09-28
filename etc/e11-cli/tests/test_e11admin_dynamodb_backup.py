"""Integration tests for e11admin backups using DynamoDB Local."""

import gzip
import hashlib
import io
import json
import os
import subprocess
from pathlib import Path

import boto3
import pytest

from e11.e11admin.dynamodb_backup import (
    BackupError,
    BackupManifest,
    backup_directory,
    load_manifest,
    restore_directory,
    view_directory,
)


USERS_TABLE = "e11-users"
SESSIONS_TABLE = "home-app-sessions"


def _client():
    return boto3.client(
        "dynamodb",
        endpoint_url=os.environ["AWS_ENDPOINT_URL_DYNAMODB"],
        region_name=os.environ["AWS_DEFAULT_REGION"],
    )


def _put_items(client):
    user = {
        "user_id": {"S": "backup-user"},
        "sk": {"S": "#"},
        "email": {"S": "backup@example.edu"},
        "payload": {"B": b"\x00\xffbackup"},
        "binary_set": {"BS": [b"first", b"\x00second"]},
        "score": {"N": "1.25"},
        "nested": {"M": {"blob": {"B": b"nested"}}},
    }
    session = {
        "sid": {"S": "backup-session"},
        "email": {"S": "backup@example.edu"},
        "roles": {"SS": ["student", "staff"]},
    }
    client.put_item(TableName=USERS_TABLE, Item=user)
    client.put_item(TableName=SESSIONS_TABLE, Item=session)
    return user, session


def test_backup_view_and_idempotent_restore_round_trip(
    tmp_path, dynamodb_local, clean_dynamodb
):
    del clean_dynamodb
    del dynamodb_local
    client = _client()
    user, session = _put_items(client)
    backup_path = tmp_path / "backup"

    manifest = backup_directory(client, backup_path, [USERS_TABLE, SESSIONS_TABLE])

    assert {entry.table_name: entry.item_count for entry in manifest.tables} == {
        USERS_TABLE: 1,
        SESSIONS_TABLE: 1,
    }
    assert all(
        (backup_path / entry.filename).read_bytes()[:2] == b"\x1f\x8b"
        for entry in manifest.tables
    )

    output = io.StringIO()
    assert view_directory(backup_path, output) == 2
    viewed = {
        record["table"]: record["item"]
        for record in map(json.loads, output.getvalue().splitlines())
    }
    assert viewed[USERS_TABLE]["payload"] == {"$binary": "AP9iYWNrdXA="}
    assert viewed[USERS_TABLE]["score"] == {"$number": "1.25"}
    assert viewed[SESSIONS_TABLE]["roles"] == ["staff", "student"]

    client.delete_item(
        TableName=USERS_TABLE,
        Key={"user_id": {"S": "backup-user"}, "sk": {"S": "#"}},
    )
    client.delete_item(
        TableName=SESSIONS_TABLE, Key={"sid": {"S": "backup-session"}}
    )
    for _repeat in range(2):
        assert restore_directory(client, backup_path) == [
            (USERS_TABLE, 1),
            (SESSIONS_TABLE, 1),
        ]

    restored_user = client.get_item(
        TableName=USERS_TABLE,
        Key={"user_id": {"S": "backup-user"}, "sk": {"S": "#"}},
        ConsistentRead=True,
    )["Item"]
    restored_binary_set = restored_user.pop("binary_set")["BS"]
    expected_binary_set = user.pop("binary_set")["BS"]
    assert set(restored_binary_set) == set(expected_binary_set)
    assert restored_user == user

    restored_session = client.get_item(
        TableName=SESSIONS_TABLE,
        Key={"sid": {"S": "backup-session"}},
        ConsistentRead=True,
    )["Item"]
    restored_roles = restored_session.pop("roles")["SS"]
    expected_roles = session.pop("roles")["SS"]
    assert set(restored_roles) == set(expected_roles)
    assert restored_session == session


def test_restore_preflight_rejects_missing_key_before_any_write(
    tmp_path, dynamodb_local, clean_dynamodb
):
    del clean_dynamodb
    del dynamodb_local
    client = _client()
    _put_items(client)
    backup_path = tmp_path / "backup"
    backup_directory(client, backup_path, [USERS_TABLE, SESSIONS_TABLE])

    client.update_item(
        TableName=USERS_TABLE,
        Key={"user_id": {"S": "backup-user"}, "sk": {"S": "#"}},
        UpdateExpression="SET marker = :marker",
        ExpressionAttributeValues={":marker": {"S": "must-survive"}},
    )

    manifest = load_manifest(backup_path)
    session_archive = next(
        table for table in manifest.tables if table.table_name == SESSIONS_TABLE
    )
    archive_path = backup_path / session_archive.filename
    with gzip.open(archive_path, "rt", encoding="utf-8") as stream:
        record = json.loads(stream.readline())
    del record["sid"]
    with gzip.open(archive_path, "wt", encoding="utf-8") as stream:
        stream.write(json.dumps(record) + "\n")
    session_archive.sha256 = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    (backup_path / "manifest.json").write_text(
        json.dumps(manifest.model_dump(mode="json"), indent=2) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(BackupError, match="missing key attribute 'sid'"):
        restore_directory(client, backup_path)

    preserved = client.get_item(
        TableName=USERS_TABLE,
        Key={"user_id": {"S": "backup-user"}, "sk": {"S": "#"}},
        ConsistentRead=True,
    )["Item"]
    assert preserved["marker"] == {"S": "must-survive"}


def test_restore_rejects_checksum_and_schema_mismatches(
    tmp_path, dynamodb_local, clean_dynamodb
):
    del clean_dynamodb
    del dynamodb_local
    client = _client()
    _put_items(client)
    backup_path = tmp_path / "backup"
    manifest = backup_directory(client, backup_path, [USERS_TABLE])
    archive_path = backup_path / manifest.tables[0].filename

    with archive_path.open("ab") as stream:
        stream.write(b"corrupt")
    with pytest.raises(BackupError, match="checksum mismatch"):
        restore_directory(client, backup_path)

    manifest.tables[0].sha256 = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    manifest.tables[0].key_schema[0].attribute_name = "wrong_key"
    (backup_path / "manifest.json").write_text(
        BackupManifest.model_validate(manifest).model_dump_json(indent=2) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(BackupError, match="key schema mismatch"):
        restore_directory(client, backup_path)


def test_backup_view_restore_commands_against_dynamodb_local(
    tmp_path, dynamodb_local, clean_dynamodb
):
    del dynamodb_local, clean_dynamodb
    client = _client()
    _put_items(client)
    backup_path = tmp_path / "command-backup"
    project = Path(__file__).resolve().parents[1]
    make = ["make", "--silent", "--no-print-directory"]

    backup = subprocess.run(
        [*make, "ddb-backup", f"DDB_DIR={backup_path}", f"DDB_TABLE={USERS_TABLE}"],
        cwd=project, check=True, capture_output=True, text=True,
    )
    assert "e11-users: 1 records" in backup.stdout
    viewed = subprocess.run(
        [*make, "ddb-view", f"DDB_DIR={backup_path}"],
        cwd=project, check=True, capture_output=True, text=True,
    )
    assert json.loads(viewed.stdout)["item"]["email"] == "backup@example.edu"

    client.delete_item(
        TableName=USERS_TABLE,
        Key={"user_id": {"S": "backup-user"}, "sk": {"S": "#"}},
    )
    restored = subprocess.run(
        [*make, "ddb-restore", f"DDB_DIR={backup_path}", "DDB_ALLOW_RESTORE=YES"],
        cwd=project, check=True, capture_output=True, text=True,
    )
    assert "e11-users: restored 1 records" in restored.stdout
    assert "Item" in client.get_item(
        TableName=USERS_TABLE,
        Key={"user_id": {"S": "backup-user"}, "sk": {"S": "#"}},
        ConsistentRead=True,
    )
