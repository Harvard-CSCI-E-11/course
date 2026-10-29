"""Render the signed-in student's private email archive.

Both list and message routes resolve identity from the existing session.
Message lookups use that student's DynamoDB partition, never a URL user ID.
The index authorizes reading the corresponding MIME object from private S3.
Email headers and plain-text content are escaped by the dedicated templates.
Responses prohibit browser caching because archived messages contain course keys.
"""

import re
from email import policy
from email.parser import BytesParser

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from e11 import e11_common
from e11.e11core.constants import CONTENT_TYPE_HEADER, HTML_CONTENT_TYPE
from e11.email_archive import (
    CODE,
    EMAIL_BUCKET,
    EMAIL_PREFIX,
    ERROR,
    ITEM,
    STATUS,
    EmailRecord,
)

from .sessions import get_session_from_event

STATUS_CODE = "statusCode"
HEADERS = "headers"
BODY = "body"
LOCATION = "Location"
TIMESTAMP = "timestamp"
QUERY = "queryStringParameters"
PRIVATE_HEADERS = {
    CONTENT_TYPE_HEADER: HTML_CONTENT_TYPE,
    "Cache-Control": "private, no-store",
    "X-Content-Type-Options": "nosniff",
}
TIMESTAMP_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z")


def _response(status, body):
    return {STATUS_CODE: status, HEADERS: PRIVATE_HEADERS, BODY: body}


def _message_page(user, timestamp, session, env):
    if not TIMESTAMP_PATTERN.fullmatch(timestamp):
        return _response(404, "Email not found.")
    row = e11_common.users_table.get_item(
        Key={
            e11_common.A.USER_ID: user.user_id,
            e11_common.A.SK: EMAIL_PREFIX + timestamp,
        },
        ConsistentRead=True,
    ).get(ITEM)
    if row is None or row.get(STATUS) == "archive_failed":
        return _response(404, "Email not found.")
    record = EmailRecord.model_validate(row)
    archive_key = f"email/{user.user_id}/{timestamp}.eml"
    if record.bucket != EMAIL_BUCKET or record.key != archive_key:
        return _response(404, "Email not found.")
    try:
        response = e11_common.s3_client.get_object(Bucket=EMAIL_BUCKET, Key=archive_key)
    except ClientError as exc:
        if exc.response.get(ERROR, {}).get(CODE) not in {"NoSuchKey", "404"}:
            raise
        return _response(404, "Email not found.")
    stream = response["Body"]
    try:
        mime = BytesParser(policy=policy.default).parsebytes(stream.read())
    finally:
        stream.close()
    part = mime.get_body(preferencelist=("plain",))
    body = part.get_content() if part else "This message has no plain-text body."
    return _response(
        200,
        env.get_template("email_message.html").render(
            ses=session, email=record, message_body=body
        ),
    )


def email_page(event, env, *, message: bool = False):
    """Return an HTTP API response for the archive list or a single message."""
    session = get_session_from_event(event)
    if session is None:
        return {STATUS_CODE: 302, HEADERS: {**PRIVATE_HEADERS, LOCATION: "/"}, BODY: ""}
    user = e11_common.get_user_from_email(session.email)
    if message:
        return _message_page(
            user, (event.get(QUERY) or {}).get(TIMESTAMP, ""), session, env
        )
    rows = e11_common.queryscan_table(
        e11_common.users_table.query,
        {
            "KeyConditionExpression": Key(e11_common.A.USER_ID).eq(user.user_id)
            & Key(e11_common.A.SK).begins_with(EMAIL_PREFIX),
            "ScanIndexForward": False,
            "ConsistentRead": True,
        },
    )
    emails = [
        EmailRecord.model_validate(row)
        for row in rows
        if row.get(STATUS) != "archive_failed"
    ]
    return _response(
        200, env.get_template("email.html").render(ses=session, emails=emails)
    )
