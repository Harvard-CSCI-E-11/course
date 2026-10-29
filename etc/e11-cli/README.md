This directory contains the following:
* e11/ - The source code for the e11 command
* lambda-home/ - The AWS Lambda function at https://csci-e-11.org/ (dashboard, registration, grading)
* lambda-leaderboard/ - The AWS Lambda function for the course leaderboard
* lambda-users-db/ - The SAM template for creating the e11-users DynamoDB table
* tests/ - Tests for the e11 CLI and grader system

You will also find in this directory:
* e11/__main__.py - Entry point for the e11 command
* e11/main.py - Main CLI command handler
* e11/e11core/ - Core grader framework modules
  * assertions.py - Test assertion helpers
  * config.py - E11Config class for configuration
  * constants.py - Project constants (course name, domain, etc.)
  * context.py - E11Context dataclass for passing lab context
  * decorators.py - @timeout and @retry decorators
  * e11ssh.py - SSH connection wrapper for remote grading
  * grader.py - Test discovery and execution framework
  * testrunner.py - TestRunner class (local/remote execution)
  * utils.py - Logging and utility functions
* e11/e11admin/ - Staff administration CLI tool
* e11/lab_tests/ - Lab test definitions (lab0-lab8)

Various directories are created:

* dist/ - The whl file that installs the e11 command

# The `e11` command
CSCI E-11 uses the `e11` command to let students control access to their AWS Instance.

The command implements these subcommands:

## The primary `e11` commands
* `e11 config` - Used to edit the configuration variables stored in `/home/ubuntu/e11-config.ini`
* `e11 register` - Registers your instance with the CSCI E-11 infrastructure, which sets up your DNS.
* `e11 status` - Status report
* `e11 version` - Show version information for both local and server
* `e11 update` - Update the e11 system
* `e11 doctor` - Run system diagnostics

## The `e11 access` subcommand
* `e11 access on` - Allows the class staff to `ssh` into your instance. This is required for grading and is the default mode.
* `e11 access off` - Disables access to your instance. Your instance lab cannot be graded if access is off.
* `e11 access check` - Reports if access is enabled or disabled.
* `e11 access check-dashboard` - Check SSH access status from the dashboard for authenticated users

## The `e11 check` subcommand
* `e11 check [lab1|lab2|lab3|lab4|lab5|lab6|lab7|lab8]` - Runs the lab checker for each lab. Not every aspect of the lab is checked, but many are.

## The `e11 grade` subcommand
* `e11 grade [lab]` - Request lab grading (typically run from course server)
* `e11 grade [lab] --direct` - Grade directly from this system (requires SSH access to target)
* `e11 grade [lab] --verbose` - Print all grading details

## The `e11 answer` subcommand
* `e11 answer [lab]` - Answer additional questions for a particular lab prior to grading (e.g., API keys for lab4, lab5, lab6)

## The `e11 report` subcommand
* `e11 report tests` - List all available tests in markdown format

## The `e11 lab8` subcommand
* `e11 lab8 --upload [file]` - Upload a file for lab8

## Global Options

These options must be placed **before** the subcommand:
* `e11 --debug <command>` - Run in debug mode
* `e11 --stage <command>` - Use stage API instead of production
* `e11 --force <command>` - Run even if not on EC2 (useful for local testing)
* `e11 --keyfile <path> <command>` - Specify SSH private key file for grading

Example: `e11 --force doctor` (not `e11 doctor --force`)

## Staff Commands

### Staff Commands in `e11` (requires `E11_STAFF` environment variable)
When the `E11_STAFF` environment variable is set, additional staff-only commands are available.

**Staff commands require AWS credentials:**
```bash
E11_STAFF=1 AWS_REGION=us-east-1 AWS_PROFILE=e11-staff uv run --locked e11 <command>
```

Available staff commands:
* `e11 check-access <host>` - Check SSH accessibility to a student's VM
* `e11 register-email <email>` - Register an email address directly with DynamoDB
* `e11 student-report` - Generate user report from DynamoDB (shows table stats and registered users)
* `e11 student-report --dump` - Dump all user information
* `e11admin print-grades <email>` - Show all grades for a specific student
* `e11admin print-grades --user-id <user_id>` - Show all grades for a specific student by `user_id`
* `e11admin print-grades <lab>` - Show all grades for a specific lab (e.g., `lab1`)
* `e11admin student-log <email> [lab] [--verbose]` - Show a student's grading history from DynamoDB
* `e11admin student-log --user-id <user_id> [lab] [--verbose]` - Show a student's grading history by `user_id`

### The `e11admin` Command
The `e11admin` command is a separate CLI tool for faculty to run on their desktop computers.
It is installed alongside the `e11` command when you install the e11 package.

**Running e11admin requires AWS SSO authentication:**

1. First, authenticate with AWS SSO:
```bash
AWS_REGION=us-east-2 AWS_PROFILE=e11-staff aws sso login
```

2. Navigate to the e11-cli directory and install dependencies:
```bash
cd etc/e11-cli
uv sync --locked
```

