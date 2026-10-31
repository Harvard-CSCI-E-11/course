"""Exercise the real email archive and authenticated dashboard routes.

All index writes and conditional claims use DynamoDB Local.
All MIME uploads, downloads, and storage failures use a real MinIO bucket.
Only SES submission is stubbed because tests must not deliver real mail.
Transport hooks inspect persisted content before SES is allowed to accept it.
Registration, duplicate suppression, and cross-student access use real records.
Run these tests through the parent Makefile's email-check target.
"""

import ast
import json
import os
import re
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from email import policy
from email.parser import BytesParser
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urljoin, urlsplit

import boto3
import pytest
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from botocore.stub import ANY, Stubber
from pydantic import BaseModel, ConfigDict, Field
from test_utils import create_lambda_event

from e11 import e11_common as common
from e11 import email_archive as archive
from e11.e11core.constants import API_PATH
from home_app import api, email_views, home, sessions
from home_app.common import COOKIE_NAME

SOURCE = "Source"
DESTINATIONS = "Destinations"
RAW_MESSAGE = "RawMessage"
DATA = "Data"
SES_MESSAGE_ID = "MessageId"
S3_BODY = "Body"
ITEMS = "Items"
CONTENTS = "Contents"
KEY = "Key"
KEY_COUNT = "KeyCount"
COOKIES = "cookies"
REQUEST_CONTEXT = "requestContext"
HTTP = "http"
PATH = "path"
QUERY = "queryStringParameters"
RAW_PATH = "rawPath"
ACTION = "action"
METHOD = "method"
BODY = "body"


class MailServices(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    s3: Any
    ses: Any
    stubber: Any
    submitted: list[bytes] = Field(default_factory=list)

    def accept(self, count=1):
        for _ in range(count):
            self.stubber.add_response(
                "send_raw_email",
                {SES_MESSAGE_ID: uuid.uuid4().hex},
                {
                    SOURCE: common.SES_VERIFIED_EMAIL,
                    DESTINATIONS: ANY,
                    RAW_MESSAGE: {DATA: ANY},
                },
            )


@pytest.fixture
def mail_services(monkeypatch, clean_dynamodb):
    endpoint = os.environ.get("MINIO_TEST_ENDPOINT")
    if not endpoint:
        if os.environ.get("REQUIRE_EMAIL_SERVICES"):
            pytest.fail("MINIO_TEST_ENDPOINT is required")
        pytest.skip("Run make email-check for real MinIO archive tests")
    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint,
        region_name="us-east-1",
        aws_access_key_id="minioadmin",
        aws_secret_access_key="minioadmin",
    )
    s3.create_bucket(Bucket=archive.EMAIL_BUCKET)
    ses = boto3.client(
        "ses",
        region_name="us-east-1",
        endpoint_url="http://127.0.0.1:9",
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )
    services = MailServices(s3=s3, ses=ses, stubber=Stubber(ses))

    def capture(params, **_kwargs):
        raw = params[RAW_MESSAGE][DATA]
        rows = common.users_table.scan()[ITEMS]
        indexed = [
            archive.EmailRecord.model_validate(row)
            for row in rows
            if row[common.A.SK].startswith(archive.EMAIL_PREFIX)
        ]
        assert any(
            s3.get_object(Bucket=row.bucket, Key=row.key)[S3_BODY].read() == raw
            for row in indexed
            if row.status != "archive_failed"
        )
        services.submitted.append(raw)

    ses.meta.events.register("before-parameter-build.ses.SendRawEmail", capture)
    monkeypatch.setattr(common, "s3_client", s3)
    monkeypatch.setattr(common, "ses_client", ses)
    with services.stubber:
        yield services
        services.stubber.assert_no_pending_responses()
    objects = s3.list_objects_v2(Bucket=archive.EMAIL_BUCKET).get(CONTENTS, [])
    for item in objects:
        s3.delete_object(Bucket=archive.EMAIL_BUCKET, Key=item[KEY])
    s3.delete_bucket(Bucket=archive.EMAIL_BUCKET)


def email_rows(user):
    rows = common.users_table.query(
        KeyConditionExpression=Key(common.A.USER_ID).eq(user.user_id)
        & Key(common.A.SK).begins_with(archive.EMAIL_PREFIX),
        ConsistentRead=True,
    )[ITEMS]
    return [archive.EmailRecord.model_validate(row) for row in rows]


