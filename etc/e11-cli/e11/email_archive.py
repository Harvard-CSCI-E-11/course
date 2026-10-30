"""Preserve each student email before its single SES submission.

DynamoDB reserves a millisecond timestamp within the student's partition.
That timestamp identifies an immutable MIME object in the course S3 bucket.
Submission status distinguishes an SES acceptance from an uncertain attempt.
Storage failures prevent sending; accepted submissions are never retried here.
The dashboard uses these records to authorize access to the private archive.
"""

from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.policy import SMTP
from email.utils import format_datetime, make_msgid
from typing import Any, Literal

from botocore.exceptions import BotoCoreError, ClientError
from pydantic import BaseModel

from e11.e11core.utils import get_logger

EMAIL_PREFIX = "email#"
EMAIL_BUCKET = "csci-e-11"
MIME_TYPE = "message/rfc822"
USER_ID = "user_id"
SORT_KEY = "sk"
STATUS = "status"
MESSAGE_ID = "message_id"
ITEM = "Item"
ERROR = "Error"
CODE = "Code"
SES_MESSAGE_ID = "MessageId"
WELCOME_STATUS = "welcome_status"
LOGGER = get_logger(__name__)


class EmailRecord(BaseModel):
    """An email archive index row; recipients must not populate the email GSI."""

    user_id: str
    sk: str
    timestamp: str
    subject: str
    recipients: list[str]
    bucket: str = EMAIL_BUCKET
    key: str
    status: Literal["pending", "archive_failed", "accepted", "rejected", "unknown"] = "pending"
    message_id: str | None = None


class EmailSubmissionUnknown(RuntimeError):
    """SES may have accepted this message; automatic resubmission is unsafe."""


def _status(table: Any, record: EmailRecord, status: str, message_id: str = ""):
    """Best-effort outcome update: a failure must not resubmit an accepted email."""
    try:
        table.update_item(
            Key={USER_ID: record.user_id, SORT_KEY: record.sk},
            UpdateExpression="SET #status = :status, #message_id = :message_id",
            ExpressionAttributeNames={"#status": STATUS, "#message_id": MESSAGE_ID},
            ExpressionAttributeValues={":status": status, ":message_id": message_id},
        )
    except (BotoCoreError, ClientError):
        LOGGER.exception("Cannot record email outcome user_id=%s sk=%s status=%s message_id=%s",
                         record.user_id, record.sk, status, message_id)


def archive_and_send(*, table: Any, s3: Any, ses: Any, user_id: str,
                     sender: str, recipients: list[str], subject: str, body: str):
    """Archive one MIME message and submit those exact bytes to SES once."""
    message = EmailMessage(policy=SMTP)
    message["From"] = sender
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject
    message["Date"] = format_datetime(datetime.now(timezone.utc))
    message["Message-ID"] = make_msgid()
    message.set_content(body)
    raw = message.as_bytes()

    instant = datetime.now(timezone.utc)
    for offset in range(1000):
        timestamp = (instant + timedelta(milliseconds=offset)).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        record = EmailRecord(user_id=user_id, sk=EMAIL_PREFIX + timestamp,
                             timestamp=timestamp, subject=subject, recipients=recipients,
                             key=f"email/{user_id}/{timestamp}.eml")
        try:
            table.put_item(Item=record.model_dump(exclude_none=True),
                           ConditionExpression="attribute_not_exists(user_id) AND attribute_not_exists(sk)")
            break
        except ClientError as exc:
            if exc.response.get(ERROR, {}).get(CODE) != "ConditionalCheckFailedException":
                raise
    else:
        raise RuntimeError("Cannot reserve a unique email archive timestamp")

    try:
        s3.put_object(Bucket=record.bucket, Key=record.key, Body=raw,
                      ContentType=MIME_TYPE, IfNoneMatch="*")
    except (BotoCoreError, ClientError):
        _status(table, record, "archive_failed")
        raise
    try:
        response = ses.send_raw_email(Source=sender, Destinations=recipients,
                                      RawMessage={"Data": raw})
    except ClientError as exc:
        # Server failures, throttling, and transport errors can be ambiguous.
        rejected = exc.response.get(ERROR, {}).get(CODE) in {
            "MessageRejected", "MailFromDomainNotVerifiedException",
            "ConfigurationSetDoesNotExistException", "ConfigurationSetSendingPausedException",
            "AccountSendingPausedException", "AccessDenied", "AccessDeniedException",
            "InvalidParameterValue", "InvalidParameterValueException",
        }
        _status(table, record, "rejected" if rejected else "unknown")
        if not rejected:
            raise EmailSubmissionUnknown(record.sk) from exc
        raise
    except BotoCoreError as exc:
        _status(table, record, "unknown")
        raise EmailSubmissionUnknown(record.sk) from exc
    _status(table, record, "accepted", response[SES_MESSAGE_ID])
    return response
