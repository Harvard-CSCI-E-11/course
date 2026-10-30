# Route archive commands before importing the AWS-backed administration app.
# The viewer reads and decodes local archives without resolving AWS credentials.
# Backup and restore create a DynamoDB client only after argument validation.
# Restores require an explicit command-line opt-in and skip sessions by default.
# Shared parser wiring keeps console help and the administration module aligned.
# Other administration commands retain their existing entry point and behavior.
"""Lightweight archive commands and dispatch for the e11admin console tool."""

import argparse
import os
import sys
from importlib import import_module
from pathlib import Path
from typing import Any

import boto3

from .dynamodb_backup import BackupError, backup_directory, require_directory, restore_directory, view_directory


def do_backup(args: argparse.Namespace) -> None:
    client = boto3.client("dynamodb", region_name=os.environ.get("AWS_REGION"))
    try:
        manifest = backup_directory(client, args.directory, args.table)
    except BackupError as error:
        raise SystemExit(f"backup failed: {error}") from error
    for table in manifest.tables:
        print(f"{table.table_name}: {table.item_count} records -> {table.filename}")
    print(f"Backup complete: {args.directory}")


def do_restore(args: argparse.Namespace) -> None:
    if not getattr(args, "allow_restore", False):
        raise SystemExit("restore requires --allow-restore")
    try:
        directory = require_directory(str(args.directory))
        client = boto3.client("dynamodb", region_name=os.environ.get("AWS_REGION"))
        restored = restore_directory(client, directory, args.table)
    except BackupError as error:
        raise SystemExit(f"restore failed: {error}") from error
    for table_name, item_count in restored:
        print(f"{table_name}: restored {item_count} records")
    if not args.table:
        print("Session tables skipped by default; select one explicitly with --table to restore it.")


def do_view(args: argparse.Namespace) -> None:
    try:
        view_directory(require_directory(str(args.directory)), sys.stdout, args.table)
    except BackupError as error:
        raise SystemExit(f"view failed: {error}") from error


def add_archive_commands(subparsers: Any) -> None:
    for command, handler, help_text in [
        ("backup", do_backup, "Back up DynamoDB tables to a new local directory"),
        ("restore", do_restore, "Restore DynamoDB records as idempotent upserts"),
        ("view", do_view, "Write local backup records as JSON Lines without AWS access"),
    ]:
        parser = subparsers.add_parser(command, help=help_text)
        parser.add_argument("directory", type=Path, help="New directory" if command == "backup" else "Backup directory")
        parser.add_argument("--table", action="append",
                            help="Table to include (repeatable; default: all except sessions for restore)")
        if command == "restore":
            parser.add_argument("--allow-restore", action="store_true", required=True,
                                help="Explicitly permit writes to the configured DynamoDB tables")
        parser.set_defaults(func=handler)


def main() -> int:
    if sys.argv[1:2] not in (["backup"], ["restore"], ["view"]):
        return import_module(".cli", __package__).main()
    parser = argparse.ArgumentParser(prog="e11admin")
    add_archive_commands(parser.add_subparsers(dest="command", required=True))
    args = parser.parse_args()
    args.func(args)
    return 0