def login(user):
    event = create_lambda_event("/email")
    session = sessions.new_session(event, {common.A.EMAIL: user.email})
    event[COOKIES] = [f"{COOKIE_NAME}={session.sid}"]
    return event


def test_first_registration_archives_welcome_once(mail_services):
    mail_services.accept()
    email = f"welcome-{uuid.uuid4().hex}@example.org"
    event = create_lambda_event("/auth/callback")
    first = sessions.new_session(event, {"email": email, "name": "New Student"})
    second = sessions.new_session(event, {"email": email, "name": "New Student"})
    assert first.sid != second.sid
    user = common.get_user_from_email(email)
    rows = email_rows(user)
    assert len(rows) == len(mail_services.submitted) == 1
    row = rows[0]
    timestamp = row.timestamp
    assert row.sk == f"email#{timestamp}"
    assert row.key == f"email/{user.user_id}/{timestamp}.eml"
    assert len(timestamp) == 24 and timestamp.endswith("Z")
    assert row.subject == "Welcome to CSCI E-11"
    assert row.status == "accepted" and row.message_id
    assert (
        common.get_user_from_email(email).user_id == user.user_id
    )  # The email GSI stays unique.
    raw = mail_services.s3.get_object(Bucket=archive.EMAIL_BUCKET, Key=row.key)[
        S3_BODY
    ].read()
    mime = BytesParser(policy=policy.default).parsebytes(raw)
    assert str(mime["To"]) == email
    assert user.course_key in mime.get_body().get_content()
    assert raw == mail_services.submitted[0]


def test_staff_registration_welcome_contains_direct_login(mail_services):
    mail_services.accept()
    user = common.create_new_user(f"staff-{uuid.uuid4().hex}@example.org")
    mime = BytesParser(policy=policy.default).parsebytes(mail_services.submitted[0])
    body = mime.get_body().get_content()
    assert common.generate_direct_login_url(user.user_id, user.course_key) in body
    assert len(email_rows(user)) == 1


def test_alternate_recipient_shares_one_student_archive(mail_services):
    mail_services.accept(2)
    user = common.create_new_user(f"primary-{uuid.uuid4().hex}@example.org")
    alternate = f"alternate-{uuid.uuid4().hex}@example.org"
    common.users_table.update_item(
        Key={common.A.USER_ID: user.user_id, common.A.SK: common.A.SK_USER},
        UpdateExpression="SET alt_email = :address",
        ExpressionAttributeValues={":address": alternate},
    )
    common.send_email2(
        [user.email, alternate], "Both addresses", "One message", user_id=user.user_id
    )
    row = next(row for row in email_rows(user) if row.subject == "Both addresses")
    assert row.recipients == [user.email, alternate]
    assert len(email_rows(user)) == len(mail_services.submitted) == 2


def test_concurrent_first_registration_has_one_account_and_welcome(mail_services):
    mail_services.accept()
    email = f"concurrent-{uuid.uuid4().hex}@example.org"
    with ThreadPoolExecutor(max_workers=4) as pool:
        users = list(pool.map(lambda _: common.create_new_user(email), range(4)))
    assert len({user.user_id for user in users}) == 1
    assert len(email_rows(users[0])) == len(mail_services.submitted) == 1


def test_archive_time_collision_preserves_both_messages(mail_services, monkeypatch):
    mail_services.accept(3)
    user = common.create_new_user(f"collision-{uuid.uuid4().hex}@example.org")

    class FrozenTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 10, 29, 12, 0, 0, 123000, tzinfo=UTC)

    monkeypatch.setattr(archive, "datetime", FrozenTime)
    for subject in ["First", "Second"]:
        common.send_email2(user.emails(), subject, subject, user_id=user.user_id)
    rows = [row for row in email_rows(user) if row.subject in {"First", "Second"}]
    assert [row.timestamp for row in rows] == [
        "2026-10-29T12:00:00.123Z",
        "2026-10-29T12:00:00.124Z",
    ]
    assert len({row.key for row in rows}) == 2


def test_archive_failure_prevents_ses_and_welcome_retries(mail_services, caplog):
    mail_services.s3.delete_bucket(Bucket=archive.EMAIL_BUCKET)
    user = common.create_new_user(f"retry-{uuid.uuid4().hex}@example.org")
    assert not mail_services.submitted
    assert common.get_user_from_user_id(user.user_id).welcome_status == "retryable"
    assert email_rows(user)[0].status == "archive_failed"
    failure = next(
        record
        for record in caplog.records
        if "Welcome email failed" in record.getMessage()
    )
    assert failure.exc_info is None
    assert "NoSuchBucket" in failure.getMessage()
    mail_services.s3.create_bucket(Bucket=archive.EMAIL_BUCKET)
    mail_services.accept()
    login(user)
    assert common.get_user_from_user_id(user.user_id).welcome_status == "accepted"
    assert len(mail_services.submitted) == 1