3. Run e11admin with the required environment variables:
```bash
E11_STAFF=1 AWS_REGION=us-east-1 AWS_PROFILE=e11-staff uv run --locked e11admin
```

| Variable | Description |
|----------|-------------|
| `E11_STAFF=1` | Enables staff-only commands |
| `AWS_REGION=us-east-1` | AWS region where DynamoDB tables are located |
| `AWS_PROFILE=e11-staff` | AWS CLI profile configured for SSO |

**Notes:**
- The `e11-staff` AWS profile must be configured in `~/.aws/config` for SSO access
- SSO login uses `us-east-2`, but DynamoDB operations use `us-east-1`
- Running `e11admin` without arguments displays all registered users and DynamoDB tables
- Python 3.14 is required.

Student selectors:
* `--email <email>` - Select a student by email where the command supports a student selector
* `--user-id <user_id>` or `--user_id <user_id>` - Select a student by `user_id`

Selected options:
* `backup <new-directory> [--table <name>]` - Create lossless local DynamoDB archives and a checksummed manifest
* `view <backup-directory> [--table <name>]` - Render archived records as JSON Lines for review
* `restore <backup-directory> [--table <name>]` - Validate the complete archive and idempotently upsert its records
* `class --dump` - Dump all table data
* `class --delete-userid <id>` or `class --delete_userid <id>` - Delete a user by `user_id`
* `class --delete_item --user-id <id> --sk <key>` - Delete a specific item
* `class --newkey <email>` - Create a new course key for a user by email
* `class --newkey --user-id <id>` - Create a new course key for a user by `user_id`
* `ssh --email <email>` or `ssh --user-id <id>` - SSH into a student's VM

See `e11/e11admin/README.md` for details.

The backup directory contains sensitive course data. Keep it out of the
repository. Stop application writes during the final rollover backup because
consistent DynamoDB scans are not a cross-table snapshot.

## End-of-course DNS cleanup

After exporting the complete Route 53 zone in
[End of Course Procedure](../../doc/End%20of%20Course%20Procedure.md), review
`dns-keep.txt` and run these targets from this directory or the Git root:

```bash
export DDB_DIR="$HOME/e11-backup-$(date -I)"
export DNS_ZONE_ID=HOSTED_ZONE_ID
export DNS_ACCOUNT_ID=ACCOUNT_ID
make dns-plan
# Review the displayed deletions before running:
make dns-delete
```

The planner reads the saved export without contacting AWS. Every name not matched
by the keep-list is selected, with all its record types and routing fields.
Keep-list entries are case-insensitive DNS names or shell globs (`*`, `?`, `[abc]`);
trailing dots are optional, `*` spans dots, and blank lines and full-line `#`
comments are ignored. The apex must be kept. Traffic-policy-instance records need
separate Route 53 handling if selected.

| Variable | Purpose and default |
|----------|---------------------|
| `DDB_DIR` | Backup prefix; the step-3 export is `$(DDB_DIR)-route53.json` |
| `DNS_ZONE_EXPORT` | Override the export path; defaults to `$(DDB_DIR)-route53.json` |
| `DNS_KEEP` | Keep-list path; defaults to `dns-keep.txt` in `etc/e11-cli` |
| `DNS_PLAN` | Saved plan; defaults to `$(DNS_ZONE_EXPORT).delete-plan.json` |
| `DNS_DOMAIN` | Hosted-zone name; defaults to `csci-e-11.org` |
| `DNS_ZONE_ID` | Required hosted-zone ID; accepts bare IDs or `/hostedzone/ID` |
| `DNS_ACCOUNT_ID` | Required AWS account ID, verified before deletion |
| `AWS_PROFILE` | AWS credential profile, using normal AWS credential resolution |
| `DNS_PROFILE` | Optional profile override for this program |

Use absolute paths for overrides when invoking targets from the Git root.
Re-running `dns-plan` replaces its saved plan. `dns-delete` uses that exact plan,
requires an unchanged keep-list, verifies live records at every planned name,
and waits for each deletion batch to become `INSYNC`. It needs no hash or extra
confirmation. New names created after the export are not added to the plan.
After a partial failure, export again and create a fresh plan for the remainder.
An empty plan succeeds without AWS calls.

Run `make dns-test` for focused offline tests and `make dns-lint` for DNS code
checks. Live DNS deletion is a separate operator action.

## DNS query logging

The standalone `e11/e11admin/dns_logging.py` script enables public Route 53 query
logging in CloudWatch Standard with 180-day retention and verifies a test query.
Run `make dns-logging-enable DNS_ZONE_ID=HOSTED_ZONE_ID` with existing AWS
credentials. Use `make dns-logging-status`, `make dns-logs`, and
`make dns-log-report` for configuration, individual lookups, and per-hostname
summaries. These targets also work from the Git root. S3 export is deferred.

The AWS profile and DNS destination variables are described above. Logging adds:

| Variable | Purpose/default |
|----------|-----------------|
| `DNS_LOG_GROUP` | Existing destination, or `/aws/route53/DOMAIN` for new logging |
| `DNS_LOG_SINCE` | Lookback such as `24h`; defaults to `1h` for events, `30d` for reports |
| `DNS_LOG_UNTIL` | ISO 8601 end time with time zone; defaults to now |
| `DNS_LOG_NAME` | One short or fully qualified hostname |
| `DNS_LOG_STUDENT` | Student hostname stem including its `-labN` names; excludes `DNS_LOG_NAME` |
| `DNS_LOG_LIMIT` | Maximum rows, 1–10,000; defaults to 100 events or 10,000 report rows |
| `DNS_LOG_FORMAT` | Output format: `table` (default), `csv`, or `json` |

[DNS query logging](../../doc/Enable%20DNS%20Logging.md) covers costs, permissions,
retention, and the limits of interpreting DNS queries as student activity. For
logging, `DNS_ACCOUNT_ID` is optional and `DNS_LOG_GROUP` can reuse an existing
destination; `DNS_ZONE_ID` remains required.
Run `make dns-logging-test` and `make dns-logging-lint` for focused validation.

# DynamoDB Database Structure

The E11 system uses four DynamoDB tables:

## e11-users Table
The main table storing user records, grades, logs, and images.

| Attribute | Description |
|-----------|-------------|
| `user_id` (PK) | Partition key - UUID for each user |
| `sk` (SK) | Sort key - determines record type |
| `email` | Student email address (GSI) |

### Sort Key Patterns
| Pattern | Description |
|---------|-------------|
| `#` | User record (main profile) |
| `grade#<lab>#<timestamp>` | Grade records for lab submissions |
| `log#<timestamp>` | User activity log entries |
| `image#<lab>#<timestamp>` | Lab 8 image upload records |
| `leaderboard-log#<timestamp>` | Leaderboard activity records |

### Global Secondary Index
* **GSI_Email** - Partition key: `email`, Projection: ALL

## home-app-sessions Tables
Session management for the web dashboard. Table names vary by environment:
* `home-app-prod-sessions` - Production
* `home-app-stage-sessions` - Staging

| Attribute | Description |
|-----------|-------------|
| `sid` (PK) | Session ID (UUID) |
| `email` | User email (GSI) |
| `session_created` | Creation timestamp |
| `session_expire` | Expiration timestamp |

## Leaderboard Table
Stores Lab 7 leaderboard entries.

| Attribute | Description |
|-----------|-------------|
| `name` (PK) | Unique leader name |
| `first_seen` | When first added |
| `last_seen` | Last activity timestamp |
| `score` | Leaderboard score |

# Safe CLI Commands for Development

The following commands are read-only and safe for testing:

```bash
# Help and documentation
e11 --help                    # Show all commands
e11 <command> --help          # Show help for specific command

# Status and diagnostics
e11 version                   # Show local and server version
e11 status                    # Display configuration state
e11 doctor                    # Run system diagnostics

# Reports
e11 report tests              # List all available tests (markdown)

# Access checking (informational only)
e11 access check              # Check if SSH access is enabled
```

# Development Workflow

For detailed architecture documentation, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Prerequisites
* Python 3.14 (CLI and Lambdas)
* uv (Python, dependency, environment, and package management)
* AWS SAM CLI (for Lambda deployment)

## Setting Up Development Environment

```bash
cd etc/e11-cli
uv sync --locked
uv run --locked e11 --help
```

## Building and Testing

```bash
# Run tests with coverage
make check

# Run linting (pylint + pyright)
make lint

# Test all components (CLI + both Lambdas)
make check-all
```

## Vendored Wheel Pattern

**IMPORTANT**: The `e11/` package is built into a wheel and vendored into Lambda functions:
* `lambda-home/src/home_app/e11.whl`
* `lambda-leaderboard/src/leaderboard_app/e11.whl`

After modifying `e11/` or `e11core/`:
```bash
uv build --wheel
cd lambda-home && make vend-e11
cd ../lambda-leaderboard && make vend-e11
```

## Local DynamoDB Testing

```bash
make start_local_dynamodb     # Start DynamoDB Local
make stop_local_dynamodb      # Stop DynamoDB Local
```

# How it Works

This program can be found in the [spring27 repository](https://github.com/Harvard-CSCI-E-11/spring27/tree/main/etc/e11-cli). Students check out that repository as `$HOME/course`; the [install-e11](https://github.com/Harvard-CSCI-E-11/spring27/blob/main/etc/install-e11) installation script then installs `e11` as a uv tool in `$HOME/.local/bin`.

## Running from this repo

```bash
uv sync --locked
uv run --locked e11
```

## Package Entry Points

The package defines two CLI entry points in `pyproject.toml`:
* `e11` - Main student CLI command
* `e11admin` - Staff administration CLI command

## Related Documentation
* [ARCHITECTURE.md](ARCHITECTURE.md) - Detailed system architecture and data flows
* [TESTING_STRATEGY.md](TESTING_STRATEGY.md) - Testing approach and patterns
* [e11/e11admin/README.md](e11/e11admin/README.md) - Admin CLI documentation
