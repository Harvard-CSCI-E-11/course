# Verify the keep-list workflow through its public Make targets and core logic.
# Fixtures use complete Route 53 record sets, including aliases and routing data.
# Offline command tests prove that planning never needs AWS and saves its output.
# Keep-list and live-record drift must stop deletion before any write is sent.
# Botocore stubs cover the AWS write/wait boundary because live deletion is not
# authorized in tests and Route 53 has no local equivalent used by this project.
"""Behavioral tests for export-based DNS planning and saved-plan deletion."""

import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import boto3
import pytest
from botocore.stub import Stubber

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[1]
SCRIPT = PROJECT / "e11/e11admin/end-of-term/cleanup_dns.py"
SPEC = importlib.util.spec_from_file_location("cleanup_dns", SCRIPT)
assert SPEC and SPEC.loader
cleanup_dns = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = cleanup_dns
SPEC.loader.exec_module(cleanup_dns)

DOMAIN = "csci-e-11.org"
ZONE_ID = "ZEXAMPLE"
ACCOUNT_ID = "123456789012"
NAME = cleanup_dns.NAME
TYPE = cleanup_dns.TYPE
TTL = cleanup_dns.TTL
RECORDS = cleanup_dns.RECORDS
VALUE = cleanup_dns.VALUE
ALIAS = cleanup_dns.ALIAS
ACTION = cleanup_dns.ACTION
RECORD_SET = cleanup_dns.RESOURCE_RECORD_SET
RECORD_SETS = cleanup_dns.RESOURCE_RECORD_SETS
IDENTIFIER = cleanup_dns.SET_IDENTIFIER
CHANGE_INFO = cleanup_dns.CHANGE_INFO
CHANGES = cleanup_dns.CHANGES
ID = cleanup_dns.ID
DNS_NAME = "DNSName"
HOSTED_ZONE_ID = "HostedZoneId"
EVALUATE_TARGET_HEALTH = "EvaluateTargetHealth"
WEIGHT = "Weight"
STATUS = "Status"
SUBMITTED_AT = "SubmittedAt"
MAX_ITEMS = "MaxItems"
PATTERNS = [DOMAIN + "."]


def _records():
    return [
        {NAME: DOMAIN + ".", TYPE: "SOA", TTL: 900,
         RECORDS: [{VALUE: "ns.example. host.example. 1 2 3 4 5"}]},
        {NAME: "student." + DOMAIN + ".", TYPE: "A", IDENTIFIER: "east",
         WEIGHT: 50, TTL: 60, RECORDS: [{VALUE: "192.0.2.1"}]},
        {NAME: "student." + DOMAIN + ".", TYPE: "A", IDENTIFIER: "west",
         WEIGHT: 50, ALIAS: {HOSTED_ZONE_ID: "ZALIAS", DNS_NAME: "target.example.",
                           EVALUATE_TARGET_HEALTH: False}},
        {NAME: "other." + DOMAIN + ".", TYPE: "AAAA", TTL: 60,
         RECORDS: [{VALUE: "2001:db8::1"}]},
    ]


def _plan(records=None, patterns=None):
    return cleanup_dns.build_plan(_records() if records is None else records,
                                  PATTERNS if patterns is None else patterns,
                                  DOMAIN, ZONE_ID, ACCOUNT_ID)


def _make(tmp_path, target, *, root=False, **variables):
    settings = {
        "DNS_DOMAIN": DOMAIN, "DNS_ZONE_ID": "/hostedzone/" + ZONE_ID,
        "DNS_ACCOUNT_ID": ACCOUNT_ID, "DDB_DIR": tmp_path / "backup",
        "DNS_KEEP": tmp_path / "keep.txt",
    }
    settings.update(variables)
    return subprocess.run(
        ["make", "--silent", "--no-print-directory", target,
         *(f"{key}={value}" for key, value in settings.items())],
        cwd=ROOT if root else PROJECT, check=False, capture_output=True, text=True,
    )


def _inputs(tmp_path, records=None):
    export = tmp_path / "backup-route53.json"
    export.write_text(json.dumps({RECORD_SETS: _records() if records is None else records}),
                      encoding="utf-8")
    keep = tmp_path / "keep.txt"
    keep.write_text(DOMAIN + "\n", encoding="utf-8")
    return export, keep, Path(str(export) + ".delete-plan.json")


def test_keep_list_globs_and_actual_infrastructure(tmp_path):
    patterns = cleanup_dns.keep_patterns(PROJECT / "dns-keep.txt", DOMAIN)
    for name in [DOMAIN, "STAGE." + DOMAIN, "api.stage." + DOMAIN,
                 "leaderboard." + DOMAIN, "grader." + DOMAIN,
                 "autodiscover." + DOMAIN, "_token.leaderboard." + DOMAIN,
                 "_token.grader." + DOMAIN, "_token.stage." + DOMAIN,
                 "_dmarc." + DOMAIN, "key._domainkey." + DOMAIN]:
        assert cleanup_dns._kept(name, patterns), name
    assert not cleanup_dns._kept("simsong." + DOMAIN, patterns)
    assert not cleanup_dns._kept("student." + DOMAIN, patterns)
    keep = tmp_path / "keep.txt"
    keep.write_text(f"# comment\n\n  {DOMAIN.upper()}  \n user?.{DOMAIN}\n lab[12].{DOMAIN}.\n")
    patterns = cleanup_dns.keep_patterns(keep, DOMAIN)
    assert cleanup_dns._kept("user1." + DOMAIN, patterns)
    assert cleanup_dns._kept("lab2." + DOMAIN, patterns)
    assert not cleanup_dns._kept("lab3." + DOMAIN, patterns)


