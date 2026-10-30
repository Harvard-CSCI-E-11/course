"""Verify release diagnostics and build provenance without contacting AWS.

Temporary Git fixtures exercise clean, dirty and detached checkout states.
The build stamper writes the same typed JSON consumed by deployed packages.
Runtime checks use real temporary artifacts and selected environment settings.
Public text must preserve provenance while excluding unrelated secret data.
Project and lock versions are checked against the shared runtime release.
"""

import subprocess
import sys
import tomllib
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from e11.e11admin.build_info import capture_build_info
from e11.version import DEPLOYMENT_ENV, STAGE_ENV, BuildInfo, __version__, version_info


@pytest.fixture
def checkout(tmp_path):
    """Create disposable fixture history, independent of agent publication commits."""
    directory = tmp_path / "checkout"
    subprocess.run(["git", "init", "-b", "fixture", str(directory)], capture_output=True, check=True)
    (directory / "source").write_text("fixture\n")
    subprocess.run(["git", "-C", str(directory), "add", "source"], check=True)
    subprocess.run(["git", "-C", str(directory), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                    "-c", "commit.gpgsign=false", "commit", "-m", "fixture"], capture_output=True, check=True)
    return directory


def test_capture_tracks_clean_dirty_and_detached_checkout(checkout):
    clean = capture_build_info(checkout)
    assert len(clean.git_commit) == 40
    assert clean.git_checkout == "fixture"
    assert clean.git_dirty is False
    assert datetime.fromisoformat(clean.build_timestamp).utcoffset() == timedelta(0)
    (checkout / "untracked").write_text("new content\n")
    assert capture_build_info(checkout).git_dirty is True
    subprocess.run(["git", "-C", str(checkout), "checkout", "--detach"], capture_output=True, check=True)
    detached = capture_build_info(checkout)
    assert detached.git_checkout == "detached"
    assert detached.git_commit == clean.git_commit


def test_stamper_artifact_retains_provenance_after_checkout_changes(checkout, tmp_path_factory):
    output = tmp_path_factory.mktemp("artifact") / "_build_info.json"
    subprocess.run([sys.executable, "-m", "e11.e11admin.build_info", "--directory", str(checkout), "--output", str(output)], check=True)
    built = BuildInfo.model_validate_json(output.read_text())
    (checkout / "source").write_text("later edit\n")
    assert capture_build_info(checkout).git_dirty is True
    assert version_info(output).git_dirty is False
    assert version_info(output).git_commit == built.git_commit


def test_non_git_sources_report_unknown_provenance(tmp_path):
    info = capture_build_info(tmp_path)
    assert info.git_commit == info.git_checkout == "unknown"
    assert info.git_dirty is None
    assert version_info(tmp_path / "missing.json").git_commit == "unknown"


@pytest.mark.parametrize("environment", ["prod", "stage"])
def test_public_runtime_details_are_allowlisted(tmp_path, monkeypatch, environment):
    artifact = tmp_path / "_build_info.json"
    artifact.write_text('{"git_commit":"abc123","git_checkout":"release","git_dirty":false,"secret":"PRIVATE_SENTINEL"}')
    monkeypatch.setenv(STAGE_ENV, environment)
    monkeypatch.setenv(DEPLOYMENT_ENV, "2026-10-30T12:00:00Z")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "PRIVATE_SENTINEL")
    info = version_info(artifact)
    text = info.text()
    assert text.startswith("version: 1.1.0a1\n")
    assert f"environment: {environment}\n" in text
    assert f"python: {info.python}\n" in text
    assert "deployed: 2026-10-30T12:00:00Z\n" in text
    assert "PRIVATE_SENTINEL" not in text
    assert str(tmp_path) not in text


def test_release_and_lock_versions_match_runtime():
    root = Path(__file__).resolve().parents[1]
    for project in (root, root / "lambda-home", root / "lambda-leaderboard"):
        config = tomllib.loads((project / "pyproject.toml").read_text())
        assert config["project"]["version"] == __version__
        lock = tomllib.loads((project / "uv.lock").read_text())
        relevant = [p for p in lock["package"] if p["name"] in ("e11", config["project"]["name"])]
        assert relevant and all(p["version"] == __version__ for p in relevant)
