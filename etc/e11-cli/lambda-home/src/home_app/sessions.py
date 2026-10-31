"""
Sessions Management
"""

# at top of home_app/home.py (module import time)
import time
import uuid
from contextvars import ContextVar

from botocore.exceptions import ClientError

from e11.e11_common import (
    A,
    EmailNotRegistered,
    Session,
    add_user_log,
    convert_dynamodb_item,
    create_new_user,
    get_user_from_email,
    send_welcome_email,
    sessions_table,
)
from e11.e11core.utils import get_logger

from .common import COOKIE_NAME, SESSION_TTL_SECS, get_cookie_domain

SID = "sid"
ERROR = "Error"
CODE = "Code"
LOGGER = get_logger("home")
CURRENT_SESSION: ContextVar[Session | None] = ContextVar(
    "current_session", default=None
)

# Auth Cookie


################################################################
## session management - sessions are signed cookies that are stored in the DynamoDB
##


def parse_cookies(event) -> dict:
    """Extract the cookies from HTTP API v2 event"""
    cookie_list = event.get("cookies") or []
    cookies = {}
    for c in cookie_list:
        if "=" in c:
            k, v = c.split("=", 1)
            cookies[k] = v
    return cookies


def new_session(event, claims) -> Session:
    """Create a new session from the OIDC claims and store in the DyanmoDB table.
    The esid (email plus session identifier) is {email}:{uuid}
    Get the USER_ID from the users table. If it is not there, create it.
    Returns the Session object.
    """
    client_ip = event["requestContext"]["http"]["sourceIp"]  # canonical client IP
    LOGGER.debug("in new_session. claims=%s client_ip=%s", claims, client_ip)
    email = claims[A.EMAIL]

    try:
        user = get_user_from_email(email)
    except EmailNotRegistered:
        # User doesn't exist, create new user
        user = create_new_user(email, claims)
        add_user_log(
            event, user.user_id, f"User {claims['email']} created", claims=claims
        )

    send_welcome_email(user)
    sid = str(uuid.uuid4())
    now = int(time.time())
    session = {
        SID: sid,
        "email": email,
        A.SESSION_CREATED: now,
        A.SESSION_EXPIRE: now + SESSION_TTL_SECS,
        A.TTL: now + SESSION_TTL_SECS,
        A.SESSION_LAST_AUTHENTICATED: now,
        A.SESSION_COOKIE_SCOPE: COOKIE_NAME,
        "client_ip": client_ip,
        "claims": claims,
    }
    ret = sessions_table.put_item(Item=session)
    LOGGER.debug(
        "new_session table=%s user=%s session=%s ret=%s",
        sessions_table,
        user,
        session,
        ret,
    )
    add_user_log(event, user.user_id, f"Session {sid} created")
    return Session(**session)


def get_session_from_sid(event, sid) -> Session | None:
    LOGGER.debug(
        "get_session_from_sid sid=%s get_cookie_domain(%s)=%s",
        sid,
        event,
        get_cookie_domain(event),
    )
    if not sid:
        return None
    resp = sessions_table.get_item(Key={SID: sid}, ConsistentRead=True)
    LOGGER.debug("get_session sid=%s resp=%s", sid, resp)
    item = resp.get("Item")
    if item is None or item.get(A.SESSION_COOKIE_SCOPE) != COOKIE_NAME:
        # A new cookie name cannot make an old, potentially disclosed SID safe.
        return None
    ses = Session(**convert_dynamodb_item(item))
    now = int(time.time())
    if not ses:
        LOGGER.debug("get_session no ses")
        return None
    if ses.session_expire <= now:
        expire_batch(now, [item])
        return None
    # A conditional update cannot recreate a logged-out or concurrently expired session.
    expiration = now + SESSION_TTL_SECS
    try:
        sessions_table.update_item(
            Key={SID: sid},
            UpdateExpression="SET session_expire = :expiration, #ttl = :expiration, "
            "session_last_authenticated = :now",
            ConditionExpression="attribute_exists(sid) AND session_expire > :now",
            ExpressionAttributeNames={"#ttl": A.TTL},
            ExpressionAttributeValues={":expiration": expiration, ":now": now},
        )
    except ClientError as error:
        if error.response.get(ERROR, {}).get(CODE) != "ConditionalCheckFailedException":
            raise
        return None
    ses.session_expire = expiration
    CURRENT_SESSION.set(ses)
    return ses


def get_session_from_event(event) -> Session | None:
    """Return the session dictionary if the session is valid and not expired.
    Sessions are determined by having the session cookie"""
    return get_session_from_sid(event, parse_cookies(event).get(COOKIE_NAME))


def all_sessions_for_email(email):
    """Return all of the sessions for an email address"""
    resp = sessions_table.query(
        IndexName="GSI_Email",
        KeyConditionExpression="email = :e",
        ExpressionAttributeValues={":e": email},
    )
    sessions = resp["Items"]
    return sessions


def delete_session(sid):
    LOGGER.info("delete_session sid=%s", sid)
    return sessions_table.delete_item(Key={SID: sid})


def delete_session_from_event(event):
    """Delete the session, whether it exists or not"""
    sid = parse_cookies(event).get(COOKIE_NAME)
    if sid:
        return delete_session(sid)
    return None


def expire_batch(now: int, items: list) -> int:
    """Delete expired rows only if they have not been renewed since the scan."""
    deleted = 0
    for item in items:
        if int(item.get(A.SESSION_EXPIRE) or 0) > now:
            continue
        try:
            sessions_table.delete_item(
                Key={SID: item[SID]},
                ConditionExpression="attribute_exists(sid) AND "
                "(attribute_not_exists(session_expire) OR session_expire <= :now)",
                ExpressionAttributeValues={":now": now},
            )
            deleted += 1
        except ClientError as error:
            if (
                error.response.get(ERROR, {}).get(CODE)
                != "ConditionalCheckFailedException"
            ):
                raise
    return deleted