def test_missing_index_prevents_ses_and_s3(mail_services, dynamodb_local):
    with pytest.raises(ClientError):
        archive.archive_and_send(
            table=dynamodb_local.Table("absent-" + uuid.uuid4().hex),
            s3=mail_services.s3,
            ses=mail_services.ses,
            user_id="student",
            sender=common.SES_VERIFIED_EMAIL,
            recipients=["student@example.org"],
            subject="Not sent",
            body="Missing index",
        )
    assert mail_services.s3.list_objects_v2(Bucket=archive.EMAIL_BUCKET)[KEY_COUNT] == 0
    assert not mail_services.submitted


def test_unknown_welcome_submission_is_not_retried(mail_services, caplog):
    mail_services.stubber.add_client_error(
        "send_raw_email",
        service_error_code="InternalFailure",
        service_message="Submission outcome uncertain",
        http_status_code=500,
    )
    user = common.create_new_user(f"unknown-{uuid.uuid4().hex}@example.org")
    login(user)
    assert common.get_user_from_user_id(user.user_id).welcome_status == "unknown"
    assert email_rows(user)[0].status == "unknown"
    failure = next(
        record
        for record in caplog.records
        if "Welcome email submission uncertain" in record.getMessage()
    )
    assert failure.exc_info is None
    assert "not retrying automatically" in failure.getMessage()
    assert len(mail_services.submitted) == 1


def test_rejected_submission_remains_archived(mail_services):
    mail_services.accept()
    user = common.create_new_user(f"reject-{uuid.uuid4().hex}@example.org")
    mail_services.stubber.add_client_error(
        "send_raw_email", service_error_code="MessageRejected"
    )
    with pytest.raises(ClientError):
        common.send_email2(
            user.emails(), "Rejected", "Retain this body", user_id=user.user_id
        )
    row = next(row for row in email_rows(user) if row.subject == "Rejected")
    assert row.status == "rejected"
    assert mail_services.s3.get_object(Bucket=archive.EMAIL_BUCKET, Key=row.key)[
        S3_BODY
    ].read()


def test_email_list_and_new_tab_message_escape_content(mail_services, monkeypatch):
    monkeypatch.setattr(common, "SES_VERIFIED_EMAIL", "archive-sender@example.org")
    mail_services.accept(2)
    user = common.create_new_user(f"view-{uuid.uuid4().hex}@example.org")
    common.send_email2(
        user.emails(),
        "<b>Grading results</b>",
        "Hello <script>alert(1)</script> ✓",
        user_id=user.user_id,
    )
    event = login(user)
    listing = home.lambda_handler(event, None)
    assert listing[email_views.STATUS_CODE] == 200
    assert "&lt;b&gt;Grading results&lt;/b&gt;" in listing[email_views.BODY]
    assert 'target="_blank" rel="noopener noreferrer"' in listing[email_views.BODY]
    assert listing[email_views.BODY].index("Grading results") < listing[
        email_views.BODY
    ].index("Welcome to CSCI E-11")
    row = next(row for row in email_rows(user) if row.subject.startswith("<b>"))
    event[RAW_PATH] = "/email/message"
    event[REQUEST_CONTEXT][HTTP][PATH] = "/email/message"
    event[QUERY] = {"timestamp": row.timestamp}
    response = home.lambda_handler(event, None)
    assert response[email_views.STATUS_CODE] == 200
    assert f"From: {common.SES_VERIFIED_EMAIL}\n" in response[email_views.BODY]
    assert "Hello &lt;script&gt;alert(1)&lt;/script&gt; ✓" in response[email_views.BODY]
    assert "<script>alert(1)</script>" not in response[email_views.BODY]
    assert response[email_views.HEADERS]["Cache-Control"] == "private, no-store"
    if directory := os.environ.get("EMAIL_PREVIEW_DIR"):
        preview = Path(directory)
        preview.mkdir(parents=True, exist_ok=True)
        (preview / "email.html").write_text(listing[email_views.BODY])
        (preview / "email_message.html").write_text(response[email_views.BODY])


