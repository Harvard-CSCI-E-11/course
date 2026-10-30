# Exercise the standalone DNS logger without real AWS resources or course data.
# Botocore validates requests and supplies AWS replies at the external boundary;
# Route 53 and CloudWatch Logs have no local services available for these tests.
# Setup tests enforce retention, destination checks, policy scope, and safe reuse.
# Query tests cover selection, result conversion, failure handling, and CSV output.
# Public Make targets are exercised with invalid input before credentials are used.
# DNS verification stubs only the external lookup and unique probe identifier.
"""Configuration and reporting behavior for public DNS query logging."""

import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

import boto3
import pytest
from botocore.stub import ANY, Stubber

from e11.e11admin import dns_logging as dl

ZONE = "ZEXAMPLE"
ACCOUNT = "123456789012"
DOMAIN = "csci-e-11.org"
GROUP = "/aws/route53/" + DOMAIN
TARGET = dl.Target(account_id=ACCOUNT, zone_id=ZONE, domain=DOMAIN, log_group=GROUP,
                   name_servers=["ns.example.org"])
QUERY_CONFIG = "QueryLoggingConfig"
HOSTED_ZONE_ID = "HostedZoneId"
ID = "Id"
TOKEN = "query-identifier"
LOCATION = "Location"
START_TIME = "startTime"
END_TIME = "endTime"
QUERY_STRING = "queryString"
LIMIT = "limit"
FILTER_PATTERN = "filterPattern"
NOW = datetime(2026, 10, 28, 18, tzinfo=timezone.utc)
SINCE = NOW - timedelta(days=30)


@pytest.fixture
def service():
    session = boto3.Session(aws_access_key_id="test", aws_secret_access_key="test", region_name=dl.REGION)
    return dl.DnsLogging(TARGET, session.client("route53"), session.client("logs"))


def _config(stub, enabled=True, arn=None):
    stub.add_response("list_query_logging_configs", {
        dl.QUERY_CONFIGS: [{ID: "config-id", HOSTED_ZONE_ID: ZONE,
                           dl.LOG_GROUP_ARN: arn or TARGET.log_arn}] if enabled else [],
    }, {HOSTED_ZONE_ID: ZONE})


def _group(stub, *, exists=True, log_class="STANDARD", retention=180):
    group = {dl.LOG_GROUP_NAME: GROUP, dl.LOG_GROUP_CLASS: log_class, dl.STORED_BYTES: 1234}
    if retention is not None:
        group[dl.RETENTION] = retention
    stub.add_response("describe_log_groups", {dl.LOG_GROUPS: [group] if exists else []},
                      {"logGroupNamePrefix": GROUP})


def _policy():
    # Expected scope is stated independently to catch broader access accidentally granted.
    return {dl.VERSION: "2012-10-17", dl.STATEMENT: [{
        dl.SID: "E11DnsQueryLogging", dl.EFFECT: "Allow",
        dl.PRINCIPAL: {dl.SERVICE: "route53.amazonaws.com"},
        dl.ACTION: ["logs:CreateLogStream", "logs:PutLogEvents"],
        dl.RESOURCE: TARGET.log_arn + ":*",
        dl.CONDITION: {
            dl.ARN_EQUALS: {dl.SOURCE_ARN: "arn:aws:route53:::hostedzone/" + ZONE},
            dl.STRING_EQUALS: {dl.SOURCE_ACCOUNT: ACCOUNT},
        },
    }]}


def _policies(stub, document=None):
    policies = [] if document is None else [{
        dl.POLICY_NAME: "E11Route53-" + ZONE, dl.POLICY_DOCUMENT: json.dumps(document),
    }]
    stub.add_response("describe_resource_policies", {dl.POLICIES: policies}, {})


def test_enable_creates_scoped_logging_with_standard_and_180_days(service):
    with Stubber(service.route53) as route, Stubber(service.logs) as logs:
        _config(route, False)
        _group(logs, exists=False)
        logs.add_response("create_log_group", {}, {dl.LOG_GROUP_NAME: GROUP, dl.LOG_GROUP_CLASS: "STANDARD"})
        logs.add_response("put_retention_policy", {}, {dl.LOG_GROUP_NAME: GROUP, dl.RETENTION: 180})
        _policies(logs)
        logs.add_response("put_resource_policy", {}, {
            dl.POLICY_NAME: "E11Route53-" + ZONE, dl.POLICY_DOCUMENT: json.dumps(_policy()),
        })
        route.add_response("create_query_logging_config", {
            LOCATION: "https://route53.amazonaws.com/2013-04-01/queryloggingconfig/config-id",
            QUERY_CONFIG: {ID: "config-id", HOSTED_ZONE_ID: ZONE, dl.LOG_GROUP_ARN: TARGET.log_arn},
        }, {HOSTED_ZONE_ID: ZONE, dl.LOG_GROUP_ARN: TARGET.log_arn})
        _config(route)
        _group(logs)
        status = service.enable()
        assert status.enabled and status.retention_days == 180 and status.log_class == "STANDARD"
        assert status.stored_bytes == 1234
        route.assert_no_pending_responses()
        logs.assert_no_pending_responses()


