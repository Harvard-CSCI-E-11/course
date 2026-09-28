"""Offline tests for the exact Route 53 cleanup plan and command guards."""

import importlib.util
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "e11/e11admin/end-of-term/cleanup_dns.py"
SPEC = importlib.util.spec_from_file_location("cleanup_dns", SCRIPT)
assert SPEC and SPEC.loader
cleanup_dns = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = cleanup_dns
SPEC.loader.exec_module(cleanup_dns)

DOMAIN = "csci-e-11.org"
ZONE_ID = "ZEXAMPLE"
ACCOUNT_ID = "123456789012"


def _records():
    return [
        {"Name": "csci-e-11.org.", "Type": "SOA", "TTL": 900,
         "ResourceRecords": [{"Value": "ns.example. host.example. 1 2 3 4 5"}]},
        {"Name": "student.csci-e-11.org.", "Type": "A", "SetIdentifier": "east",
         "Weight": 50, "TTL": 60, "ResourceRecords": [{"Value": "192.0.2.1"}]},
        {"Name": "student.csci-e-11.org.", "Type": "A", "SetIdentifier": "west",
         "Weight": 50, "AliasTarget": {"HostedZoneId": "ZALIAS", "DNSName": "target.example.",
                                        "EvaluateTargetHealth": False}},
        {"Name": "other.csci-e-11.org.", "Type": "AAAA", "TTL": 60,
         "ResourceRecords": [{"Value": "2001:db8::1"}]},
    ]


def test_plan_preserves_alias_and_routing_fields_and_only_selected_name():
    plan = cleanup_dns.build_plan(_records(), {"student.csci-e-11.org."},
                                  DOMAIN, ZONE_ID, ACCOUNT_ID)
    assert [change["ResourceRecordSet"] for change in plan.changes] == _records()[1:3]
    assert all(change["Action"] == "DELETE" for change in plan.changes)
    assert len(cleanup_dns.batches(plan.changes)) == 1
    cleanup_dns._matching_records(plan, _records())
    changed = _records()
    changed[2]["AliasTarget"]["DNSName"] = "new-target.example."
    with pytest.raises(cleanup_dns.CleanupError, match="changed"):
        cleanup_dns._matching_records(plan, changed)


def test_plan_rejects_missing_and_unsafe_records():
    with pytest.raises(cleanup_dns.CleanupError, match="no records"):
        cleanup_dns.build_plan(_records(), {"missing.csci-e-11.org."},
                               DOMAIN, ZONE_ID, ACCOUNT_ID)
    traffic_policy = _records()
    traffic_policy[1]["TrafficPolicyInstanceId"] = "example"
    with pytest.raises(cleanup_dns.CleanupError, match="separate handling"):
        cleanup_dns.build_plan(traffic_policy, {"student.csci-e-11.org."},
                               DOMAIN, ZONE_ID, ACCOUNT_ID)
    records = _records()
    records.append(records[1].copy())
    with pytest.raises(cleanup_dns.CleanupError, match="duplicate"):
        cleanup_dns.build_plan(records, {"student.csci-e-11.org."},
                               DOMAIN, ZONE_ID, ACCOUNT_ID)


def test_batching_obeys_element_and_character_limits():
    change = {"Action": "DELETE", "ResourceRecordSet": {
        "Name": "student.csci-e-11.org.", "Type": "TXT", "TTL": 60,
        "ResourceRecords": [{"Value": "x"}],
    }}
    assert [len(batch) for batch in cleanup_dns.batches([change] * 1001)] == [1000, 1]
    long = {"Action": "DELETE", "ResourceRecordSet": {
        **change["ResourceRecordSet"], "ResourceRecords": [{"Value": "x" * 20000}],
    }}
    assert [len(batch) for batch in cleanup_dns.batches([long, long])] == [1, 1]
    too_long = {"Action": "DELETE", "ResourceRecordSet": {
        **change["ResourceRecordSet"], "ResourceRecords": [{"Value": "x" * 32001}],
    }}
    with pytest.raises(cleanup_dns.CleanupError, match="batch limits"):
        cleanup_dns.batches([too_long])


def test_offline_command_writes_reviewable_plan_and_rejects_wrong_hash(tmp_path):
    export = tmp_path / "zone.json"
    export.write_text(json.dumps({"ResourceRecordSets": _records()}), encoding="utf-8")
    names = tmp_path / "student-names.txt"
    names.write_text("student.csci-e-11.org.\n", encoding="utf-8")
    plan_path = tmp_path / "plan.json"
    project = Path(__file__).resolve().parents[1]
    common = ["make", "--silent", "--no-print-directory",
              f"DNS_DOMAIN={DOMAIN}", f"DNS_ZONE_ID={ZONE_ID}",
              f"DNS_ACCOUNT_ID={ACCOUNT_ID}", f"DNS_PLAN={plan_path}"]
    planned = subprocess.run(
        [*common, "dns-plan", f"DNS_NAMES={names}", f"DNS_ZONE_EXPORT={export}"],
        cwd=project, check=True, capture_output=True, text=True,
    )
    assert "changes: 2" in planned.stdout
    assert len(json.loads(plan_path.read_text())["changes"]) == 2
    digest = hashlib.sha256(plan_path.read_bytes()).hexdigest()
    assert len(cleanup_dns._read_plan(plan_path, digest).changes) == 2
    rejected = subprocess.run(
        [*common, "dns-apply", f"DNS_SHA256={'0' * 64}"],
        cwd=project, check=False, capture_output=True, text=True,
    )
    assert rejected.returncode != 0
    assert "SHA-256 does not match" in rejected.stderr
