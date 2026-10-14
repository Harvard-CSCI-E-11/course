<<<<<<< HEAD
# End of Course Procedure

This procedure preserves the completed course, removes student DNS records, and
prepares the infrastructure for the next class. It is intentionally conservative:
the backup and review gates must be complete before any deletion.

The DNS cleanup program is
`etc/e11-cli/e11/e11admin/end-of-term/cleanup_dns.py`. It creates a reviewable
plan from an explicit list of student names. Applying that plan requires its
SHA-256 hash and verifies the AWS account, hosted zone, and live record sets.
Do not apply a plan until an independent reviewer has approved the exact file.

The umbrella tracking checklist is [Spring 2027 preparation and rollover
checklist](https://github.com/Harvard-CSCI-E-11/spring27/issues/64).

## 1. Assign responsibility and schedule downtime

1. Assign one operator and one independent reviewer.
2. Schedule a maintenance window and stop registration, grading, leaderboard,
   session, and other application writes.
3. Record the repository commit, AWS account ID, region, hosted-zone ID, and
   deployed stack versions.
4. Do not combine rehearsal and production cleanup. Complete the dry run, review
   it, and preserve its output before authorizing deletion.

## 2. Back up DynamoDB
=======
End of Course Procedure
=======================

Goals:
-----
* Preserve the completed course
* Removes student DNS records
* Prepare the infrastructure for the next class.

This procedure is intentionally conservative: the backup and review gates must be complete before any deletion.

The umbrella tracking checklist is
[Spring 2027 preparation and rollover checklist](https://github.com/Harvard-CSCI-E-11/spring27/issues/64).

Elements:
--------
DNS cleanup program - `etc/e11-cli/e11/e11admin/end-of-term/cleanup_dns.py`.

* Creates a reviewable plan from an explicit list of student names.
* Applying that plan requires its SHA-256 hash and verifies the AWS account, hosted zone, and live record sets.
* Does not apply a plan until an independent reviewer has approved the exact file.

Checklist
---------

### 1. Assign responsibility and schedule downtime

1. Assign one operator and one independent reviewer.
2. Make sure grades are submitted!
3. Record the repository commit, AWS account ID, region, hosted-zone ID, and deployed stack versions.
4. Do not combine rehearsal and production cleanup. Complete the dry run, review
   it, and preserve its output before authorizing deletion.

### 2. Back up DynamoDB
>>>>>>> dev-slg

Authenticate to the intended production account and verify the caller identity
before creating the backup. The destination must be a new directory on encrypted
storage and must not be inside a Git repository.

```console
$ AWS_PROFILE=fas aws sso login
$ AWS_PROFILE=fas aws sts get-caller-identity
$ cd /path/to/spring27/etc/e11-cli
$ AWS_PROFILE=fas AWS_REGION=us-east-1 make ddb-backup DDB_DIR=/secure/path/e11-backup-YYYY-MM-DD
```

`make ddb-backup` creates `manifest.json` and one compressed binary `.ddb` file
per table. The destination cannot already exist. With no `--table` option it backs
up every DynamoDB table visible to the account.

Review the archive without modifying it:

```console
$ make -s ddb-view DDB_DIR=/secure/path/e11-backup-YYYY-MM-DD > /secure/path/e11-backup-YYYY-MM-DD.jsonl
```

Before continuing:

- Confirm the manifest contains every intended table.
- Compare manifest item counts with fresh production counts.
<<<<<<< HEAD
- Copy the backup to the approved encrypted archive and recheck its SHA-256
  checksums.
=======
- Copy the backup to the approved encrypted archive and recheck its SHA-256 checksums.
>>>>>>> dev-slg
- Restore it into empty DynamoDB Local tables with matching key schemas, then run
  the restore a second time to prove idempotence.
- Preserve the backup location, manifest hash, commands, results, operator, and
  reviewer in the rollover record.

For the restore drill, start DynamoDB Local with `make start_local_dynamodb`,
create empty tables matching the manifest's key schemas, and run this from
`etc/e11-cli` twice. The endpoint and dummy credentials keep this drill local:

```console
$ AWS_ENDPOINT_URL_DYNAMODB=http://localhost:8000 AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 make ddb-restore DDB_DIR=/secure/path/e11-backup-YYYY-MM-DD DDB_ALLOW_RESTORE=YES
```

Restore performs idempotent upserts: an existing record with the same partition
and sort key is replaced. It does not delete destination records that are absent
from the backup.

<<<<<<< HEAD
## 3. Export the Route 53 zone before cleanup
=======
### 3. Export the Route 53 zone before cleanup
>>>>>>> dev-slg

Save the complete hosted-zone record-set response before preparing a delete list.
This export is the source needed to reconstruct aliases, weighted records, latency
records, failover records, and other Route 53 details.

```console
$ AWS_PROFILE=fas aws route53 list-hosted-zones-by-name --dns-name csci-e-11.org
$ AWS_PROFILE=fas aws route53 list-resource-record-sets --hosted-zone-id HOSTED_ZONE_ID > /secure/path/route53-before-YYYY-MM-DD.json
```

Verify that `HOSTED_ZONE_ID` belongs to the intended AWS account and exactly
matches `csci-e-11.org.`. Store the export beside the protected rollover backup;
do not commit it.

Route 53 records do not contain a last-used timestamp. Unless DNS query logging
was enabled during the course, the last time a student used a DNS name is unknown.
A record's existence or modification time must not be reported as usage.

<<<<<<< HEAD
## 4. Build the student-name list
=======
### 4. Build the student-name list
>>>>>>> dev-slg

Create a dated file outside Git containing **only** student-owned fully qualified
DNS names, one name per line. Derive it from the final roster and exported DNS
inventory; independently review every name. Include every record type at each
listed name. Do not list the zone apex, `leaderboard`, `stage`, `simsong`, or any
other infrastructure name. The old `keep-names.txt` is not an input to the new
planner.

The planner rejects names outside the zone, the zone apex, missing names, SOA/NS
records, and traffic-policy-instance records. Handle traffic-policy instances
through their own Route 53 API and a separate review.

<<<<<<< HEAD
## 5. Create and review the DNS plan
=======
### 5. Create and review the DNS plan
>>>>>>> dev-slg

From `etc/e11-cli`, set and independently verify the AWS account and hosted-zone
IDs. These are examples, not trusted production identifiers:

```console
$ export DNS_DOMAIN=csci-e-11.org
$ export DNS_ZONE_ID=HOSTED_ZONE_ID
$ export DNS_ACCOUNT_ID=ACCOUNT_ID
$ export DNS_NAMES=/secure/path/student-names-YYYY-MM-DD.txt
$ export DNS_PLAN=/secure/path/dns-delete-plan-YYYY-MM-DD.json
$ AWS_PROFILE=fas make dns-plan
```

`make dns-plan` performs a read-only Route 53 inventory, writes a new plan file,
prints each proposed deletion and the file's SHA-256 hash, and refuses to replace
an existing plan. It preserves the complete Route 53 record set, including
aliases and routing fields. For an offline rehearsal against the zone export from
Section 3, use `make dns-plan DNS_ZONE_EXPORT=/secure/path/route53-before-YYYY-MM-DD.json`
with a **new** plan path; the resulting plan still requires a fresh live-record
comparison before any application.

The independent reviewer must compare the plan with the protected zone export,
roster, and intended student-name list. Confirm every proposed record belongs to
a former student, all infrastructure records are absent, all record types and
routing fields are represented, and the account and hosted-zone IDs are correct.
Keep the exact plan file, SHA-256 hash, reviewer, and approval with the rollover
record. Any uncertainty stops the procedure; correct the list and make a new
plan rather than editing an approved file.

## 6. Approve the exact plan

Run the repository's `make check-all` and the local DNS planner tests on the
released revision. Compare the plan SHA-256 printed by `make dns-plan` with an
independent hash of the saved file. Record explicit approval for that hash, the
AWS account, hosted zone, revision, and maintenance window. A code review or a
successful dry run alone does not authorize production deletion.

## 7. Apply the approved plan

Only the designated operator should run this after Section 6 is complete:

```console
$ AWS_PROFILE=fas make dns-apply DNS_SHA256=APPROVED_PLAN_SHA256
```

The apply command rejects a changed plan, mismatched AWS account or hosted zone,
and live student records that differ from the approved plan. It submits bounded
Route 53 batches, prints each change ID, and waits for `INSYNC` before proceeding.
A failure after one submitted batch can leave a partial cleanup; preserve the
printed IDs and current zone inventory, then make a new plan for the remaining
records. Do not simply replay the old plan.

## 8. Verify DNS cleanup

1. Export the full zone again as `route53-after-YYYY-MM-DD.json`.
2. Confirm no reviewed student record remains.
3. Confirm every preserved record is identical to its pre-change representation.
4. Resolve a sample of former student names and all infrastructure names through
   at least two independent recursive DNS resolvers.
5. Confirm the website, staging site, leaderboard, authentication callback, email,
   and grading workflows still use resolvable infrastructure names.
6. Attach the before/after inventories, approved change hash, Route 53 change IDs,
   `INSYNC` evidence, and verification results to the protected rollover record.

If an infrastructure record was removed, stop immediately. Recreate it from the
complete pre-change Route 53 export and wait for the corrective change to become
`INSYNC`. Do not improvise values from memory.

## 9. Reset course data separately

DNS cleanup does not delete DynamoDB, S3, SQS, Lambda, or session data. Obtain a
separate explicit approval naming the exact tables and operation before removing
course records. Recheck the archive, restore proof, final reports, AWS identity,
region, and table names immediately before that operation.

Do not delete CloudFormation-managed tables in a way that creates stack drift or
bypasses deletion protection. After the approved reset, verify the tables are
empty, recreate only intentional Spring 2027 seed/admin records, and confirm that
no paused writer repopulated old data.

## 10. Close the maintenance window

1. Re-enable writers in a controlled order.
2. Test a new student registration, generated DNS names, dashboard login, grading,
   email, leaderboard, and admin reports end to end.
3. Watch Lambda errors, queue depths, Route 53 changes, and DynamoDB item counts.
4. Preserve a post-change configuration snapshot and schedule a later restore
   drill and archive-access review.
5. Close the rollover checklist only after every remaining item has an owner and a
   linked issue or recorded completion evidence.

## Appendix A. Enable public DNS query logging for the next course

Enable logging before students begin using their hostnames. Public hosted-zone
query logging is not retroactive. It records queries that recursive resolvers send
to Route 53, not every query made by every client; resolver caching means the data
is evidence of observed DNS activity, not a complete student-usage history.

Route 53 public hosted-zone logs must first go to a CloudWatch Logs log group in
`us-east-1` in the same AWS account as the hosted zone. The following zsh commands
configure `/aws/route53/csci-e-11.org` with 180-day retention. Run them one at a
time, inspect every derived value, and stop if the account or hosted zone is wrong.

```console
$ export E11_AWS_PROFILE=fas
$ export E11_ZONE_NAME=csci-e-11.org.
$ export E11_LOG_REGION=us-east-1
$ export E11_LOG_GROUP=/aws/route53/csci-e-11.org
$ E11_ACCOUNT_ID="$(aws sts get-caller-identity --profile "$E11_AWS_PROFILE" --query Account --output text)"
$ E11_ZONE_PATH="$(aws route53 list-hosted-zones-by-name --profile "$E11_AWS_PROFILE" --dns-name "$E11_ZONE_NAME" --query "HostedZones[?Name=='${E11_ZONE_NAME}'] | [0].Id" --output text)"
$ E11_ZONE_ID="${E11_ZONE_PATH##*/}"
$ E11_LOG_GROUP_ARN="arn:aws:logs:${E11_LOG_REGION}:${E11_ACCOUNT_ID}:log-group:${E11_LOG_GROUP}"
$ printf 'account=%s zone=%s log-group=%s\n' "$E11_ACCOUNT_ID" "$E11_ZONE_ID" "$E11_LOG_GROUP_ARN"
```

Check for an existing logging configuration and log group before creating either:

```console
$ aws route53 list-query-logging-configs --profile "$E11_AWS_PROFILE" --hosted-zone-id "$E11_ZONE_ID"
$ aws logs describe-log-groups --profile "$E11_AWS_PROFILE" --region "$E11_LOG_REGION" --log-group-name-prefix "$E11_LOG_GROUP" --query "logGroups[?logGroupName=='${E11_LOG_GROUP}'].[logGroupName,arn,retentionInDays]"
```

A public hosted zone can have only one query-logging configuration. If one already
exists, do not run `create-query-logging-config`; identify its log group and apply
the retention policy to that group. If the exact log group does not exist, create
it:

```console
$ aws logs create-log-group --profile "$E11_AWS_PROFILE" --region "$E11_LOG_REGION" --log-group-name "$E11_LOG_GROUP" --tags Course=E11,Purpose=DNSQueryLogging
$ aws logs put-retention-policy --profile "$E11_AWS_PROFILE" --region "$E11_LOG_REGION" --log-group-name "$E11_LOG_GROUP" --retention-in-days 180
```

Grant Route 53 permission to create streams and publish events. The source-account
and source-ARN conditions restrict the permission to this account and hosted zone:

```console
$ E11_LOG_POLICY="{\"Version\":\"2012-10-17\",\"Statement\":[{\"Sid\":\"Route53LogsToCloudWatchLogs\",\"Effect\":\"Allow\",\"Principal\":{\"Service\":\"route53.amazonaws.com\"},\"Action\":[\"logs:CreateLogStream\",\"logs:PutLogEvents\"],\"Resource\":\"${E11_LOG_GROUP_ARN}:*\",\"Condition\":{\"ArnLike\":{\"aws:SourceArn\":\"arn:aws:route53:::hostedzone/${E11_ZONE_ID}\"},\"StringEquals\":{\"aws:SourceAccount\":\"${E11_ACCOUNT_ID}\"}}}]}"
$ aws logs put-resource-policy --profile "$E11_AWS_PROFILE" --region "$E11_LOG_REGION" --policy-name Route53QueryLoggingE11 --policy-document "$E11_LOG_POLICY"
```

Create the Route 53 logging configuration only if the earlier list command showed
none:

```console
$ aws route53 create-query-logging-config --profile "$E11_AWS_PROFILE" --hosted-zone-id "$E11_ZONE_ID" --cloud-watch-logs-log-group-arn "$E11_LOG_GROUP_ARN"
```

Verify both the association and retention setting:

```console
$ aws route53 list-query-logging-configs --profile "$E11_AWS_PROFILE" --hosted-zone-id "$E11_ZONE_ID"
$ aws logs describe-log-groups --profile "$E11_AWS_PROFILE" --region "$E11_LOG_REGION" --log-group-name-prefix "$E11_LOG_GROUP" --query "logGroups[?logGroupName=='${E11_LOG_GROUP}'].[logGroupName,retentionInDays,storedBytes]"
```

Submit a unique test lookup, wait several minutes, and inspect recent events:

```console
$ dig unique-logging-test-YYYYMMDDHHMMSS.csci-e-11.org A
$ aws logs tail "$E11_LOG_GROUP" --profile "$E11_AWS_PROFILE" --region "$E11_LOG_REGION" --since 10m
```

CloudWatch supports `180` days, not a calendar-month retention expression. Events
older than that are expired by CloudWatch. The logging configuration and retention
policy are separate resources; creating one does not set the other.

### Storage choices

For authoritative queries to the public `csci-e-11.org` zone:

- **CloudWatch Logs only, retained for 180 days:** the simplest choice and the best
  option for Logs Insights, near-real-time searches, metrics, and alarms.
- **CloudWatch Logs plus S3 archive:** export historical ranges to an encrypted S3
  bucket, or use a CloudWatch Logs subscription and Firehose for continuous
  delivery. Apply an independent 180-day S3 lifecycle rule if S3 must obey the same
  retention. S3 is generally better for economical archives and Athena queries.
- **CloudWatch Logs plus Firehose/external analytics:** use a subscription filter
  when logs must be continuously delivered to S3, OpenSearch, or another supported
  destination. This adds delivery, IAM, failure-handling, and cost configuration.
- **Local copies:** export from CloudWatch or S3 and download an encrypted copy.
  This is not a native Route 53 destination and should not be the only retained
  copy.

Route 53 Resolver query logging is different: it records DNS activity originating
from selected VPCs and can deliver directly to CloudWatch Logs, S3, or Firehose. It
does not replace public hosted-zone logging for internet queries to student names.

AWS references:

- [Public DNS query logging](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/query-logs.html)
- [CreateQueryLoggingConfig CLI](https://docs.aws.amazon.com/cli/latest/reference/route53/create-query-logging-config.html)
- [CloudWatch Logs retention policy CLI](https://docs.aws.amazon.com/cli/latest/reference/logs/put-retention-policy.html)
- [Exporting CloudWatch Logs to S3](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/S3Export.html)
- [Resolver query-log destinations](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver-query-logs-choosing-target-resource.html)