def test_enable_again_reuses_every_resource_without_writes(service):
    with Stubber(service.route53) as route, Stubber(service.logs) as logs:
        _config(route)
        _group(logs)
        _policies(logs, _policy())
        _config(route)
        _group(logs)
        assert service.enable().enabled
        route.assert_no_pending_responses()
        logs.assert_no_pending_responses()


def test_policy_update_preserves_other_statements(service):
    original = {dl.VERSION: "2012-10-17", dl.STATEMENT: [{
        dl.SID: "Unrelated", dl.EFFECT: "Allow", dl.PRINCIPAL: {dl.SERVICE: "route53.amazonaws.com"},
        dl.ACTION: "logs:PutLogEvents", dl.RESOURCE: TARGET.log_arn + ":log-stream:other",
    }]}
    expected = {**original, dl.STATEMENT: original[dl.STATEMENT] + _policy()[dl.STATEMENT]}
    with Stubber(service.logs) as logs:
        _policies(logs, original)
        logs.add_response("put_resource_policy", {}, {
            dl.POLICY_NAME: "E11Route53-" + ZONE, dl.POLICY_DOCUMENT: json.dumps(expected),
        })
        service._ensure_policy()
        logs.assert_no_pending_responses()


def test_enable_does_not_redirect_existing_logging(service):
    with Stubber(service.route53) as route, Stubber(service.logs):
        _config(route, arn=TARGET.log_arn + "-different")
        with pytest.raises(dl.LoggingError, match="different destination"):
            service.enable()


def test_enable_refuses_infrequent_access_before_any_write(service):
    with Stubber(service.route53) as route, Stubber(service.logs) as logs:
        _config(route, False)
        _group(logs, log_class="INFREQUENT_ACCESS")
        with pytest.raises(dl.LoggingError, match="not Standard"):
            service.enable()


def test_query_selection_is_exact_and_student_includes_labs():
    text = dl.query_text(TARGET, report=False, name="Alice." + DOMAIN + ".")
    assert 'filter hostZoneId = "ZEXAMPLE"' in text
    assert r"/^alice\.csci\-e\-11\.org\.?$/" in text
    text = dl.query_text(TARGET, report=True, student="alice")
    assert r"/^alice(-lab[0-9]+)?\.csci\-e\-11\.org\.?$/" in text
    assert "NXDOMAIN" in text and "latest(queryTimestamp)" in text
    assert 'fields rtrim(tolower(queryName), ".") as hostname' in text
    assert "by hostname" in text
    for name in ["bad/name", 'bad"name', "outside.example.org"]:
        with pytest.raises(dl.LoggingError):
            dl.query_text(TARGET, report=False, name=name)


def _start(logs, *, report=False, **kwargs):
    text = dl.query_text(TARGET, report=report, limit=100, **kwargs)
    logs.add_response("start_query", {dl.QUERY_ID: TOKEN}, {
        dl.LOG_GROUP_NAME: GROUP, START_TIME: int(SINCE.timestamp()),
        END_TIME: int(NOW.timestamp()), QUERY_STRING: text, LIMIT: 100,
    })


def test_report_converts_results_and_produces_csv(service):
    with Stubber(service.route53) as route, Stubber(service.logs) as logs:
        _config(route)
        _start(logs, report=True, student="alice")
        logs.add_response("get_query_results", {
            dl.STATUS: "Complete", dl.RESULTS: [[
                {dl.FIELD: "hostname", dl.VALUE: "alice." + DOMAIN},
                {dl.FIELD: "last_seen", dl.VALUE: NOW.isoformat()},
                {dl.FIELD: "queries", dl.VALUE: "12"},
                {dl.FIELD: "nxdomain", dl.VALUE: "3"},
            ]], dl.STATISTICS: {dl.BYTES_SCANNED: 1024.0},
        }, {dl.QUERY_ID: TOKEN})
        output = service.query(report=True, since=SINCE, until=NOW, student="alice")
        assert output.bytes_scanned == 1024
        assert output.rows == [dl.HostnameReport(hostname="alice." + DOMAIN, last_seen=NOW,
                                                queries=12, nxdomain=3)]
        csv = dl.render(list(output.rows), "csv", dl.HostnameReport)
        assert csv.startswith("hostname,last_seen,queries,nxdomain\r\n")
        assert "alice." + DOMAIN in csv and csv.endswith(",12,3")
        logs.assert_no_pending_responses()


def test_events_show_individual_queries(service):
    row = dl.QueryEvent(timestamp=NOW, hostname="alice." + DOMAIN, query_type="AAAA",
                        response_code="NOERROR", resolver_ip="192.0.2.1")
    with Stubber(service.route53) as route, Stubber(service.logs) as logs:
        _config(route)
        _start(logs, name="alice")
        logs.add_response("get_query_results", {
            dl.STATUS: "Complete", dl.RESULTS: [[{dl.FIELD: key, dl.VALUE: value}
                                                for key, value in row.model_dump(mode="json").items()]],
        }, {dl.QUERY_ID: TOKEN})
        output = service.query(report=False, since=SINCE, until=NOW, name="alice")
        assert output.rows == [row]
        assert json.loads(dl.render(list(output.rows), "json", dl.QueryEvent))[0]["resolver_ip"] == "192.0.2.1"


