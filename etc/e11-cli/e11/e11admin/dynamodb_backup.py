"""Portable, lossless DynamoDB backups for course administration."""

from __future__ import annotations

import base64
import gzip
import hashlib
import json
import time
from collections.abc import Iterator, Sequence
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal, TextIO, cast

from boto3.dynamodb.types import Binary, TypeDeserializer
from pydantic import BaseModel, ConfigDict, Field, ValidationError


FORMAT_NAME = "e11-dynamodb-backup"
FORMAT_VERSION = 1
MANIFEST_FILENAME = "manifest.json"
MAX_BATCH_ITEMS = 25
MAX_BATCH_RETRIES = 8

# DynamoDB wire-format keys. These dictionaries cross the boto3 API boundary.
TABLE_NAMES = "TableNames"
TABLE = "Table"
KEY_SCHEMA = "KeySchema"
ATTRIBUTE_NAME = "AttributeName"
KEY_TYPE = "KeyType"
ITEMS = "Items"
ITEM = "Item"
LAST_EVALUATED_KEY = "LastEvaluatedKey"
EXCLUSIVE_START_KEY = "ExclusiveStartKey"
UNPROCESSED_ITEMS = "UnprocessedItems"
PUT_REQUEST = "PutRequest"

ATTRIBUTE_VALUE_TYPES = frozenset(
    {"B", "BS", "BOOL", "L", "M", "N", "NS", "NULL", "S", "SS"}
)

WireValue = dict[str, Any]
WireItem = dict[str, WireValue]


class BackupError(RuntimeError):
    """The archive is incomplete, invalid, or incompatible with its target."""


class KeyElement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    attribute_name: str = Field(min_length=1)
    key_type: Literal["HASH", "RANGE"]


