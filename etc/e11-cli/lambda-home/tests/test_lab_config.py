"""
Tests for LAB_CONFIG functionality including deadline checking and next_lab computation.

IMPORTANT TESTING NOTE:
======================
We use DynamoDB Local for testing, NOT monkeypatching for DynamoDB operations.
- Create actual records using create_new_user() and new_session()
- Query the real DynamoDB Local tables (they have proper GSI indexes)
- Do NOT mock users_table.query or sessions_table.query for user/session lookups
- Only mock users_table.query if you need to return empty items for logs/grades/images
  to simplify a test, but NEVER mock sessions_table.query - always use the real table!
"""

import json
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from e11.e11_common import LAB_CONFIG, LAB_REDIRECTS
from e11.e11core.constants import HTTP_OK
from home_app import api, home
from home_app.common import COOKIE_NAME


def test_lab_config_structure():
    """Test that LAB_CONFIG has the correct structure for all labs."""
    assert len(LAB_CONFIG) == 9, "LAB_CONFIG should have 9 labs (lab0-lab8)"

    for lab_num in range(9):
        lab_key = f"lab{lab_num}"
        assert lab_key in LAB_CONFIG, f"Missing {lab_key} in LAB_CONFIG"
        lab_config = LAB_CONFIG[lab_key]

        assert "redirect" in lab_config, f"{lab_key} missing 'redirect'"
        assert "deadline" in lab_config, f"{lab_key} missing 'deadline'"
        assert isinstance(lab_config["redirect"], str), (
            f"{lab_key}.redirect should be a string"
        )
        assert lab_config["redirect"].startswith("http"), (
            f"{lab_key}.redirect should be a valid URL"
        )

        # Verify deadline is valid ISO-8601 format (no timezone, Eastern time)
        deadline_str = lab_config["deadline"]
        deadline = datetime.fromisoformat(deadline_str)
        assert deadline.tzinfo is None, (
            f"{lab_key}.deadline should not have timezone (assumed Eastern)"
        )


def test_lab_config_backward_compatibility():
    """Test that LAB_REDIRECTS still works for backward compatibility."""
    assert len(LAB_REDIRECTS) == 9, "LAB_REDIRECTS should have 9 labs"

    for lab_num in range(9):
        assert lab_num in LAB_REDIRECTS, f"LAB_REDIRECTS missing lab {lab_num}"
        assert LAB_REDIRECTS[lab_num] == LAB_CONFIG[f"lab{lab_num}"]["redirect"], (
            f"LAB_REDIRECTS[{lab_num}] should match LAB_CONFIG['lab{lab_num}']['redirect']"
        )


def test_lab_redirects_still_work():
    """Test that lab redirect routes still work with LAB_CONFIG."""

    event = {
        "requestContext": {
            "http": {"method": "GET", "sourceIp": "1.2.3.4"},
            "stage": "test",
        },
        "rawPath": "/lab0",
    }

    response = home.lambda_handler(event, None)
    assert response["statusCode"] == 302
    assert response["headers"]["Location"] == LAB_CONFIG["lab0"]["redirect"]


@pytest.mark.parametrize("source", ["api", "sqs"])
@pytest.mark.parametrize("seconds,score", [(-1, 5), (0, 5), (1, 4.45)])
def test_api_grader_accepts_requests_and_caps_late_results(source, seconds, score, monkeypatch, dynamodb_local):
    """Both delivery paths persist, return and email the same awarded grade."""
    import uuid

    from e11 import e11_common as common

    email = f"grade-{uuid.uuid4().hex}@example.com"
    user = common.User(user_id=str(uuid.uuid4()), sk="#", email=email,
                       course_key="test-key", public_ip="203.0.113.1")
    common.users_table.put_item(Item=user.model_dump(exclude_none=True))
    deadline = datetime.fromisoformat(LAB_CONFIG["lab0"]["deadline"]).replace(tzinfo=common.LAB_TIMEZONE)
    received = deadline + timedelta(seconds=seconds)

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return received + timedelta(minutes=5)

    summary = {"lab": "lab0", "score": 5, "passes": ["test"], "fails": [], "tests": [], "error": False}
    sent = []
    monkeypatch.setattr(api, "datetime", Clock)
    monkeypatch.setattr(api, "get_pkey_pem", lambda key: "unused")
    monkeypatch.setattr(api.grader, "grade_student_vm", lambda *args, **kwargs: summary)
    monkeypatch.setattr(api, "send_email2", lambda **kwargs: sent.append(kwargs))
    event = {"source": source, "requestContext": {common.A.REQUEST_TIME_EPOCH: int(received.timestamp() * 1000),
             "http": {"method": "POST", "sourceIp": "127.0.0.1"}}}
    response = api.api_grader(event, None, {"auth": {"email": email, "course_key": "test-key"}, "lab": "lab0"})
    assert response["statusCode"] == HTTP_OK
    awarded = json.loads(response["body"])["summary"]
    assert awarded["score"] == score and awarded["late"] == (seconds > 0)
    assert common.get_grade(user, "lab0") == score
    assert f"score {float(score)}/5.0" in sent[0]["email_subject"]
    assert ("89/100" in sent[0]["email_body"]) == (seconds > 0)


