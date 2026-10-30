"""Check scoped Lambda-log discovery and retention changes without deleting logs.

CloudWatch and CloudFormation have no required local emulator in this project.
Botocore Stubber therefore checks the exact AWS contract without live writes.
Cases cover historical groups, creation races, failed readback and account guards.
Unexpected destructive calls fail instead of being accepted by a permissive mock.
"""

from datetime import datetime, timezone
from types import SimpleNamespace

import boto3
import pytest
from botocore.stub import Stubber

from e11.e11admin import lambda_logs as ll

STACK_NAME = "StackName"
PREFIX = "logGroupNamePrefix"
LOGICAL_ID = "LogicalResourceId"
RESOURCE_STATUS = "ResourceStatus"
LAST_UPDATED = "LastUpdatedTimestamp"


def test_discovers_current_and_historical_groups():
    cf = boto3.client("cloudformation")
    logs = boto3.client("logs")
    with Stubber(cf) as cloud, Stubber(logs) as log:
        cloud.add_response("list_stack_resources", {ll.RESOURCES: [{LOGICAL_ID: "Function", ll.PHYSICAL_ID: "home-app-prod-Function-current",
                           ll.RESOURCE_TYPE: "AWS::Lambda::Function", RESOURCE_STATUS: "CREATE_COMPLETE", LAST_UPDATED: datetime(2026, 1, 1, tzinfo=timezone.utc)}]}, {STACK_NAME: "home-app-prod"})
        log.add_response("describe_log_groups", {ll.GROUPS: [{ll.GROUP_NAME: "/aws/lambda/home-app-prod-Function-old", ll.RETENTION: 365}]},
                         {PREFIX: "/aws/lambda/home-app-prod-"})
        groups = ll.discover_groups(cf, logs, ["home-app-prod"])
        assert [(g.name, g.exists, g.before_days) for g in groups] == [
            ("/aws/lambda/home-app-prod-Function-current", False, None),
            ("/aws/lambda/home-app-prod-Function-old", True, 365)]
        cloud.assert_no_pending_responses()
        log.assert_no_pending_responses()


def test_applies_retention_and_handles_create_race():
    logs = boto3.client("logs")
    group = ll.LogGroupPlan(name="/aws/lambda/home-app-prod-test", exists=False)
    with Stubber(logs) as stub:
        stub.add_client_error("create_log_group", "ResourceAlreadyExistsException", expected_params={ll.GROUP_NAME: group.name})
        stub.add_response("put_retention_policy", {}, {ll.GROUP_NAME: group.name, ll.RETENTION: 180})
        stub.add_response("describe_log_groups", {ll.GROUPS: [{ll.GROUP_NAME: group.name, ll.RETENTION: 180}]}, {PREFIX: group.name})
        ll.apply_retention(logs, [group])
        assert group.after_days == 180
        stub.assert_no_pending_responses()


def test_failed_readback_is_not_reported_as_success():
    logs = boto3.client("logs")
    group = ll.LogGroupPlan(name="/aws/lambda/leaderboard-test", exists=True)
    with Stubber(logs) as stub:
        stub.add_response("put_retention_policy", {}, {ll.GROUP_NAME: group.name, ll.RETENTION: 180})
        stub.add_response("describe_log_groups", {ll.GROUPS: [{ll.GROUP_NAME: group.name}]}, {PREFIX: group.name})
        with pytest.raises(RuntimeError, match="readback failed"):
            ll.apply_retention(logs, [group])
        assert group.after_days is None


def test_wrong_account_stops_before_log_access(monkeypatch):
    sts = boto3.client("sts")
    requested_clients = []
    def client(service):
        requested_clients.append(service)
        assert service == "sts"
        return sts
    with Stubber(sts) as stub:
        stub.add_response("get_caller_identity", {"Account": "000000000000", "Arn": "arn:aws:iam::000000000000:user/test", "UserId": "test"})
        monkeypatch.setattr(ll.boto3, "Session", lambda **kwargs: SimpleNamespace(client=client))
        monkeypatch.setattr("sys.argv", ["lambda_logs", "--apply"])
        with pytest.raises(RuntimeError, match="account does not match"):
            ll.main()
        assert requested_clients == ["sts"]
