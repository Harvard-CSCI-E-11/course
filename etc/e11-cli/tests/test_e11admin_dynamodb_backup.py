# Exercise lossless archive operations against real DynamoDB Local tables.
# Round trips retain binary, numeric, set, and nested attribute representations.
# Default restores omit sessions, while explicitly selected tables can be restored.
# Preflight failures must leave all previously selected destination data untouched.
# Console tests cover offline views and opt-in enforcement before AWS access.
# Temporary tables and archive directories belong only to the current test.
"""Integration tests for e11admin backups using DynamoDB Local."""

import gzip
import hashlib
import io
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import boto3
import pytest

from e11.e11admin.dynamodb_backup import (
    BackupError,
    BackupManifest,
    KeyElement,
    TableArchive,
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
        assert restore_directory(client, backup_path, [USERS_TABLE, SESSIONS_TABLE]) == [
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
        restore_directory(client, backup_path, [USERS_TABLE, SESSIONS_TABLE])

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


def test_default_restore_does_not_revive_archived_sessions(tmp_path, dynamodb_local, clean_dynamodb):
    del dynamodb_local, clean_dynamodb
    client = _client()
    _put_items(client)
    backup = tmp_path / "session-backup"
    backup_directory(client, backup, [USERS_TABLE, SESSIONS_TABLE])
    client.delete_item(TableName=SESSIONS_TABLE, Key={"sid": {"S": "backup-session"}})
    assert restore_directory(client, backup) == [(USERS_TABLE, 1)]
    assert "Item" not in client.get_item(TableName=SESSIONS_TABLE,
                                         Key={"sid": {"S": "backup-session"}}, ConsistentRead=True)


@pytest.mark.parametrize("incompatible_key", ["sid", "secondary"])
def test_restore_checks_primary_and_index_key_types_before_writes(
    tmp_path, dynamodb_local, clean_dynamodb, incompatible_key,
):
    del dynamodb_local, clean_dynamodb
    from e11.e11admin import dynamodb_backup as archive
    client = _client()
    _put_items(client)
    table_name = "z-key-type-preflight"
    secondary = "secondary"
    sid = "sid"
    string_type = "S"
    number_type = "N"

    def create_table(numeric_key=None):
        client.create_table(
            TableName=table_name,
            KeySchema=[{archive.ATTRIBUTE_NAME: sid, archive.KEY_TYPE: "HASH"}],
            AttributeDefinitions=[{archive.ATTRIBUTE_NAME: name,
                                   archive.ATTRIBUTE_TYPE: number_type if name == numeric_key else string_type}
                                  for name in [sid, secondary]],
            GlobalSecondaryIndexes=[{"IndexName": "BySecondary", archive.KEY_SCHEMA: [
                {archive.ATTRIBUTE_NAME: secondary, archive.KEY_TYPE: "HASH"}],
                "Projection": {"ProjectionType": "ALL"}}],
            BillingMode="PAY_PER_REQUEST",
        )
        client.get_waiter("table_exists").wait(TableName=table_name)

    create_table()
    try:
        client.put_item(TableName=table_name, Item={sid: {string_type: "old-id"},
                                                   secondary: {string_type: "old-index"}})
        backup = tmp_path / "key-types"
        backup_directory(client, backup, [USERS_TABLE, table_name])
        client.update_item(TableName=USERS_TABLE, Key={"user_id": {"S": "backup-user"}, "sk": {"S": "#"}},
                           UpdateExpression="SET marker = :m", ExpressionAttributeValues={":m": {"S": "preserved"}})
        client.delete_table(TableName=table_name)
        client.get_waiter("table_not_exists").wait(TableName=table_name)
        create_table(incompatible_key)
        with pytest.raises(BackupError, match="key type/value mismatch"):
            restore_directory(client, backup)
        assert client.get_item(TableName=USERS_TABLE,
                               Key={"user_id": {"S": "backup-user"}, "sk": {"S": "#"}},
                               ConsistentRead=True)["Item"]["marker"] == {"S": "preserved"}
    finally:
        client.delete_table(TableName=table_name)


def _offline_environment():
    environment = os.environ.copy()
    for key in ["AWS_PROFILE", "AWS_DEFAULT_PROFILE", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY",
                "AWS_SESSION_TOKEN", "AWS_REGION", "AWS_DEFAULT_REGION"]:
        environment.pop(key, None)
    environment.update(AWS_CONFIG_FILE=os.devnull, AWS_SHARED_CREDENTIALS_FILE=os.devnull,
                       AWS_EC2_METADATA_DISABLED="true")
    return environment


def test_console_view_is_offline_and_restore_requires_opt_in(tmp_path):
    directory = tmp_path / "offline-backup"
    directory.mkdir()
    data = directory / "table-0000.ddb"
    with gzip.open(data, "wt", encoding="utf-8") as stream:
        stream.write(json.dumps({"user_id": {"S": "offline-user"}}) + "\n")
    manifest = BackupManifest(created_at=datetime.now(timezone.utc), region=None, tables=[
        TableArchive(table_name="offline-users", filename=data.name, item_count=1,
                     sha256=hashlib.sha256(data.read_bytes()).hexdigest(),
                     key_schema=[KeyElement(attribute_name="user_id", key_type="HASH")]),
    ])
    (directory / "manifest.json").write_text(manifest.model_dump_json())
    project = Path(__file__).resolve().parents[1]
    viewed = subprocess.run(["make", "--silent", "--no-print-directory", "ddb-view", f"DDB_DIR={directory}"],
                            cwd=project, env=_offline_environment(), capture_output=True, text=True, check=True)
    assert json.loads(viewed.stdout)["item"]["user_id"] == "offline-user"
    rejected = subprocess.run([str(project / ".venv/bin/e11admin"), "restore", str(directory)],
                              env=_offline_environment(), capture_output=True, text=True, check=False)
    assert rejected.returncode == 2
    assert "--allow-restore" in rejected.stderr
    assert "NoRegionError" not in rejected.stderr


@pytest.mark.parametrize("value_type,key_role,length", [("S", "HASH", 2049), ("S", "RANGE", 1025), ("B", "HASH", 2049)])
def test_restore_checks_new_index_key_byte_limits_before_writes(
    tmp_path, dynamodb_local, clean_dynamodb, value_type, key_role, length,
):
    del dynamodb_local, clean_dynamodb
    from e11.e11admin import dynamodb_backup as archive
    client = _client()
    _put_items(client)
    table_name = "z-key-length-preflight"

    def create_table(with_index):
        arguments = {
            "TableName": table_name,
            archive.KEY_SCHEMA: [{archive.ATTRIBUTE_NAME: "sid", archive.KEY_TYPE: "HASH"}],
            archive.ATTRIBUTE_DEFINITIONS: [{archive.ATTRIBUTE_NAME: "sid", archive.ATTRIBUTE_TYPE: "S"}],
            "BillingMode": "PAY_PER_REQUEST",
        }
        if with_index:
            arguments[archive.ATTRIBUTE_DEFINITIONS].append(
                {archive.ATTRIBUTE_NAME: "secondary", archive.ATTRIBUTE_TYPE: value_type})
            schema = [{archive.ATTRIBUTE_NAME: "secondary", archive.KEY_TYPE: key_role}]
            if key_role == "RANGE":
                schema.insert(0, {archive.ATTRIBUTE_NAME: "sid", archive.KEY_TYPE: "HASH"})
            arguments[archive.GLOBAL_SECONDARY_INDEXES] = [
                {"IndexName": "BySecondary", archive.KEY_SCHEMA: schema,
                 "Projection": {"ProjectionType": "ALL"}}]
        client.create_table(**arguments)
        client.get_waiter("table_exists").wait(TableName=table_name)

    create_table(False)
    try:
        # Non-ASCII text ensures the check measures UTF-8 bytes, not characters.
        payload = "é" * (length // 2) + "x" if value_type == "S" else b"x" * length
        client.put_item(TableName=table_name, Item={"sid": {"S": "old-id"}, "secondary": {value_type: payload}})
        backup = tmp_path / "key-lengths"
        backup_directory(client, backup, [USERS_TABLE, table_name])
        client.update_item(TableName=USERS_TABLE, Key={"user_id": {"S": "backup-user"}, "sk": {"S": "#"}},
                           UpdateExpression="SET marker = :m", ExpressionAttributeValues={":m": {"S": "preserved"}})
        client.delete_table(TableName=table_name)
        client.get_waiter("table_not_exists").wait(TableName=table_name)
        create_table(True)
        with pytest.raises(BackupError, match="key exceeds"):
            restore_directory(client, backup)
        assert client.get_item(TableName=USERS_TABLE, Key={"user_id": {"S": "backup-user"}, "sk": {"S": "#"}},
                               ConsistentRead=True)["Item"]["marker"] == {"S": "preserved"}
    finally:
        client.delete_table(TableName=table_name)


def test_write_batches_fit_actual_boto3_request_serialization():
    from botocore.session import Session
    from botocore.serialize import create_serializer
    from e11.e11admin import dynamodb_backup as archive
    model = Session().get_service_model("dynamodb").operation_model("BatchWriteItem")
    serializer = create_serializer("json")
    for payload in [{"S": "é" * 150000}, {"B": b"x" * 300000}]:
        items = [{"id": {"S": str(index)}, "payload": payload} for index in range(26)]
        batches = list(archive._write_batches("byte-limit", iter(items)))
        assert [item for batch in batches for item in batch] == items
        assert len(batches) >= 2
        for batch in batches:
            request = {archive.REQUEST_ITEMS: {"byte-limit": [{archive.PUT_REQUEST: {archive.ITEM: item}} for item in batch]}}
            wire = serializer.serialize_to_request(request, model)["body"]
            assert len(wire) <= archive.MAX_BATCH_BYTES
            assert len(batch) <= archive.MAX_BATCH_ITEMS


def _create_local_index_table(client, table_name, projection=None):
    from e11.e11admin import dynamodb_backup as archive
    definitions = [{archive.ATTRIBUTE_NAME: name, archive.ATTRIBUTE_TYPE: "S"} for name in ["pk", "sk"]]
    arguments = {
        "TableName": table_name,
        archive.KEY_SCHEMA: [{archive.ATTRIBUTE_NAME: "pk", archive.KEY_TYPE: "HASH"},
                             {archive.ATTRIBUTE_NAME: "sk", archive.KEY_TYPE: "RANGE"}],
        archive.ATTRIBUTE_DEFINITIONS: definitions,
        "BillingMode": "PAY_PER_REQUEST",
    }
    if projection:
        definitions.append({archive.ATTRIBUTE_NAME: "secondary", archive.ATTRIBUTE_TYPE: "S"})
        projection_arguments = {archive.PROJECTION_TYPE: projection}
        if projection == "INCLUDE":
            projection_arguments[archive.NON_KEY_ATTRIBUTES] = ["note"]
        arguments[archive.LOCAL_SECONDARY_INDEXES] = [{
            archive.INDEX_NAME: "BySecondary",
            archive.KEY_SCHEMA: [{archive.ATTRIBUTE_NAME: "pk", archive.KEY_TYPE: "HASH"},
                                 {archive.ATTRIBUTE_NAME: "secondary", archive.KEY_TYPE: "RANGE"}],
            archive.PROJECTION: projection_arguments,
        }]
    client.create_table(**arguments)
    client.get_waiter("table_exists").wait(TableName=table_name)


@pytest.mark.parametrize("legacy_manifest", [False, True])
def test_restore_rejects_new_lsi_projection_before_earlier_table_writes(
    tmp_path, dynamodb_local, clean_dynamodb, legacy_manifest,
):
    del dynamodb_local, clean_dynamodb
    client = _client()
    _put_items(client)
    table_name = "z-local-index-preflight"
    _create_local_index_table(client, table_name)
    try:
        client.put_item(TableName=table_name, Item={"pk": {"S": "p"}, "sk": {"S": "s"},
            "secondary": {"S": "index-key"}, "payload": {"S": "x" * 250000}})
        backup = tmp_path / "local-index-backup"
        backup_directory(client, backup, [USERS_TABLE, table_name])
        if legacy_manifest:
            path = backup / "manifest.json"
            manifest = json.loads(path.read_text())
            manifest["format_version"] = 1
            for table in manifest["tables"]:
                table.pop("local_secondary_indexes")
            path.write_text(json.dumps(manifest))
        client.update_item(TableName=USERS_TABLE, Key={"user_id": {"S": "backup-user"}, "sk": {"S": "#"}},
                           UpdateExpression="SET marker = :m", ExpressionAttributeValues={":m": {"S": "preserved"}})
        client.delete_table(TableName=table_name)
        client.get_waiter("table_not_exists").wait(TableName=table_name)
        _create_local_index_table(client, table_name, "ALL")
        with pytest.raises(BackupError, match="local secondary index layout mismatch"):
            restore_directory(client, backup)
        assert client.get_item(TableName=USERS_TABLE, Key={"user_id": {"S": "backup-user"}, "sk": {"S": "#"}},
                               ConsistentRead=True)["Item"]["marker"] == {"S": "preserved"}
    finally:
        client.delete_table(TableName=table_name)


@pytest.mark.parametrize("projection", ["KEYS_ONLY", "INCLUDE", "ALL"])
def test_matching_local_index_layout_restores_losslessly(tmp_path, dynamodb_local, projection):
    del dynamodb_local
    client = _client()
    table_name = "z-matching-local-index"
    _create_local_index_table(client, table_name, projection)
    try:
        item = {"pk": {"S": "p"}, "sk": {"S": "s"}, "secondary": {"S": "index-key"},
                "payload": {"S": "x" * 100000}, "note": {"S": "projected-note"}}
        client.put_item(TableName=table_name, Item=item)
        backup = tmp_path / "matching-index"
        manifest = backup_directory(client, backup, [table_name])
        assert manifest.format_version == 2
        assert manifest.tables[0].local_secondary_indexes[0].projection_type == projection
        client.delete_item(TableName=table_name, Key={"pk": item["pk"], "sk": item["sk"]})
        assert restore_directory(client, backup) == [(table_name, 1)]
        assert client.get_item(TableName=table_name, Key={"pk": item["pk"], "sk": item["sk"]},
                               ConsistentRead=True)["Item"] == item
    finally:
        client.delete_table(TableName=table_name)


def test_version_one_archive_still_restores_without_local_indexes(tmp_path, dynamodb_local, clean_dynamodb):
    del dynamodb_local, clean_dynamodb
    client = _client()
    user, _session = _put_items(client)
    backup = tmp_path / "version-one"
    backup_directory(client, backup, [USERS_TABLE])
    path = backup / "manifest.json"
    manifest = json.loads(path.read_text())
    manifest["format_version"] = 1
    for table in manifest["tables"]:
        table.pop("local_secondary_indexes")
    path.write_text(json.dumps(manifest))
    client.delete_item(TableName=USERS_TABLE, Key={"user_id": user["user_id"], "sk": user["sk"]})
    assert restore_directory(client, backup) == [(USERS_TABLE, 1)]
    assert client.get_item(TableName=USERS_TABLE, Key={"user_id": user["user_id"], "sk": user["sk"]},
                           ConsistentRead=True)["Item"]["payload"] == user["payload"]