class TableArchive(BaseModel):
    model_config = ConfigDict(extra="forbid")

    table_name: str = Field(min_length=1)
    filename: str = Field(pattern=r"^table-[0-9]{4}\.ddb$")
    item_count: int = Field(ge=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    key_schema: list[KeyElement] = Field(min_length=1, max_length=2)


class BackupManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    format_name: Literal["e11-dynamodb-backup"] = FORMAT_NAME
    format_version: Literal[1] = FORMAT_VERSION
    created_at: datetime
    region: str | None
    tables: list[TableArchive] = Field(min_length=1)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _encode_av(value: WireValue) -> WireValue:
    """Make one DynamoDB AttributeValue JSON-safe without changing its type."""
    if len(value) != 1:
        raise BackupError("DynamoDB AttributeValue must contain exactly one type")
    value_type, payload = next(iter(value.items()))
    if value_type not in ATTRIBUTE_VALUE_TYPES:
        raise BackupError(f"unknown DynamoDB AttributeValue type: {value_type}")
    if value_type == "B":
        if not isinstance(payload, (bytes, bytearray, memoryview)):
            raise BackupError("DynamoDB B value is not binary")
        payload = base64.b64encode(bytes(payload)).decode("ascii")
    elif value_type == "BS":
        if not isinstance(payload, Sequence) or isinstance(payload, (str, bytes)):
            raise BackupError("DynamoDB BS value is not a sequence")
        payload = [base64.b64encode(bytes(entry)).decode("ascii") for entry in payload]
    elif value_type == "M":
        if not isinstance(payload, dict):
            raise BackupError("DynamoDB M value is not a map")
        payload = {name: _encode_av(child) for name, child in payload.items()}
    elif value_type == "L":
        if not isinstance(payload, list):
            raise BackupError("DynamoDB L value is not a list")
        payload = [_encode_av(child) for child in payload]
    return {value_type: payload}


def _decode_av(value: Any) -> WireValue:
    if not isinstance(value, dict) or len(value) != 1:
        raise BackupError("DynamoDB AttributeValue must contain exactly one type")
    value_type, payload = next(iter(value.items()))
    if value_type not in ATTRIBUTE_VALUE_TYPES:
        raise BackupError(f"unknown DynamoDB AttributeValue type: {value_type}")
    try:
        if value_type == "B":
            if not isinstance(payload, str):
                raise BackupError("encoded DynamoDB B value is not a string")
            payload = base64.b64decode(payload, validate=True)
        elif value_type == "BS":
            if not isinstance(payload, list) or not all(isinstance(entry, str) for entry in payload):
                raise BackupError("encoded DynamoDB BS value is not a string list")
            payload = [base64.b64decode(entry, validate=True) for entry in payload]
        elif value_type == "M":
            if not isinstance(payload, dict):
                raise BackupError("encoded DynamoDB M value is not a map")
            payload = {name: _decode_av(child) for name, child in payload.items()}
        elif value_type == "L":
            if not isinstance(payload, list):
                raise BackupError("encoded DynamoDB L value is not a list")
            payload = [_decode_av(child) for child in payload]
    except (ValueError, TypeError) as error:
        raise BackupError(f"invalid {value_type} value: {error}") from error
    decoded = {value_type: payload}
    try:
        TypeDeserializer().deserialize(cast(Any, decoded))
    except (TypeError, ValueError) as error:
        raise BackupError(f"invalid DynamoDB {value_type} value: {error}") from error
    return decoded


def _encode_item(item: WireItem) -> str:
    encoded = {name: _encode_av(value) for name, value in item.items()}
    return json.dumps(encoded, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _decode_item(payload: Any) -> WireItem:
    if not isinstance(payload, dict) or not payload:
        raise BackupError("record is not a non-empty DynamoDB item")
    if not all(isinstance(name, str) for name in payload):
        raise BackupError("record contains a non-string attribute name")
    return {name: _decode_av(value) for name, value in payload.items()}


def _iter_archive_items(path: Path) -> Iterator[tuple[int, WireItem]]:
    try:
        with gzip.open(path, "rt", encoding="utf-8", newline="") as stream:
            for line_number, line in enumerate(stream, start=1):
                if not line.strip():
                    raise BackupError(f"{path.name}:{line_number}: blank record")
                try:
                    payload = json.loads(line)
                    yield line_number, _decode_item(payload)
                except json.JSONDecodeError as error:
                    raise BackupError(f"{path.name}:{line_number}: invalid JSON: {error}") from error
                except BackupError as error:
                    raise BackupError(f"{path.name}:{line_number}: {error}") from error
    except (OSError, EOFError) as error:
        raise BackupError(f"cannot read {path.name}: {error}") from error


def _list_tables(client: Any) -> list[str]:
    names: list[str] = []
    for page in client.get_paginator("list_tables").paginate():
        names.extend(page[TABLE_NAMES])
    return sorted(names)


def _select_table_names(client: Any, requested: Sequence[str] | None) -> list[str]:
    available = _list_tables(client)
    if not requested:
        if not available:
            raise BackupError("the account has no DynamoDB tables")
        return available
    selected = list(dict.fromkeys(requested))
    missing = sorted(set(selected) - set(available))
    if missing:
        raise BackupError(f"DynamoDB table not found: {', '.join(missing)}")
    return sorted(selected)


def _key_schema(description: dict[str, Any]) -> list[KeyElement]:
    try:
        return [
            KeyElement(attribute_name=entry[ATTRIBUTE_NAME], key_type=entry[KEY_TYPE])
            for entry in description[TABLE][KEY_SCHEMA]
        ]
    except (KeyError, TypeError, ValidationError) as error:
        raise BackupError(f"invalid DynamoDB table description: {error}") from error


def _write_table(client: Any, table_name: str, path: Path) -> int:
    count = 0
    scan_arguments: dict[str, Any] = {"TableName": table_name, "ConsistentRead": True}
    with gzip.open(path, "wt", encoding="utf-8", newline="\n") as stream:
        while True:
            response = client.scan(**scan_arguments)
            for item in response[ITEMS]:
                stream.write(_encode_item(item))
                stream.write("\n")
                count += 1
            if LAST_EVALUATED_KEY not in response:
                break
            scan_arguments[EXCLUSIVE_START_KEY] = response[LAST_EVALUATED_KEY]
    path.chmod(0o600)
    return count


def backup_directory(
    client: Any, destination: Path, table_names: Sequence[str] | None = None
) -> BackupManifest:
    """Create a new backup directory. Existing paths are never overwritten."""
    selected = _select_table_names(client, table_names)
    try:
        destination.mkdir(mode=0o700, parents=True, exist_ok=False)
        destination.chmod(0o700)
    except FileExistsError as error:
        raise BackupError(f"destination already exists: {destination}") from error

    tables: list[TableArchive] = []
    for index, table_name in enumerate(selected, start=1):
        description = client.describe_table(TableName=table_name)
        filename = f"table-{index:04d}.ddb"
        path = destination / filename
        item_count = _write_table(client, table_name, path)
        tables.append(
            TableArchive(
                table_name=table_name,
                filename=filename,
                item_count=item_count,
                sha256=_sha256(path),
                key_schema=_key_schema(description),
            )
        )

    manifest = BackupManifest(
        created_at=datetime.now(timezone.utc),
        region=client.meta.region_name,
        tables=tables,
    )
    manifest_path = destination / MANIFEST_FILENAME
    manifest_path.write_text(
        json.dumps(manifest.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    manifest_path.chmod(0o600)
    return manifest


def load_manifest(directory: Path) -> BackupManifest:
    try:
        manifest = BackupManifest.model_validate_json(
            (directory / MANIFEST_FILENAME).read_text(encoding="utf-8")
        )
    except (OSError, ValidationError) as error:
        raise BackupError(f"invalid backup manifest: {error}") from error
    table_names = [table.table_name for table in manifest.tables]
    filenames = [table.filename for table in manifest.tables]
    if len(table_names) != len(set(table_names)) or len(filenames) != len(set(filenames)):
        raise BackupError("manifest contains duplicate tables or filenames")
    return manifest


def _select_archives(
    manifest: BackupManifest, requested: Sequence[str] | None
) -> list[TableArchive]:
    if not requested:
        return manifest.tables
    requested_names = set(requested)
    available_names = {table.table_name for table in manifest.tables}
    missing = sorted(requested_names - available_names)
    if missing:
        raise BackupError(f"table not present in backup: {', '.join(missing)}")
    return [table for table in manifest.tables if table.table_name in requested_names]


def _validate_file(directory: Path, table: TableArchive) -> None:
    path = directory / table.filename
    if not path.is_file():
        raise BackupError(f"backup file is missing: {table.filename}")
    digest = _sha256(path)
    if digest != table.sha256:
        raise BackupError(f"checksum mismatch for {table.filename}")


def _key_fingerprint(item: WireItem, key_schema: Sequence[KeyElement]) -> str:
    key: dict[str, WireValue] = {}
    for element in key_schema:
        if element.attribute_name not in item:
            raise BackupError(f"record is missing key attribute {element.attribute_name!r}")
        key[element.attribute_name] = _encode_av(item[element.attribute_name])
    return json.dumps(key, separators=(",", ":"), sort_keys=True)


def _preflight(client: Any, directory: Path, tables: Sequence[TableArchive]) -> None:
    """Validate every selected table and record before restore performs any write."""
    available = set(_list_tables(client))
    for table in tables:
        if table.table_name not in available:
            raise BackupError(f"restore target table does not exist: {table.table_name}")
        target_schema = _key_schema(client.describe_table(TableName=table.table_name))
        expected = {(entry.attribute_name, entry.key_type) for entry in table.key_schema}
        actual = {(entry.attribute_name, entry.key_type) for entry in target_schema}
        if actual != expected:
            raise BackupError(f"key schema mismatch for table {table.table_name}")
        _validate_file(directory, table)
        seen_keys: set[str] = set()
        count = 0
        for line_number, item in _iter_archive_items(directory / table.filename):
            try:
                fingerprint = _key_fingerprint(item, table.key_schema)
            except BackupError as error:
                raise BackupError(f"{table.filename}:{line_number}: {error}") from error
            if fingerprint in seen_keys:
                raise BackupError(f"{table.filename}:{line_number}: duplicate primary key")
            seen_keys.add(fingerprint)
            count += 1
        if count != table.item_count:
            raise BackupError(
                f"record count mismatch for {table.filename}: expected {table.item_count}, found {count}"
            )


def _write_batch(client: Any, table_name: str, items: Sequence[WireItem]) -> None:
    pending = [{PUT_REQUEST: {ITEM: item}} for item in items]
    for attempt in range(MAX_BATCH_RETRIES + 1):
        response = client.batch_write_item(RequestItems={table_name: pending})
        pending = response.get(UNPROCESSED_ITEMS, {}).get(table_name, [])
        if not pending:
            return
        if attempt < MAX_BATCH_RETRIES:
            time.sleep(min(0.05 * (2**attempt), 2.0))
    raise BackupError(
        f"DynamoDB did not process {len(pending)} records for {table_name} after retries"
    )


def restore_directory(
    client: Any, directory: Path, table_names: Sequence[str] | None = None
) -> list[tuple[str, int]]:
    """Upsert all selected records after validating the complete restore set."""
    tables = _select_archives(load_manifest(directory), table_names)
    _preflight(client, directory, tables)
    restored: list[tuple[str, int]] = []
    for table in tables:
        batch: list[WireItem] = []
        count = 0
        for _line_number, item in _iter_archive_items(directory / table.filename):
            batch.append(item)
            if len(batch) == MAX_BATCH_ITEMS:
                _write_batch(client, table.table_name, batch)
                count += len(batch)
                batch = []
        if batch:
            _write_batch(client, table.table_name, batch)
            count += len(batch)
        restored.append((table.table_name, count))
    return restored


def _jsonable(value: Any) -> Any:
    if isinstance(value, Decimal):
        converted = int(value) if value == value.to_integral_value() else {"$number": str(value)}
    elif isinstance(value, Binary):
        converted = {
            "$binary": base64.b64encode(cast(Any, value).value).decode("ascii")
        }
    elif isinstance(value, (bytes, bytearray)):
        converted = {"$binary": base64.b64encode(bytes(value)).decode("ascii")}
    elif isinstance(value, set):
        converted = [_jsonable(entry) for entry in value]
        converted = sorted(converted, key=lambda entry: json.dumps(entry, sort_keys=True))
    elif isinstance(value, list):
        converted = [_jsonable(entry) for entry in value]
    elif isinstance(value, dict):
        converted = {name: _jsonable(child) for name, child in value.items()}
    else:
        converted = value
    return converted


def view_directory(
    directory: Path,
    output: TextIO,
    table_names: Sequence[str] | None = None,
) -> int:
    """Write human-readable JSON Lines after validating archive checksums."""
    tables = _select_archives(load_manifest(directory), table_names)
    count = 0
    deserializer = TypeDeserializer()
    for table in tables:
        _validate_file(directory, table)
        table_count = 0
        for _line_number, item in _iter_archive_items(directory / table.filename):
            decoded = {
                name: deserializer.deserialize(cast(Any, value))
                for name, value in item.items()
            }
            output.write(
                json.dumps(
                    {"table": table.table_name, "item": _jsonable(decoded)},
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                )
                + "\n"
            )
            table_count += 1
            count += 1
        if table_count != table.item_count:
            raise BackupError(
                f"record count mismatch for {table.filename}: expected {table.item_count}, found {table_count}"
            )
    return count


def require_directory(path: str) -> Path:
    directory = Path(path).expanduser()
    if not directory.is_dir():
        raise BackupError(f"backup directory does not exist: {directory}")
    return directory