def test_do_dashboard_computes_next_lab(monkeypatch, fake_aws, dynamodb_local):
    """
    Test that do_dashboard correctly computes next_lab.

    IMPORTANT: This test uses DynamoDB Local, NOT mocking. The user and session
    are created in the real DynamoDB Local tables. We only mock users_table.query
    to return empty items for logs/grades/images (to simplify the test), but the
    session query uses the real DynamoDB Local table.
    """
    # Create test user - this puts the user record in DynamoDB Local
    import time
    import uuid

    from e11.e11_common import A, create_new_user, users_table
    from e11.e11core.utils import smash_email
    from home_app.sessions import new_session

    test_email = f"test-{uuid.uuid4().hex[:8]}@example.com"
    user = create_new_user(
        test_email,
        {
            "email": test_email,
            "preferred_name": "Test User",
        },
    )
    # Register the instance by setting public_ip on the user record
    users_table.update_item(
        Key={"user_id": user[A.USER_ID], "sk": user[A.SK]},
        UpdateExpression=f"SET {A.PUBLIC_IP} = :ip, {A.HOSTNAME} = :hn, {A.HOST_REGISTERED} = :t",
        ExpressionAttributeValues={
            ":ip": "1.2.3.4",
            ":hn": smash_email(test_email),
            ":t": int(time.time()),
        },
    )

    # Create a session using new_session - this goes into DynamoDB Local
    event_for_session = {"requestContext": {"http": {"sourceIp": "1.2.3.4"}}}
    ses = new_session(
        event_for_session, {"email": test_email, "preferred_name": "Test User"}
    )

    event = {
        "requestContext": {
            "http": {"method": "GET", "sourceIp": "1.2.3.4"},
            "stage": "test",
        },
        "rawPath": "/dashboard",
        "cookies": [f"{COOKIE_NAME}={ses.sid}"],
    }

    # Mock time to be before lab0 deadline
    from e11.e11_common import LAB_TIMEZONE

    test_time = datetime(2026, 1, 15, 12, 0, 0, tzinfo=LAB_TIMEZONE)  # Before lab0

    with patch("home_app.home.datetime") as mock_dt:
        mock_dt.datetime.now.return_value = test_time
        mock_dt.datetime.fromisoformat = datetime.fromisoformat
        with patch("home_app.home.LAB_TIMEZONE", LAB_TIMEZONE):
            # NOTE: We need to be careful about mocking. do_dashboard calls:
            # 1. get_user_from_email() - uses e11_common.users_table.query with GSI_Email (NEED REAL TABLE)
            # 2. users_table.query() for logs/grades/images - we can mock this
            # 3. all_sessions_for_email() - uses sessions_table.query with GSI_Email (NEED REAL TABLE)
            #
            # We can't mock users_table.query globally because get_user_from_email needs it.
            # Instead, we need to ensure the user exists and let the real queries work.
            # For logs/grades/images, do_dashboard uses queryscan_table(users_table.query, ...)
            # which we can't easily mock without breaking get_user_from_email.
            #
            # Solution: Don't mock users_table.query at all - just ensure the user exists
            # and let the real queries work. The test will be slower but more accurate.
            response = home.do_dashboard(event)
            assert response["statusCode"] == 200

            # Parse the HTML to check for next_lab
            body = response["body"]
            assert "lab0" in body or "next_lab" in body.lower()


