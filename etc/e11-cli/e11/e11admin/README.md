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