@pytest.mark.parametrize("message_date", ["Tue, 29 Sep 2026 14:07:08 -0400", None])
def test_message_date_comes_from_archived_mime(mail_services, message_date):
    """A historical or absent Date header must never become the archive timestamp."""
    mail_services.accept(2)
    user = common.create_new_user(f"date-{uuid.uuid4().hex}@example.org")
    common.send_email2(
        user.emails(), "Original date", "Date fixture", user_id=user.user_id
    )
    row = next(row for row in email_rows(user) if row.subject == "Original date")
    raw = mail_services.s3.get_object(Bucket=archive.EMAIL_BUCKET, Key=row.key)[
        S3_BODY
    ].read()
    mime = BytesParser(policy=policy.default).parsebytes(raw)
    del mime[email_views.DATE_HEADER]
    if message_date is not None:
        mime[email_views.DATE_HEADER] = message_date
    mail_services.s3.put_object(
        Bucket=archive.EMAIL_BUCKET, Key=row.key, Body=mime.as_bytes(policy=policy.SMTP)
    )
    event = login(user)
    event[RAW_PATH] = "/email/message"
    event[REQUEST_CONTEXT][HTTP][PATH] = "/email/message"
    event[QUERY] = {"timestamp": row.timestamp}
    response = home.lambda_handler(event, None)
    assert response[email_views.STATUS_CODE] == 200
    assert f"Date: {message_date or '(not provided)'}\n" in response[email_views.BODY]
    assert (
        f"Date: {home.utc_iso_to_eastern(row.timestamp)}"
        not in response[email_views.BODY]
    )


def test_message_requires_owner_and_active_session(mail_services):
    mail_services.accept()
    owner = common.create_new_user(f"owner-{uuid.uuid4().hex}@example.org")
    row = email_rows(owner)[0]
    other = common.User(
        user_id=str(uuid.uuid4()),
        sk=common.A.SK_USER,
        email=f"other-{uuid.uuid4().hex}@example.org",
        course_key="secret",
    )
    common.users_table.put_item(Item=other.model_dump(exclude_none=True))
    event = login(other)
    event[RAW_PATH] = "/email/message"
    event[REQUEST_CONTEXT][HTTP][PATH] = "/email/message"
    event[QUERY] = {
        "timestamp": row.timestamp,
        "user_id": owner.user_id,
    }
    assert home.lambda_handler(event, None)[email_views.STATUS_CODE] == 404
    event[COOKIES] = []
    assert home.lambda_handler(event, None)[email_views.STATUS_CODE] == 302
    assert (
        len(mail_services.submitted) == 1
    )  # Existing students are not retrospectively welcomed.


def test_sender_rejects_other_students_recipient(mail_services):
    mail_services.accept()
    user = common.create_new_user(f"recipient-{uuid.uuid4().hex}@example.org")
    with pytest.raises(ValueError, match="belong"):
        common.send_email2(
            ["someone-else@example.org"], "Wrong owner", "Private", user_id=user.user_id
        )
    assert len(mail_services.submitted) == 1


def test_shared_navigation_works_from_nested_email_message(mail_services):
    mail_services.accept()
    user = common.create_new_user(f"navigation-{uuid.uuid4().hex}@example.org")
    row = email_rows(user)[0]
    event = login(user)
    event[RAW_PATH] = "/email/message"
    event[QUERY] = {"timestamp": row.timestamp}
    response = home.lambda_handler(event, None)
    assert response[email_views.STATUS_CODE] == 200
    links = re.findall(
        r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', response[email_views.BODY], re.DOTALL
    )
    visited = set()
    for href, label in links:
        label = label.strip()
        destination = urlsplit(urljoin("https://app.example.org/email/message", href))
        if label in {"About", "Terms", "Privacy", "Help", "[terms]"}:
            follow = create_lambda_event(
                destination.path,
                qs=dict(parse_qsl(destination.query)),
                cookies=event[COOKIES],
            )
            assert home.lambda_handler(follow, None)[email_views.STATUS_CODE] == 200
            visited.add(label)
        elif label == "Logout":
            assert destination.path == "/logout"
            visited.add(label)
        elif label == "Harvard CSCI E-11":
            assert destination.path == "/"
            visited.add(label)
    assert visited == {
        "About",
        "Terms",
        "Privacy",
        "Help",
        "[terms]",
        "Logout",
        "Harvard CSCI E-11",
    }


