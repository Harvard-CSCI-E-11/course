"""
Common includes for lambda-home.
"""

import os
import sys
from os.path import dirname, isdir, join

from e11 import e11_common

users_table = e11_common.users_table

# Authentication cookies are host-only; the prefix also blocks subdomain injection.
SESSION_TTL_SECS = 120 * 24 * 60 * 60
COOKIE_NAME = "__Host-AuthSid"
LEGACY_COOKIE_NAME = "AuthSid"
COOKIE_SECURE = True
COOKIE_SAMESITE = os.environ.get("COOKIE_SAMESITE", "Lax")  # Lax|Strict|None

# fix the path. Don't know why this is necessary
MY_DIR = dirname(__file__)
sys.path.append(MY_DIR)
NESTED = join(MY_DIR, ".aws-sam", "build", "E11HomeFunction")
if isdir(join(NESTED, "e11")):
    sys.path.insert(0, NESTED)
# path fixing done

TEMPLATE_DIR = join(MY_DIR, "templates")
STATIC_DIR = join(MY_DIR, "static")


################################################################
## Add to user log
# Staging environment configuration
def is_staging_environment(event) -> bool:
    """Detect if we're running in the staging environment"""
    stage = event.get("requestContext", {}).get("stage", "")
    return stage == "stage"


def make_cookie(
    name: str,
    value: str,
    max_age: int = SESSION_TTL_SECS,
    clear: bool = False,
    domain=None,
) -> str:
    """create a cookie for Lambda"""
    parts = [f"{name}={'' if clear else value}"]
    if domain and not name.startswith("__Host-"):
        parts.append(f"Domain={domain}")
    parts.append("Path=/")
    if COOKIE_SECURE:
        parts.append("Secure")
    parts.append("HttpOnly")
    parts.append(f"SameSite={COOKIE_SAMESITE}")
    if clear:
        parts.append("Max-Age=0")
        parts.append("Expires=Thu, 01 Jan 1970 00:00:00 GMT")
    else:
        parts.append(f"Max-Age={max_age}")
    return "; ".join(parts)


def get_cookie_domain(_event) -> None:
    """Omit Domain so the browser confines cookies to the exact issuing host."""
    return


def get_request_host(event) -> str | None:
    """Get the request host from the event (e.g. stage.csci-e-11.org or csci-e-11.org).
    Used for OAuth redirect_uri so users return to the same host they started from."""
    headers = event.get("headers") or {}
    host = headers.get("host") or headers.get("Host")
    if host:
        return str(host).split(":", maxsplit=1)[0].strip()
    return event.get("requestContext", {}).get("domainName")


def get_public_host(event=None) -> str | None:
    """Return the configured public host for this stack, falling back to the request host."""
    if host := os.environ.get("PUBLIC_DOMAIN_NAME"):
        return host.strip()
    if event is None:
        return None
    return get_request_host(event)
