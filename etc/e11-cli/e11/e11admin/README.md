# e11admin - E11 Admin CLI Tool

This is the admin tool for E11 faculty to run on their desktop computers.
It is not designed for use by students.

## Installation

`e11admin` is installed as part of the main `e11` package. It is available as a CLI command
after installing the e11 package:

```bash
# Install the e11 package (which includes e11admin)
cd /path/to/e11-cli
uv sync --locked

# Run e11admin commands
uv run --locked e11admin <command>
```

## Usage

The `e11admin` command provides staff-only administrative functions for managing
the E11 course infrastructure. It is installed as a standard project script entry point
alongside the main `e11` command.

The `AWS_PROFILE` variable must be set to an AWS Profile that has read/write access to the appropriate DynamoDB tables.

To see available commands:
```bash
uv run --locked e11admin --help
```

## DynamoDB backups

Create a backup in a new directory, inspect it as JSON Lines, and restore it:

```bash
AWS_PROFILE=e11-staff AWS_REGION=us-east-1 make ddb-backup DDB_DIR=/secure/path/backup-2026-09-06
make -s ddb-view DDB_DIR=/secure/path/backup-2026-09-06 > /secure/path/backup.jsonl
AWS_PROFILE=e11-staff AWS_REGION=us-east-1 make ddb-restore DDB_DIR=/secure/path/backup-2026-09-06 DDB_ALLOW_RESTORE=YES
```

Run these from `etc/e11-cli`. The explicit restore flag prevents an accidental
write. The direct CLI requires `e11admin restore DIRECTORY --allow-restore` as
well. Keep the backup and rendered JSON Lines outside the Git repository.

All three commands accept a repeatable `--table TABLE` option. With no
`--table`, `backup` includes every table visible to the current AWS account and
`view` includes every table in the manifest. Default restore skips `sessions`
and names ending in `-sessions`, so archived login sessions are not revived.
Restoring one requires explicitly naming it with `--table`; ordinarily recreate
session tables and require users to log in again.

The backup directory is created with mode `0700` and must not already exist.
It contains a versioned `manifest.json` and one gzip-compressed binary `.ddb`
file per table. The files retain DynamoDB's typed attribute representation,
including exact numbers, binary values, sets, maps, and lists. The manifest
records each table's primary-key schema, local secondary index layout, record
count, and SHA-256 checksum. New backups use format version 2; this tool also
reads version 1 archives.
Treat the directory as sensitive course data and do not commit it.

`restore` performs a full preflight before its first write: it verifies the
manifest, checksums, record counts, target-table key schemas, every record's
primary key, primary/index key attribute types and byte limits, and duplicate
keys. A destination with local secondary indexes must exactly match the archived
local index names, keys, and projections, because adding a projection can exceed
DynamoDB’s combined item-size limit. Version 1 archives lack this metadata and
cannot restore into destinations with local secondary indexes; create a new
backup with this version first. Destinations without local indexes still accept
version 1 archives. Use unmodified archives produced by `backup`; manually
editing `.ddb` records and regenerating checksums is unsupported.

Write batches respect both the 25-item and 16 MiB request limits,
including JSON escaping and binary expansion. It then uses DynamoDB `PutRequest` operations,
so an existing item with the same partition and sort key is replaced and
re-running the restore is idempotent. Items in the target table that are absent
from the backup are not deleted. A service failure during writes can leave a
partial restore, but it is safe to rerun the same command.

`view` works offline without an AWS profile, region, or credential lookup. It
writes one object per line with `table` and `item` fields. Binary values
appear as `{"$binary":"BASE64"}` and non-integral exact numbers as
`{"$number":"..."}`. This rendering is for review only; restore always reads
the lossless `.ddb` files.

For a coherent multi-table rollover backup, stop application writes before
running `backup`. Consistent DynamoDB scans do not provide a transactionally
consistent snapshot across pages or tables.

## End-of-course DNS cleanup

See [End of Course Procedure](../../../../doc/End%20of%20Course%20Procedure.md)
for the backup and deletion sequence. From the Git root or `etc/e11-cli`, use
`make dns-plan` to select every name in the step-3 Route 53 export that does not
match `dns-keep.txt`. It displays each deletion and saves complete record sets.
`make dns-delete` applies that saved plan after checking the keep-list, account,
hosted zone, and live records, then waits for `INSYNC`. It requires no copied hash
or interactive confirmation. See the [CLI README](../../README.md#end-of-course-dns-cleanup)
for variables and path overrides. No student-name list is needed.

New grading-history command:
```bash
uv run --locked e11admin student-log student@example.edu
uv run --locked e11admin student-log student@example.edu lab2
uv run --locked e11admin student-log --user-id 3c139e61-4932-4f2d-910d-fe8a5fc1741d lab2
uv run --locked e11admin student-log student@example.edu lab2 --verbose
uv run --locked e11admin canvas-grades lab2 --template canvas.csv --outfile canvas-out.csv
uv run --locked e11admin status
```

Commands that select an existing student accept either `--email <email>` or
`--user-id <user_id>`/`--user_id <user_id>`. Positional email arguments remain
available for existing workflows.

## Development

To validate the e11admin code, use the main Makefile:
```bash
cd /path/to/e11-cli
make check
```

See the main project README and ARCHITECTURE.md for more information about the e11 package structure.
