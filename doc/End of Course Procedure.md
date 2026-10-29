End of Course Procedure
=======================

This procedure preserves the completed course, removes student DNS records, and
prepares the infrastructure for the next class. It is intentionally conservative:
the backup and review gates must be complete before any deletion.

Goals:
-----
* Preserve the completed course
* Removes student DNS records
* Prepare the infrastructure for the next class.

Tools:
------
The DNS cleanup program is
`etc/e11-cli/e11/e11admin/end-of-term/cleanup_dns.py`. It creates a reviewable
plan from the Route 53 export and `etc/e11-cli/dns-keep.txt`. Every name not
matched by the keep-list is selected for deletion. `make dns-plan` displays and
saves the plan; `make dns-delete` checks the account, zone, and live records,
then deletes the saved record sets.

The umbrella tracking checklist is [Spring 2027 preparation and rollover checklist](https://github.com/Harvard-CSCI-E-11/spring27/issues/64).

This procedure is intentionally conservative: the backup and review gates must be complete before any deletion.


Procedures
-------------------

### 1. Assign responsibility and schedule downtime

1. Make sure grades are submitted!
2. Assign one operator and one independent reviewer.
3. Schedule a maintenance window and stop registration, grading, leaderboard,
   session, and other application writes.
4. Record the repository commit, AWS account ID, region, hosted-zone ID, and deployed stack versions.
5. Do not combine rehearsal and production cleanup. Complete the dry run, review
   it, and preserve its output before authorizing deletion.

### 2. Back up DynamoDB

Authenticate to the intended production account and verify the caller identity
before creating the backup. The destination must be a new directory on encrypted
storage and must not be inside a Git repository.

First check:
```console
printenv | grep AWS
OP_BYPASS_AWS=1
AWS_REGION=us-east-1
AWS_PROFILE=fas


% aws sts get-caller-identity
{
    "UserId": "AIDAYRH5NHXAA6D3KYAPJ",
    "Account": "****",
    "Arn": "arn:aws:iam::****:user/admin-sgarfinkel"
}
%
```

Now run these commands:

```console
GIT_ROOT=$HOME/gits/e11-course
cd $GIT_ROOT/etc/e11-cli
BACKUP_ROOT=$HOME/e11-backup-$(date -I)
make ddb-backup DDB_DIR=$BACKUP_ROOT
```
Notes:
1. `make ddb-backup` creates `manifest.json` and one compressed binary `.ddb` file
per table. The destination cannot already exist. With no `--table` option it backs
up every DynamoDB table visible to the account.

2. To review the archive without modifying it:

```console
$ make -s ddb-view DDB_DIR=$BACKUP_ROOT > $HOME/e11-backup-$(date -I).jsonl
```

Before continuing:

- Confirm the manifest contains every intended table.
- Compare manifest item counts with fresh production counts.
- Copy the backup to the approved encrypted archive and recheck its SHA-256 checksums.
- Copy the backup to the approved encrypted archive and recheck its SHA-256 checksums.
- Restore it into empty DynamoDB Local tables with matching key schemas, then run
  the restore a second time to prove idempotence.
- Preserve the backup location, manifest hash, commands, results, operator, and
  reviewer in the rollover record.

For the restore drill, start DynamoDB Local with `make start_local_dynamodb`,
create empty tables matching the manifest's key schemas, and run this from
`etc/e11-cli` twice. The endpoint and dummy credentials keep this drill local:

```console
AWS_ENDPOINT_URL_DYNAMODB=http://localhost:8000 AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test \
AWS_DEFAULT_REGION=us-east-1 make ddb-restore DDB_DIR=$BACKUP_ROOT DDB_ALLOW_RESTORE=YES
```

Restore performs idempotent upserts: an existing record with the same partition
and sort key is replaced. It does not delete destination records that are absent
from the backup.

### 3. Export the Route 53 zone before cleanup

Save the complete hosted-zone record-set response before preparing a delete list.
This export is the source needed to reconstruct aliases, weighted records, latency
records, failover records, and other Route 53 details.

```console
aws route53 list-hosted-zones-by-name --dns-name csci-e-11.org

HOSTED_ZONE_ID=$(aws route53 list-hosted-zones-by-name --dns-name csci-e-11.org | jq -r '.HostedZones[0].Id')

aws route53 list-resource-record-sets --hosted-zone-id $HOSTED_ZONE_ID > $BACKUP_ROOT-route53.json
```

Verify the contents of `$BACKUP_ROOT-route53.json`

Route 53 records do not contain a last-used timestamp. Unless DNS query logging
was enabled during the course, the last time a student used a DNS name is unknown.
A record's existence or modification time must not be reported as usage.

### 4. Create and review the DNS plan

Review `etc/e11-cli/dns-keep.txt`: it lists the only names to preserve, including
the zone apex, certificate/email validation records, grader, leaderboard, stage,
and autodiscover. All record types at every other name will be deleted, including
`simsong.csci-e-11.org`. Names are case-insensitive and trailing dots are optional.
Shell globs (`*`, `?`, `[abc]`) are supported; `*` can span multiple DNS labels.

Use the complete Route 53 export from step 3. No student-name list is needed.
From the Git root or `etc/e11-cli`:

```console
export DNS_DOMAIN=csci-e-11.org
export DNS_ZONE_ID=$HOSTED_ZONE_ID
export DNS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
export DDB_DIR=$BACKUP_ROOT
make dns-plan
```

`make dns-plan` reads `$DDB_DIR-route53.json`, prints every proposed deletion
as `WILL DELETE` (name, type, and routing identifier), and saves the exact record sets to
`$DDB_DIR-route53.json.delete-plan.json`. It does not contact AWS. Re-running it
replaces the plan, so review its latest output before deleting. Use
`DNS_ZONE_EXPORT`, `DNS_KEEP`, or `DNS_PLAN` to override the default paths.
The summary counts record sets selected for deletion and those kept in the export.

## 5. Delete the domains


```console
make dns-delete
```

This applies the saved plan without a copied hash or another confirmation. It
refuses to delete if the keep-list, account, hosted zone, or records at planned
names have changed. It waits for each Route 53 batch to become `INSYNC`.
Before submitting, it prints the number to delete and expected number left in
the zone. Each batch reports its size, completed deletions, and number still to
delete. The final summary counts records remaining in a fresh zone inventory.
Names created after the step-3 export are not added to the saved plan.
An empty plan is a successful no-op. If a batch fails after earlier batches
succeeded, export the zone again and run `make dns-plan` for the remaining records.
After deletion, export the zone again and compare it with the saved inventory:
planned records should be absent and kept records unchanged. Test the sites in
step 7.

## 6. Reset course data


## 7. Close the maintenance window

1. Test https://csci-e-11.org/ with Harvard Key to make sure that you can log in.
2. Test https://leaderboard.csci-e-11.org/ to make sure leaderboard is working.

<!--  LocalWords:  FERPA
 -->