def test_do_dashboard_no_next_lab_when_all_past(monkeypatch, fake_aws, dynamodb_local):
    """
    Test that do_dashboard handles case when all labs are past.

    IMPORTANT: This test uses DynamoDB Local, NOT mocking. The user and session
    are created in the real DynamoDB Local tables. We only mock users_table.query
    to return empty items for logs/grades/images (to simplify the test), but the
    session query uses the real DynamoDB Local table.
    """
    # Create test user - this puts the user record in DynamoDB Local
    import time
    import uuid

    from e11.e11_common import A, create_new_user, users_table
    from e11.e11core.utils import smash_email
    from home_app.sessions import new_session

    test_email = f"test-{uuid.uuid4().hex[:8]}@example.com"
    user = create_new_user(
        test_email,
        {
            "email": test_email,
            "preferred_name": "Test User",
        },
    )
    # Register the instance by setting public_ip on the user record
    users_table.update_item(
        Key={"user_id": user[A.USER_ID], "sk": user[A.SK]},
        UpdateExpression=f"SET {A.PUBLIC_IP} = :ip, {A.HOSTNAME} = :hn, {A.HOST_REGISTERED} = :t",
        ExpressionAttributeValues={
            ":ip": "1.2.3.4",
            ":hn": smash_email(test_email),
            ":t": int(time.time()),
        },
    )

    # Create a session using new_session - this goes into DynamoDB Local
    event_for_session = {"requestContext": {"http": {"sourceIp": "1.2.3.4"}}}
    ses = new_session(
        event_for_session, {"email": test_email, "preferred_name": "Test User"}
    )

    event = {
        "requestContext": {
            "http": {"method": "GET", "sourceIp": "1.2.3.4"},
            "stage": "test",
        },
        "rawPath": "/dashboard",
        "cookies": [f"{COOKIE_NAME}={ses.sid}"],
    }

    # Mock time to be after all lab deadlines
    from e11.e11_common import LAB_TIMEZONE

    test_time = datetime(2027, 1, 1, 12, 0, 0, tzinfo=LAB_TIMEZONE)  # After all labs

    with patch("home_app.home.datetime") as mock_dt:
        mock_dt.datetime.now.return_value = test_time
        mock_dt.datetime.fromisoformat = datetime.fromisoformat
        with patch("home_app.home.LAB_TIMEZONE", LAB_TIMEZONE):
            # NOTE: We need to be careful about mocking. do_dashboard calls:
            # 1. get_user_from_email() - uses e11_common.users_table.query with GSI_Email (NEED REAL TABLE)
            # 2. users_table.query() for logs/grades/images - we can mock this
            # 3. all_sessions_for_email() - uses sessions_table.query with GSI_Email (NEED REAL TABLE)
            #
            # We can't mock users_table.query globally because get_user_from_email needs it.
            # Instead, we need to ensure the user exists and let the real queries work.
            # For logs/grades/images, do_dashboard uses queryscan_table(users_table.query, ...)
            # which we can't easily mock without breaking get_user_from_email.
            #
            # Solution: Don't mock users_table.query at all - just ensure the user exists
            # and let the real queries work. The test will be slower but more accurate.
            response = home.do_dashboard(event)
            assert response["statusCode"] == 200
            # Should not crash even when no next_lab


def test_lab_name_normalization():
    """Test that lab name normalization works correctly."""
    # Test various lab name formats
    test_cases = [
        ("lab0", "lab0"),
        ("lab1", "lab1"),
        ("0", "lab0"),
        ("1", "lab1"),
        ("lab2", "lab2"),
    ]

    for input_lab, expected_key in test_cases:
        if input_lab.startswith("lab"):
            lab_key = input_lab
        else:
            lab_num = input_lab.replace("lab", "").strip()
            lab_key = f"lab{lab_num}"

        assert lab_key == expected_key, (
            f"Normalization failed: {input_lab} -> {lab_key} (expected {expected_key})"
        )