def post_action(user, action, payload):
    event = login(user) if user else create_lambda_event(API_PATH)
    event[RAW_PATH] = API_PATH
    event[REQUEST_CONTEXT][HTTP][METHOD] = "POST"
    event[BODY] = json.dumps({ACTION: action, **payload})
    return home.lambda_handler(event, None)


def test_image_deletion_cannot_remove_email_or_another_students_image(mail_services):
    mail_services.accept()
    owner = common.create_new_user(f"deletion-{uuid.uuid4().hex}@example.org")
    email = email_rows(owner)[0]
    image_key = "images/" + uuid.uuid4().hex + ".jpeg"
    mail_services.s3.put_object(
        Bucket=archive.EMAIL_BUCKET, Key=image_key, Body=b"test image"
    )
    common.add_image(owner.user_id, "lab8", archive.EMAIL_BUCKET, image_key)
    image = common.get_images(owner.user_id)[0]
    payload = {
        common.A.USER_ID: owner.user_id,
        common.A.SK: email.sk,
        common.A.BUCKET: archive.EMAIL_BUCKET,
        common.A.KEY: email.key,
    }
    assert post_action(None, "delete-image", payload)[email_views.STATUS_CODE] == 403
    assert post_action(owner, "delete-image", payload)[email_views.STATUS_CODE] == 400
    with pytest.raises(ValueError, match="image"):
        common.delete_image(owner.user_id, email.sk, archive.EMAIL_BUCKET, email.key)
    other = common.User(
        user_id=str(uuid.uuid4()),
        sk=common.A.SK_USER,
        email=f"delete-other-{uuid.uuid4().hex}@example.org",
        course_key="secret",
    )
    common.users_table.put_item(Item=other.model_dump(exclude_none=True))
    payload[common.A.SK] = image[common.A.SK]
    assert post_action(other, "delete-image", payload)[email_views.STATUS_CODE] == 404
    assert len(common.get_images(owner.user_id)) == 1
    # The owner can delete the actual image, but payload locations cannot select email.
    assert post_action(owner, "delete-image", payload)[email_views.STATUS_CODE] == 200
    assert not common.get_images(owner.user_id)
    assert mail_services.s3.get_object(Bucket=archive.EMAIL_BUCKET, Key=email.key)[
        S3_BODY
    ].read()
    assert len(email_rows(owner)) == 1
    with pytest.raises(ClientError):
        mail_services.s3.head_object(Bucket=archive.EMAIL_BUCKET, Key=image_key)


def test_diagnostics_return_only_safe_status_fields(mail_services, monkeypatch):
    monkeypatch.setenv("EMAIL_DIAGNOSTIC_TEST_MARKER", "synthetic-test-only")
    response = api.dispatch("POST", "ping", create_lambda_event(API_PATH), object(), {})
    assert json.loads(response[email_views.BODY]) == {"error": False, "message": "ok"}
    mail_services.accept(2)
    user = common.create_new_user(f"diagnostic-{uuid.uuid4().hex}@example.org")
    response = post_action(
        user,
        "ping-mail",
        {"auth": {common.A.EMAIL: user.email, common.A.COURSE_KEY: user.course_key}},
    )
    body = json.loads(response[email_views.BODY])
    assert response[email_views.STATUS_CODE] == 200
    assert set(body) == {"error", "message", archive.MESSAGE_ID}
    assert body[archive.MESSAGE_ID]
    assert "synthetic-test-only" not in response[email_views.BODY]
    assert len(email_rows(user)) == len(mail_services.submitted) == 2


def test_only_one_outbound_transport_path():
    root = Path(__file__).resolve().parents[2]
    generated = [root / "lambda-home/src/e11", root / "lambda-leaderboard/src/e11"]
    calls = []
    for directory in [
        root / "e11",
        root / "lambda-home/src",
        root / "lambda-leaderboard/src",
    ]:
        for path in directory.rglob("*.py"):
            if any(path.is_relative_to(package) for package in generated):
                continue  # uv-installed copies of the canonical shared package.
            for node in ast.walk(ast.parse(path.read_text())):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr
                    in {"send_email", "send_raw_email", "sendmail", "send_message"}
                ):
                    if (
                        node.func.attr == "send_message"
                        and isinstance(node.func.value, ast.Name)
                        and node.func.value.id == "sqs_client"
                    ):
                        continue  # SQS submission is not an email transport.
                    calls.append((path.relative_to(root).as_posix(), node.func.attr))
    assert calls == [("e11/email_archive.py", "send_raw_email")]
