"""Check that Make's SAM wrapper preserves complete deployment configuration.

These tests exercise config precedence, empty values and argument boundaries.
A temporary SAM executable captures the real subprocess invocation safely.
It never contacts AWS or performs a deployment.
The existing production and staging TOML files are also checked directly.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from e11.e11admin import lambda_build_check, sam_deploy


def test_config_precedence_and_quoted_values(tmp_path):
    config = tmp_path / "samconfig.toml"
    config.write_text('''version = 0.1
[default.global.parameters]
parameter_overrides = 'EnvironmentName="stage"'
[default.deploy.parameters]
parameter_overrides = 'EnvironmentName="prod" CertificateArn="" Note="two words" DeploymentTimestamp="old"'
''')
    deployment = sam_deploy.Deployment.load(config, tmp_path / "bundle.yaml", "2026-10-30T00:00:00Z")
    command = deployment.command()
    values = {key: json.loads(value) for key, value in (arg.split("=", 1) for arg in command[command.index("--parameter-overrides") + 1:])}
    assert values == {"EnvironmentName": "prod", "CertificateArn": "", "Note": "two words", "DeploymentTimestamp": "2026-10-30T00:00:00Z"}


@pytest.mark.parametrize("app,environment,count", [("lambda-home", "prod", 10), ("lambda-home", "stage", 10), ("lambda-leaderboard", "prod", 7)])
def test_checked_in_configs_keep_their_parameters(app, environment, count):
    root = Path(__file__).resolve().parents[1] / app
    deployment = sam_deploy.Deployment.load(root / f"samconfig-{environment}.toml", root / "template.yaml")
    assert len(deployment.parameters) == count
    assert deployment.parameters["EnvironmentName"] == environment
    assert deployment.parameters["CertificateArn"] == ""
    assert deployment.parameters["UsersTableName"] == "e11-users"
    assert deployment.parameters[sam_deploy.TIMESTAMP].endswith("Z")


def test_wrapper_executes_without_shell_reinterpretation(tmp_path):
    config = tmp_path / "samconfig.toml"
    config.write_text('''[default.deploy.parameters]
parameter_overrides = 'Note="$(false); still one value" CertificateArn=""'
''')
    executable = tmp_path / "sam"
    capture = tmp_path / "args.json"
    executable.write_text(f'''#!/usr/bin/env python3
# Capture a SAM-wrapper invocation during a unit test.
# This executable replaces the AWS command only inside a temporary PATH.
# Arguments are recorded as JSON for boundary and quoting assertions.
# It has no AWS access and performs no deployment.
# The temporary test directory owns and removes its output.
import json,sys
with open({str(capture)!r}, "w") as output:
    json.dump(sys.argv[1:], output)
''')
    executable.chmod(0o755)
    subprocess.run([sys.executable, sam_deploy.__file__, "--config", str(config), "--template", str(tmp_path / "template.yaml")],
                   env={**os.environ, "PATH": str(tmp_path) + os.pathsep + os.environ["PATH"]}, check=True)
    arguments = json.loads(capture.read_text())
    assert 'Note="$(false); still one value"' in arguments
    assert 'CertificateArn=""' in arguments


def test_invalid_override_stops_before_sam(tmp_path):
    config = tmp_path / "bad.toml"
    config.write_text('[default.deploy.parameters]\nparameter_overrides = "missing-equals"\n')
    with pytest.raises(ValueError, match="Invalid SAM"):
        sam_deploy.Deployment.load(config, tmp_path / "template.yaml")


def test_smoke_response_parser_ignores_logs_and_detects_missing_http():
    response = lambda_build_check.parse_response('START\n{"statusCode":500,"body":"first"}\nREPORT\n{"statusCode":200,"body":"version: test"}')
    assert response.status_code == 200 and response.body == "version: test"
    with pytest.raises(RuntimeError, match="No HTTP response"):
        lambda_build_check.parse_response('START\n{"errorType":"Runtime.ImportModuleError"}\nEND')