def test_timed_out_query_is_stopped(service):
    with Stubber(service.route53) as route, Stubber(service.logs) as logs:
        _config(route)
        _start(logs)
        logs.add_response("get_query_results", {dl.STATUS: "Running", dl.RESULTS: []}, {dl.QUERY_ID: TOKEN})
        logs.add_response("stop_query", {"success": True}, {dl.QUERY_ID: TOKEN})
        with pytest.raises(dl.LoggingError, match="timed out and was stopped"):
            service.query(report=False, since=SINCE, until=NOW, timeout=0)
        logs.assert_no_pending_responses()


def test_failed_query_does_not_return_partial_results(service):
    with Stubber(service.route53) as route, Stubber(service.logs) as logs:
        _config(route)
        _start(logs)
        logs.add_response("get_query_results", {dl.STATUS: "Failed", dl.RESULTS: []}, {dl.QUERY_ID: TOKEN})
        with pytest.raises(dl.LoggingError, match="Failed"):
            service.query(report=False, since=SINCE, until=NOW)


@pytest.mark.parametrize("observed", [True, False])
def test_verification_requires_the_actual_probe_event(service, monkeypatch, observed):
    monkeypatch.setattr(dl, "uuid4", lambda: UUID(int=0))
    probe = "e11-log-check-" + "0" * 32 + "." + DOMAIN

    def lookup(server, name, query_type, lifetime):
        assert (server, name, query_type, lifetime) == ("ns.example.org", probe, "A", 10)
        raise dl.dns.resolver.NXDOMAIN

    monkeypatch.setattr(dl.dns.resolver, "resolve_at", lookup)
    with Stubber(service.route53) as route, Stubber(service.logs) as logs:
        _config(route)
        _group(logs)
        logs.add_response("filter_log_events", {dl.EVENTS: [{
            dl.MESSAGE: f"1.0 2026-10-28T18:00:00Z {ZONE} {probe} A NXDOMAIN UDP IAD1 192.0.2.1 -",
        }] if observed else []}, {
            dl.LOG_GROUP_NAME: GROUP, START_TIME: ANY, FILTER_PATTERN: f'"{probe}"',
        })
        if observed:
            assert "Verified: observed DNS query" in service.verify(timeout=0)
        else:
            with pytest.raises(dl.LoggingError, match="not observed"):
                service.verify(timeout=0)


def test_verification_retries_transient_dns_failure_on_another_authority(service, monkeypatch):
    monkeypatch.setattr(dl, "uuid4", lambda: UUID(int=0))
    service.target.name_servers = ["ns.example.org", "ns2.example.org"]
    probe = "e11-log-check-" + "0" * 32 + "." + DOMAIN
    servers = []

    def lookup(server, _name, _query_type, lifetime):
        assert lifetime == 10
        servers.append(server)
        if len(servers) == 1:
            raise dl.dns.exception.Timeout
        raise dl.dns.resolver.NXDOMAIN

    monkeypatch.setattr(dl.dns.resolver, "resolve_at", lookup)
    with Stubber(service.route53) as route, Stubber(service.logs) as logs:
        _config(route)
        _group(logs)
        for events in [[], [{dl.MESSAGE: f"1.0 2026-10-28T18:00:00Z {ZONE} {probe} A NXDOMAIN UDP IAD1 192.0.2.1 -"}]]:
            logs.add_response("filter_log_events", {dl.EVENTS: events}, {
                dl.LOG_GROUP_NAME: GROUP, START_TIME: ANY, FILTER_PATTERN: f'"{probe}"',
            })
        assert "Verified: observed DNS query" in service.verify(timeout=20)
    assert servers == ["ns.example.org", "ns2.example.org"]


def test_csv_escapes_formula_names_without_changing_json():
    row = dl.QueryEvent(timestamp=NOW, hostname="=1+2.csci-e-11.org", query_type="A",
                        response_code="NXDOMAIN", resolver_ip="192.0.2.1")
    import csv
    import io
    rendered = list(csv.DictReader(io.StringIO(dl.render([row], "csv", dl.QueryEvent))))
    assert rendered[0]["hostname"] == "'" + row.hostname
    assert json.loads(dl.render([row], "json", dl.QueryEvent))[0]["hostname"] == row.hostname


@pytest.mark.parametrize("root", [True, False])
def test_make_report_rejects_bad_time_before_using_credentials(root):
    project = Path(__file__).resolve().parents[1]
    result = subprocess.run([
        "make", "--silent", "--no-print-directory", "dns-log-report",
        "DNS_ZONE_ID=" + ZONE, "DNS_LOG_SINCE=invalid",
    ], cwd=project.parents[1] if root else project, capture_output=True, text=True, check=False)
    assert result.returncode != 0
    assert "--since must be a positive duration" in result.stderr
    assert result.stdout == ""  # Machine-readable exports must not contain Make commands.