def test_plan_selects_every_unkept_record_and_preserves_exact_fields():
    plan = _plan()
    assert [change[RECORD_SET] for change in plan.changes] == [_records()[3], *_records()[1:3]]
    assert all(change[ACTION] == "DELETE" for change in plan.changes)
    assert len(cleanup_dns.batches(plan.changes)) == 1
    assert not _plan(patterns=["*." + DOMAIN + ".", *PATTERNS]).changes
    delegation = {NAME: "delegated." + DOMAIN + ".", TYPE: "NS", TTL: 60,
                  RECORDS: [{VALUE: "ns.example."}]}
    assert _plan([delegation]).changes[0][RECORD_SET] == delegation


def test_plan_rejects_outside_duplicate_and_traffic_policy_records(tmp_path):
    with pytest.raises(cleanup_dns.CleanupError, match="outside"):
        _plan([{**_records()[1], NAME: "unrelated.example."}])
    traffic_policy = _records()
    traffic_policy[1][cleanup_dns.TRAFFIC_POLICY_INSTANCE_ID] = "example"
    with pytest.raises(cleanup_dns.CleanupError, match="separate handling"):
        _plan(traffic_policy)
    with pytest.raises(cleanup_dns.CleanupError, match="duplicate"):
        _plan([*_records(), _records()[1]])
    keep = tmp_path / "keep.txt"
    keep.write_text("# empty\n")
    with pytest.raises(cleanup_dns.CleanupError, match="apex"):
        cleanup_dns.keep_patterns(keep, DOMAIN)
    keep.write_text(f"{DOMAIN}\n*.unrelated.example\n")
    with pytest.raises(cleanup_dns.CleanupError, match="belong"):
        cleanup_dns.keep_patterns(keep, DOMAIN)


def test_batching_obeys_element_and_character_limits():
    change = {ACTION: "DELETE", RECORD_SET: {
        NAME: "student." + DOMAIN + ".", TYPE: "TXT", TTL: 60,
        RECORDS: [{VALUE: "x"}],
    }}
    assert [len(batch) for batch in cleanup_dns.batches([change] * 1001)] == [1000, 1]
    many_values = {ACTION: "DELETE", RECORD_SET: {
        **change[RECORD_SET], RECORDS: [{VALUE: "x"}] * 600,
    }}
    assert [len(batch) for batch in cleanup_dns.batches([many_values] * 2)] == [1, 1]
    long = {ACTION: "DELETE", RECORD_SET: {
        **change[RECORD_SET], RECORDS: [{VALUE: "x" * 20000}],
    }}
    assert [len(batch) for batch in cleanup_dns.batches([long, long])] == [1, 1]
    too_long = {ACTION: "DELETE", RECORD_SET: {
        **change[RECORD_SET], RECORDS: [{VALUE: "x" * 32001}],
    }}
    with pytest.raises(cleanup_dns.CleanupError, match="batch limits"):
        cleanup_dns.batches([too_long])


@pytest.mark.parametrize("root", [False, True])
def test_make_plans_from_export_and_detects_keep_list_changes(tmp_path, root):
    _, keep, plan_path = _inputs(tmp_path)
    planned = _make(tmp_path, "dns-plan", root=root)
    assert planned.returncode == 0, planned.stderr
    assert "record sets to delete: 3" in planned.stdout
    assert "record sets to keep: 1" in planned.stdout
    assert [line for line in planned.stdout.splitlines()
            if line.startswith(("DELETE ", "WILL DELETE "))] == [
        f"WILL DELETE other.{DOMAIN}. AAAA",
        f"WILL DELETE student.{DOMAIN}. A east",
        f"WILL DELETE student.{DOMAIN}. A west",
    ]
    plan = cleanup_dns._read_plan(plan_path, PATTERNS)
    assert plan.zone_id == ZONE_ID
    assert plan == _plan()
    assert _make(tmp_path, "dns-plan", root=root).returncode == 0  # Replanning replaces it.
    keep.write_text(f"{DOMAIN}\nstudent.{DOMAIN}\n")
    rejected = _make(tmp_path, "dns-delete", root=root)
    assert rejected.returncode != 0
    assert "keep-list changed" in rejected.stderr
    # After replanning, a metadata mismatch is rejected before any AWS calls.
    assert _make(tmp_path, "dns-plan", root=root).returncode == 0
    rejected = _make(tmp_path, "dns-delete", root=root, DNS_ACCOUNT_ID="999999999999")
    assert rejected.returncode != 0
    assert "does not match" in rejected.stderr


