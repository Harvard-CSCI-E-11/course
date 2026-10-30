"""Smoke-test the actual Linux arm64 SAM deployment bundles locally.

Make builds both functions from uv-exported runtime requirements first.
This check invokes each bundled handler through SAM's Lambda container runtime.
Only their public version routes run; grading, login and email are not invoked.
Dummy AWS credentials prevent accidental access to production resources.
Events are temporary; diagnostic logs remain in each app's ignored .aws-sam folder.
Successful imports and HTTP responses catch dependencies hidden by dev venvs.
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path

from pydantic import BaseModel, Field

VERSION = "version"
ROUTE_KEY = "routeKey"
RAW_PATH = "rawPath"
RAW_QUERY_STRING = "rawQueryString"
HEADERS = "headers"
HOST = "host"
REQUEST_CONTEXT = "requestContext"
HTTP = "http"
METHOD = "method"
PATH = "path"
SOURCE_IP = "sourceIp"
PROTOCOL = "protocol"
STAGE = "stage"
STATUS_CODE = "statusCode"
BODY = "body"


class ArtifactCheck(BaseModel):
    """One bundle's public route and its expected version-response prefix."""

    app: str
    function: str
    path: str
    body_prefix: str


class VersionResponse(BaseModel):
    """The actual HTTP response emitted by a bundled Lambda handler."""

    status_code: int = Field(alias=STATUS_CODE)
    body: str


def parse_response(output: str) -> VersionResponse:
    """SAM redirects the response along with function logs under --log-file."""
    response = None
    for line in output.splitlines():
        try:
            response = VersionResponse.model_validate_json(line)
        except ValueError:
            continue
    if response is None:
        raise RuntimeError("No HTTP response in the Lambda smoke log")
    return response


def main():
    checks = [ArtifactCheck(app="lambda-home", function="E11HomeFunction", path="/version", body_prefix="version:"),
              ArtifactCheck(app="lambda-leaderboard", function="LeaderboardFlaskFunction", path="/ver", body_prefix="1.")]
    root = Path(__file__).resolve().parents[2]
    env = dict(os.environ)
    for name in ("AWS_PROFILE", "AWS_DEFAULT_PROFILE", "AWS_SESSION_TOKEN"):
        env.pop(name, None)
    env.update(AWS_ACCESS_KEY_ID="test", AWS_SECRET_ACCESS_KEY="test", AWS_DEFAULT_REGION="us-east-1",
               AWS_EC2_METADATA_DISABLED="true", SAM_CLI_TELEMETRY="0")
    with tempfile.TemporaryDirectory(prefix="e11-lambda-smoke-") as temporary:
        directory = Path(temporary)
        for check in checks:
            event = {VERSION: "2.0", ROUTE_KEY: "ANY /{proxy+}", RAW_PATH: check.path, RAW_QUERY_STRING: "", HEADERS: {HOST: "localhost"},
                     REQUEST_CONTEXT: {STAGE: "$default", HTTP: {METHOD: "GET", PATH: check.path, SOURCE_IP: "127.0.0.1", PROTOCOL: "HTTP/1.1"}}}
            event_file = directory / "event.json"
            event_file.write_text(json.dumps(event))
            log_file = root / check.app / ".aws-sam" / "smoke.log"
            result = subprocess.run(["sam", "local", "invoke", check.function, "--template", ".aws-sam/build/template.yaml",
                                     "--event", str(event_file), "--log-file", str(log_file)],
                                    cwd=root / check.app, env=env, capture_output=True, text=True, check=True)
            response = parse_response(log_file.read_text() + "\n" + result.stdout)
            if response.status_code != 200 or not response.body.startswith(check.body_prefix):
                raise RuntimeError(f"Bundled handler smoke check failed: {check.app}")
            print(f"{check.app}: Linux arm64 handler imported and version route returned HTTP 200")


if __name__ == "__main__":
    main()
