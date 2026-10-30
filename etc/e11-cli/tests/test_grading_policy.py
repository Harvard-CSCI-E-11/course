"""Verify the Spring 2027 noon deadlines and consistent late-grade awards.

Pure checks exercise the exact cutoff, Eastern DST offsets and cap arithmetic.
DynamoDB Local checks the persisted awarded/raw scores and highest-grade rule.
Email rendering is checked against the same stored result without sending mail.
No historical grades or real student records are changed by these tests.
"""

import importlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from e11 import e11_common as common
from e11.e11core import grader


@pytest.mark.parametrize("lab,day", enumerate(["02-01", "02-08", "02-15", "02-22", "03-08", "03-29", "04-12", "04-26", "05-10"]))
def test_noon_deadline_and_late_cap(lab, day):
    deadline = datetime.fromisoformat(f"2027-{day}T12:00:00").replace(tzinfo=common.LAB_TIMEZONE)
    assert deadline.weekday() == 0
    assert common.LAB_CONFIG[f"lab{lab}"]["deadline"] == f"2027-{day}T12:00:00"
    assert common.evaluate_grade_policy(str(lab), 5, deadline).score == 5
    policy = common.evaluate_grade_policy(f"lab{lab}", 5, deadline + timedelta(microseconds=1))
    assert policy.late and policy.score == 4.45 and policy.raw_score == 5
    assert common.evaluate_grade_policy(f"lab{lab}", 3, deadline + timedelta(days=1)).score == 3


def test_eastern_dst_and_naive_clock_guard():
    assert not common.evaluate_grade_policy("lab0", 5, datetime(2027, 2, 1, 17, tzinfo=timezone.utc)).late
    assert not common.evaluate_grade_policy("lab5", 5, datetime(2027, 3, 29, 16, tzinfo=timezone.utc)).late
    assert common.evaluate_grade_policy("lab5", 5, datetime(2027, 3, 29, 16, 0, 1, tzinfo=timezone.utc)).late
    with pytest.raises(ValueError, match="timezone"):
        common.evaluate_grade_policy("lab0", 5, datetime(2027, 2, 1, 12))


def test_aws_receipt_timestamp_is_authoritative():
    queued = datetime(2027, 2, 1, 16, 59, 59, tzinfo=timezone.utc)
    receipt = common.grading_receipt_time({common.A.REQUEST_TIME_EPOCH: str(int(queued.timestamp() * 1000))})
    assert receipt == queued
    assert common.evaluate_grade_policy("lab0", 5, receipt).score == 5
    assert common.grading_receipt_time({}) is None


def test_stored_grade_email_and_existing_best_agree(dynamodb_local):
    user = common.User(user_id=str(uuid.uuid4()), sk="#", email="policy@example.com")
    deadline = datetime(2027, 2, 1, 12, tzinfo=common.LAB_TIMEZONE)
    def summary():
        return {"lab": "lab0", "score": 5, "passes": ["example"], "fails": [], "tests": []}
    common.add_grade(user, "lab0", "127.0.0.1", summary(), requested_at=deadline)
    late = summary()
    common.add_grade(user, "lab0", "127.0.0.1", late, requested_at=deadline + timedelta(seconds=1))
    rows = common.users_table.query(KeyConditionExpression=common.Key(common.A.USER_ID).eq(user.user_id), ConsistentRead=True)["Items"]
    row = next(item for item in rows if item[common.A.LATE])
    assert row[common.A.SCORE] == "4.45" and row[common.A.RAW_SCORE] == "5.0"
    assert json.loads(row["raw"])[common.A.SCORE] == late[common.A.SCORE] == 4.45
    assert common.get_grade(user, "lab0") == 5
    subject, body = grader.create_email(late)
    assert "4.45/5.0" in subject and "89/100" in body and "2027-02-01T12:00:00-05:00" in body


def test_leaderboard_late_email_explains_retained_higher_grade(dynamodb_local, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "lambda-leaderboard/src"))
    app_module = importlib.import_module("leaderboard_app.flask_app")
    user = common.User(user_id=str(uuid.uuid4()), sk="#", email=f"leader-{uuid.uuid4().hex}@example.com", course_key="test-key")
    common.users_table.put_item(Item=user.model_dump(exclude_none=True))
    deadline = datetime(2027, 4, 26, 12, tzinfo=common.LAB_TIMEZONE)
    common.add_grade(user, "lab7", "127.0.0.1", {"lab": "lab7", "score": 5, "passes": [], "fails": [], "tests": []}, requested_at=deadline)
    sent = []
    monkeypatch.setattr(app_module, "send_email2", lambda **kwargs: sent.append(kwargs))
    response = app_module.app.test_client().post("/api/register", data={"email": user.email, "course_key": user.course_key},
        headers={"User-Agent": "magic"}, environ_overrides={"apig_wsgi.request_context": {common.A.REQUEST_TIME_EPOCH: int((deadline + timedelta(seconds=1)).timestamp() * 1000)}})
    assert response.status_code == 200
    assert "4.45/5.0" in sent[0]["email_subject"]
    assert "previous highest grade was 5.0" in sent[0]["email_body"]
    assert "will be reported to Canvas" in sent[0]["email_body"]
    assert common.get_grade(user, "lab7") == 5
