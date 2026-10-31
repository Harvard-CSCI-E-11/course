# Exercise session lifetime, host-only cookies, and escaped dashboard rendering.
# Session records and conditional cleanup use the real DynamoDB Local service.
# Test payloads include HTML tags, attribute breakers, and script terminators.
# The actual Lambda handler must escape reflected and stored HTML values.
# Template script values must use HTML-safe JSON without breaking attributes.
# Local preview files contain synthetic data only; no real login or mail is sent.
"""Behavioral security regressions for the home Lambda."""

import json
import os
import time
import uuid
from html.parser import HTMLParser
from pathlib import Path

import pytest
from test_utils import create_lambda_event

from e11 import e11_common as shared
from home_app import common, home, sessions

PAYLOAD = '"\'><script>alert("student")</script><img src=x onerror=alert(1)>'
SID = "sid"
ITEM = "Item"
COOKIES = "cookies"
BODY = "body"
STATUS = "statusCode"
TTL = shared.A.TTL
EXPIRE = shared.A.SESSION_EXPIRE
AUTHENTICATED = shared.A.SESSION_LAST_AUTHENTICATED


class Page(HTMLParser):
    """Collect browser-parsed tags and attributes without executing test scripts."""

    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


def store_session(expiration, *, host_bound=True):
    sid = uuid.uuid4().hex
    item = {
        SID: sid,
        "email": "security@example.org",
        "session_created": int(time.time()) - 60,
        EXPIRE: expiration,
        "claims": None,
    }
    if host_bound:
        item[shared.A.SESSION_COOKIE_SCOPE] = common.COOKIE_NAME
    shared.sessions_table.put_item(Item=item)
    return sid


@pytest.mark.parametrize("host", ["csci-e-11.org", "stage.csci-e-11.org"])
def test_cookie_and_ttl_renew_together(fake_aws, dynamodb_local, host):
    now = int(time.time())
    sid = store_session(now + 3600)
    shared.sessions_table.update_item(
        Key={SID: sid},
        UpdateExpression="SET session_created = :old",
        ExpressionAttributeValues={":old": now - 150 * 86400},
    )
    event = create_lambda_event(
        "/", qs={"page": "terms.html"}, cookies=[f"{common.COOKIE_NAME}={sid}"]
    )
    event["headers"] = {"host": host}
    previous_context = sessions.CURRENT_SESSION.get()
    response = home.lambda_handler(event, None)
    assert response[STATUS] == 200
    cookie = response[COOKIES][0]
    assert cookie.startswith(f"__Host-AuthSid={sid};")
    assert all(
        flag in cookie for flag in ("Path=/", "Secure", "HttpOnly", "SameSite=Lax")
    )
    assert "Domain=" not in cookie
    assert "Max-Age=10368000" in cookie
    record = shared.sessions_table.get_item(Key={SID: sid}, ConsistentRead=True)[ITEM]
    assert now <= record[AUTHENTICATED] <= int(time.time())
    assert record[TTL] == record[EXPIRE] == record[AUTHENTICATED] + 120 * 86400
    # A host-bound unexpired row acquired missing activity/TTL metadata on first use.
    assert sessions.CURRENT_SESSION.get() is previous_context


def test_cookie_cannot_be_broadened_by_domain_argument():
    cookie = common.make_cookie(common.COOKIE_NAME, "test", domain="csci-e-11.org")
    assert "Domain=" not in cookie
    assert common.get_cookie_domain({}) is None


def test_expired_cookie_and_legacy_name_are_rejected(fake_aws, dynamodb_local):
    sid = store_session(int(time.time()) - 1)
    event = create_lambda_event("/dashboard", cookies=[f"{common.COOKIE_NAME}={sid}"])
    assert home.lambda_handler(event, None)[STATUS] == 302
    assert ITEM not in shared.sessions_table.get_item(Key={SID: sid})
    active = store_session(int(time.time()) + 100)
    event = create_lambda_event("/dashboard", cookies=[f"AuthSid={active}"])
    assert home.lambda_handler(event, None)[STATUS] == 302