def test_make_empty_plan_and_delete_are_offline_noops(tmp_path):
    _, keep, _ = _inputs(tmp_path)
    keep.write_text(f"{DOMAIN}\n*.{DOMAIN}\n")
    assert _make(tmp_path, "dns-plan", root=True).returncode == 0
    deleted = _make(tmp_path, "dns-delete", root=True)
    assert deleted.returncode == 0, deleted.stderr
    assert "No record sets to delete" in deleted.stdout


@pytest.mark.parametrize("key,value", [(cleanup_dns.IS_TRUNCATED, True),
                                       (cleanup_dns.NEXT_TOKEN, "more-records")])
def test_rejects_truncated_export(tmp_path, key, value):
    export, _, plan_path = _inputs(tmp_path)
    export.write_text(json.dumps({RECORD_SETS: _records(), key: value}))
    rejected = _make(tmp_path, "dns-plan")
    assert rejected.returncode != 0
    assert "truncated" in rejected.stderr
    assert not plan_path.exists()


def test_plan_path_cannot_overwrite_inputs(tmp_path):
    export, keep, _ = _inputs(tmp_path)
    for path in [export, keep]:
        original = path.read_bytes()
        rejected = _make(tmp_path, "dns-plan", DNS_PLAN=path)
        assert rejected.returncode != 0
        assert "must not overwrite" in rejected.stderr
        assert path.read_bytes() == original


def test_read_plan_rejects_nondelete_and_kept_records(tmp_path):
    path = tmp_path / "plan.json"
    plan = _plan()
    plan.changes[0][ACTION] = "UPSERT"
    path.write_text(plan.model_dump_json())
    with pytest.raises(cleanup_dns.CleanupError, match="non-delete"):
        cleanup_dns._read_plan(path, PATTERNS)
    plan = _plan()
    plan.changes.append({ACTION: "DELETE", RECORD_SET: _records()[0]})
    path.write_text(plan.model_dump_json())
    with pytest.raises(cleanup_dns.CleanupError, match="outside deletable"):
        cleanup_dns._read_plan(path, PATTERNS)


def _client():
    return boto3.client("route53", region_name="us-east-1",
                        aws_access_key_id="test", aws_secret_access_key="test")


def _inventory(stub, records):
    stub.add_response("list_resource_record_sets", {
        RECORD_SETS: records, cleanup_dns.IS_TRUNCATED: False, MAX_ITEMS: "100",
    }, {HOSTED_ZONE_ID: ZONE_ID})


@pytest.mark.parametrize("count", [3, 1001])
def test_apply_submits_exact_deletions_and_reports_counts(count, capsys):
    client = _client()
    records = _records() if count == 3 else [
        _records()[0],
        *[{**_records()[3], NAME: f"student-{index}.{DOMAIN}."} for index in range(count)],
    ]
    plan = _plan(records)
    change_batches = cleanup_dns.batches(plan.changes)
    assert [len(batch) for batch in change_batches] == ([3] if count == 3 else [1000, 1])
    with Stubber(client) as stub:
        _inventory(stub, records)
        for index, batch in enumerate(change_batches):
            change_id = f"/change/CEXAMPLE{index}"
            info = {ID: change_id, STATUS: "PENDING", SUBMITTED_AT: datetime.now(timezone.utc)}
            stub.add_response("change_resource_record_sets", {CHANGE_INFO: info},
                              {HOSTED_ZONE_ID: ZONE_ID, "ChangeBatch": {CHANGES: batch}})
            stub.add_response("get_change", {CHANGE_INFO: {**info, STATUS: "INSYNC"}}, {ID: change_id})
        # A new name illustrates why the final count must come from a fresh read.
        _inventory(stub, [records[0], {**_records()[3], NAME: "new-name." + DOMAIN + "."}])
        cleanup_dns.apply_plan(client, plan)
        stub.assert_no_pending_responses()
    output = capsys.readouterr().out
    assert f"Deleting {count} record sets in {len(change_batches)} batch" in output
    assert "1 expected to remain in zone." in output
    assert f"deleted {count}/{count}; 0 remaining to delete." in output
    assert f"Done: deleted {count} record sets; 2 remain in zone." in output
    if count == 1001:
        assert "1000 record sets; waiting for INSYNC" in output
        assert "deleted 1000/1001; 1 remaining to delete." in output


@pytest.mark.parametrize("drift", ["value", "new-type", "missing"])
def test_apply_refuses_live_record_drift_before_writes(drift):
    records = _records()
    if drift == "value":
        records[2][ALIAS][DNS_NAME] = "changed.example."
    elif drift == "new-type":
        records.append({NAME: records[1][NAME], TYPE: "TXT", TTL: 60,
                        RECORDS: [{VALUE: '"added after export"'}]})
    else:
        records.pop()
    with Stubber(_client()) as stub:
        _inventory(stub, records)
        with pytest.raises(cleanup_dns.CleanupError, match="live records changed"):
            cleanup_dns.apply_plan(stub.client, _plan())
        stub.assert_no_pending_responses()
