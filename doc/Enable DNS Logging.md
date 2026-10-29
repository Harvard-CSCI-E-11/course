# DNS query logging

The standalone `etc/e11-cli/e11/e11admin/dns_logging.py` script configures public
Route 53 query logging and produces terminal reports. Logs use **CloudWatch
Standard in us-east-1 with 180-day retention**. S3 export is not implemented.

Run the following from the Git root or `etc/e11-cli`, using existing AWS
credentials. No SSO login is performed. Set `DNS_ZONE_ID` to the public hosted-zone
ID already used for DNS maintenance; `DNS_ACCOUNT_ID` optionally checks the
expected account. `AWS_PROFILE=fas` selects the existing staff credentials.

```console
export AWS_PROFILE=fas
export DNS_ZONE_ID="$HOSTED_ZONE_ID"
make dns-logging-enable
make dns-logging-status
make dns-logs DNS_LOG_STUDENT=alice DNS_LOG_SINCE=24h
make dns-log-report DNS_LOG_SINCE=30d
make dns-log-report DNS_LOG_STUDENT=alice DNS_LOG_FORMAT=csv > alice-dns.csv
```

`DNS_LOG_STUDENT=alice` selects `alice.csci-e-11.org` and its
`alice-labN.csci-e-11.org` names. `DNS_LOG_NAME` selects one exact hostname instead;
it accepts a short name or a fully qualified name.

`dns-logging-enable` creates or reuses the log group and query-logging
configuration, sets 180-day retention, and grants Route 53 the required log-write
permissions. The script's policy is scoped to the account, hosted zone, and log
group; other policy statements are preserved. Existing logging destinations are
reused unless an explicit conflicting `DNS_LOG_GROUP` is supplied, in which case
setup stops. Existing non-Standard groups are rejected because their class cannot
be changed. Reducing an existing group's retention to 180 days expires older data.

Setup queries an authoritative Route 53 server directly with a unique hostname,
retrying while it waits up to three minutes for the log event. Recursive DNS
caching cannot hide the probe. The expected NXDOMAIN response is itself logged;
no DNS record is created.
A configuration table alone establishes configuration, while `Verified: observed
DNS query ...` establishes actual delivery. If delivery takes longer, the
configuration remains enabled; retry with `make dns-logging-verify`.

The operator needs Route 53 zone/configuration read access and permission to
create query-logging configurations; CloudWatch Logs group/policy read and write
access, retention-policy write access, `FilterLogEvents`, and Logs Insights
`StartQuery`, `GetQueryResults`, and `StopQuery` access. Normal AWS credential
resolution and `GetCallerIdentity` establish the current account.
The script reuses one AWS session throughout each command. If a profile uses
1Password through `credential_process`, separate commands can request another
1Password authorization; AWS does not share a cache for these process credentials.
The script does not write credentials to disk.

The read-only commands provide:

- `dns-logging-status`: enabled state, AWS account/zone, log group, class,
  retention, and stored bytes.
- `dns-logs`: individual queries with UTC time, hostname, record type, response
  code, and resolver address. Defaults to the latest 100 events within one hour.
- `dns-log-report`: hostname, most recent observed query, query count, and
  NXDOMAIN count. Defaults to the preceding 30 days and at most 10,000 hostnames.

Hostname summaries normalize case and trailing dots before grouping. CSV exports
prefix spreadsheet formula-like cells with an apostrophe; JSON keeps raw values.
Verification retries transient DNS failures and rotates through the zone's
authoritative name servers.

Reports execute in CloudWatch Logs Insights and print the scanned data volume to
stderr. The selected period is explicit in the options; a row-limit warning means
results may be incomplete. No observed query is not proof of inactivity. A
student's hostname identifies the queried name, not the person making the lookup.
Resolver caching hides some lookups, and bots can query student names too. This
is not a browser-access or server-login history. Logging is not retroactive.

| Variable | Purpose/default |
|----------|-----------------|
| `AWS_PROFILE` | Existing AWS credential profile, e.g. `fas`; no login is initiated |
| `DNS_PROFILE` | Optional profile override |
| `DNS_ZONE_ID` | Required public hosted-zone ID; accepts `/hostedzone/ID` |
| `DNS_ACCOUNT_ID` | Optional expected account ID; mismatch stops all operations |
| `DNS_DOMAIN` | Expected zone name; defaults to `csci-e-11.org` |
| `DNS_LOG_GROUP` | Existing destination, or `/aws/route53/DOMAIN` for new logging |
| `DNS_LOG_SINCE` | Positive lookback such as `30m`, `24h`, `30d`; defaults above |
| `DNS_LOG_UNTIL` | ISO 8601 end time with time zone; defaults to now |
| `DNS_LOG_NAME` | One hostname; mutually exclusive with `DNS_LOG_STUDENT` |
| `DNS_LOG_STUDENT` | Student hostname stem, including its `-labN` names |
| `DNS_LOG_LIMIT` | Maximum rows, 1–10,000 |
| `DNS_LOG_FORMAT` | `table` (default), `csv`, or `json` |

Retention is based on event age. AWS typically removes expired events within
another 72 hours. Disabling logging would not erase already retained logs.

For 80 students, an illustrative 100 logged queries per student per day at
500 bytes each produces about 0.12 GB per 30-day month. Using N. Virginia list
rates of approximately $0.50/GB ingested, $0.03/GB-month stored, and $0.005/GB
scanned, a conservative uncompressed six-month retention estimate plus four
full-history scans per month is **about $0.10/month**, before free allowances.
At 1,000 queries per student per day, it is about $1/month. This is an estimate,
not a measured bill: traffic to all names, including infrastructure and bots, is
logged. Storage is billed after compression; other account workloads can consume
shared free allowances. No paid dashboard, custom metrics, or recurring jobs are
created. Ordinary existing Route 53 DNS-query charges are separate.

Run `make dns-logging-test` and `make dns-logging-lint` for local validation.
Contract tests stub the external AWS/DNS boundaries; `dns-logging-verify` checks
actual delivery in AWS.

References (pricing checked October 28, 2026):

- [Route 53 public DNS query logging](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/query-logs.html)
- [CloudWatch pricing](https://aws.amazon.com/cloudwatch/pricing/)
- [CloudWatch Logs Insights query pricing](https://aws.amazon.com/blogs/mt/control-investigation-costs-before-they-start-with-aws-devops-agent/)
- [CloudWatch retention](https://docs.aws.amazon.com/AmazonCloudWatchLogs/latest/APIReference/API_PutRetentionPolicy.html)