def test_scheduled_cleanup_respects_a_concurrent_renewal(fake_aws, dynamodb_local):
    now = int(time.time())
    expired = store_session(now - 1)
    renewed = store_session(now + 3600)
    # The sweeper's stale scan must not delete a record renewed by another request.
    assert sessions.expire_batch(now, [{SID: renewed, EXPIRE: now - 1}]) == 0
    legacy = store_session(now + 3600)
    shared.sessions_table.update_item(
        Key={SID: legacy},
        UpdateExpression="SET session_created = :old",
        ExpressionAttributeValues={":old": now - common.SESSION_TTL_SECS - 1},
    )
    response = home.lambda_handler({"action": "heartbeat"}, None)
    assert response[STATUS] == 200
    assert json.loads(response[BODY])["expired"] >= 1
    assert ITEM in shared.sessions_table.get_item(Key={SID: legacy})
    assert ITEM not in shared.sessions_table.get_item(Key={SID: expired})
    assert ITEM in shared.sessions_table.get_item(Key={SID: renewed})
    # A second sweeper must not count an already absent record as a deletion.
    assert sessions.expire_batch(now, [{SID: expired, EXPIRE: now - 1}]) == 0


def test_reflected_and_stored_html_are_escaped(fake_aws, dynamodb_local):
    response = home.lambda_handler(create_lambda_event("/", qs={"page": PAYLOAD}), None)
    assert response[STATUS] == 404
    assert "<script>alert" not in response[BODY]
    assert "&lt;script&gt;" in response[BODY]
    email = f"security-{uuid.uuid4().hex}@example.org"
    user = shared.create_new_user(email)
    shared.users_table.update_item(
        Key={shared.A.USER_ID: user.user_id, shared.A.SK: shared.A.SK_USER},
        UpdateExpression="SET preferred_name = :name",
        ExpressionAttributeValues={":name": PAYLOAD},
    )
    session = sessions.new_session(create_lambda_event("/"), {"email": email})
    record = shared.sessions_table.get_item(
        Key={SID: session.sid}, ConsistentRead=True
    )[ITEM]
    assert record[TTL] == record[EXPIRE] == record[AUTHENTICATED] + 120 * 86400
    assert record[shared.A.SESSION_COOKIE_SCOPE] == common.COOKIE_NAME
    event = create_lambda_event(
        "/dashboard", cookies=[f"{common.COOKIE_NAME}={session.sid}"]
    )
    shared.add_user_log(event, user.user_id, PAYLOAD)
    response = home.lambda_handler(event, None)
    assert response[STATUS] == 200
    assert PAYLOAD not in response[BODY]
    assert "&lt;script&gt;" in response[BODY]
    page = Page()
    page.feed(response[BODY])
    assert all("onerror" not in attrs for _, attrs in page.tags)
    if directory := os.environ.get("EMAIL_PREVIEW_DIR"):
        output = Path(directory) / "security-dashboard.html"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(response[BODY])


def test_script_json_and_claim_attributes_cannot_break_out():
    body = home.env.get_template("dashboard.html").render(
        user={"email": PAYLOAD, "course_key": PAYLOAD},
        ses={SID: "example"},
        sessions=[],
        images=[],
        grades=[],
        logs=[{"claims": {"claim": PAYLOAD}, "message": PAYLOAD}],
        next_lab="lab0",
        next_deadline=PAYLOAD,
    )
    page = Page()
    page.feed(body)
    assert len([tag for tag, _ in page.tags if tag == "script"]) == 1
    assert all("onerror" not in attrs for _, attrs in page.tags)
    claims = next(
        attrs["data-claims"] for _, attrs in page.tags if "data-claims" in attrs
    )
    assert json.loads(claims) == {"claim": PAYLOAD}
    assert "\\u003cscript\\u003e" in body
    assert "&lt;script&gt;" in body


def test_pre_cutover_sid_cannot_be_replayed_or_upgraded(fake_aws, dynamodb_local):
    old_expiration = int(time.time()) + 3600
    sid = store_session(old_expiration, host_bound=False)
    # A thief cannot convert an exposed legacy SID by choosing the new cookie name.
    event = create_lambda_event("/dashboard", cookies=[f"{common.COOKIE_NAME}={sid}"])
    response = home.lambda_handler(event, None)
    assert response[STATUS] == 302
    assert not response.get(COOKIES)
    # The SID-login helper must not exchange a legacy SID for a trusted cookie.
    assert home.do_login(create_lambda_event("/login", qs={SID: sid}))[STATUS] == 404
    legacy_event = create_lambda_event("/dashboard", cookies=[f"AuthSid={sid}"])
    response = home.lambda_handler(legacy_event, None)
    assert response[STATUS] == 302
    assert len(response[COOKIES]) == 2
    assert all(
        cookie.startswith("AuthSid=;") and "Max-Age=0" in cookie
        for cookie in response[COOKIES]
    )
    assert any("Domain=csci-e-11.org" in cookie for cookie in response[COOKIES])
    record = shared.sessions_table.get_item(Key={SID: sid}, ConsistentRead=True)[ITEM]
    assert record[EXPIRE] == old_expiration
    assert TTL not in record
    assert AUTHENTICATED not in record
