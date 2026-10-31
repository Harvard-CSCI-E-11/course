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
from e11.version import BUILD_INFO_FILE, BuildInfo, __version__

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
    checks = [ArtifactCheck(app="lambda-home", function="E11HomeFunction", body_prefix=f"version: {__version__}\n"),
              ArtifactCheck(app="lambda-leaderboard", function="LeaderboardFlaskFunction", body_prefix=f"version: {__version__}\n")]
    build = BuildInfo.model_validate_json(BUILD_INFO_FILE.read_text())
    root = Path(__file__).resolve().parents[2]
    env = dict(os.environ)
    for name in ("AWS_PROFILE", "AWS_DEFAULT_PROFILE", "AWS_SESSION_TOKEN"):
        env.pop(name, None)
    env.update(AWS_ACCESS_KEY_ID="test", AWS_SECRET_ACCESS_KEY="test", AWS_DEFAULT_REGION="us-east-1",
               AWS_EC2_METADATA_DISABLED="true", SAM_CLI_TELEMETRY="0")
    with tempfile.TemporaryDirectory(prefix="e11-lambda-smoke-") as temporary:
        directory = Path(temporary)
        for check in checks:
            first_body = None
            for path in ("/ver", "/version"):
                event = {VERSION: "2.0", ROUTE_KEY: "ANY /{proxy+}", RAW_PATH: path, RAW_QUERY_STRING: "", HEADERS: {HOST: "localhost"},
                         REQUEST_CONTEXT: {STAGE: "$default", HTTP: {METHOD: "GET", PATH: path, SOURCE_IP: "127.0.0.1", PROTOCOL: "HTTP/1.1"}}}
                event_file = directory / "event.json"
                event_file.write_text(json.dumps(event))
                log_file = root / check.app / ".aws-sam" / "smoke.log"
                result = subprocess.run(["sam", "local", "invoke", check.function, "--template", ".aws-sam/build/template.yaml",
                                         "--event", str(event_file), "--log-file", str(log_file)],
                                        cwd=root / check.app, env=env, capture_output=True, text=True, check=True)
                response = parse_response(log_file.read_text() + "\n" + result.stdout)
                if (response.status_code != 200 or not response.body.startswith(check.body_prefix)
                        or f"git commit: {build.git_commit}\n" not in response.body
                        or (first_body is not None and response.body != first_body)):
                    raise RuntimeError(f"Bundled version alias/provenance check failed: {check.app} {path}")
                first_body = response.body
            print(f"{check.app}: Linux arm64 /ver and /version returned identical HTTP 200 build/runtime reports")


if __name__ == "__main__":
    main()
