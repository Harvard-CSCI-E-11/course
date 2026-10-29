# Exercise the repository hook with a real isolated Git index.
# Fully staged files are normalized by the existing whitespace helper.
# Partially staged files retain their exact selected and unselected content.
# Helper failures must stop the hook instead of silently allowing a commit.
# Tests create no commits and never modify the course checkout's Git index.
"""Commit-hook regression checks for staging boundaries and failures."""

import shutil
import subprocess
from pathlib import Path

import pytest


def test_hook_preserves_partial_staging_and_normalizes_fully_staged_files(tmp_path):
    repository = Path(__file__).resolve().parents[3]
    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True)
    helper = tmp_path / "etc/fix_trailing_whitespace.py"
    helper.parent.mkdir()
    shutil.copy2(repository / "etc/fix_trailing_whitespace.py", helper)
    partial = tmp_path / "partial.txt"
    full = tmp_path / "full.txt"
    partial.write_text("selected  \n")
    full.write_text("normalize  \n")
    subprocess.run(["git", "add", "partial.txt", "full.txt"], cwd=tmp_path, check=True)
    partial.write_text("unselected  \n")
    subprocess.run([str(repository / ".githooks/pre-commit")], cwd=tmp_path, check=True)
    selected = subprocess.run(["git", "show", ":partial.txt"], cwd=tmp_path, capture_output=True, text=True, check=True)
    normalized = subprocess.run(["git", "show", ":full.txt"], cwd=tmp_path, capture_output=True, text=True, check=True)
    assert selected.stdout == "selected  \n"
    assert partial.read_text() == "unselected  \n"
    assert normalized.stdout == full.read_text() == "normalize\n"


def test_hook_failure_stops_before_staging_changes(tmp_path):
    repository = Path(__file__).resolve().parents[3]
    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True)
    path = tmp_path / "selected.txt"
    path.write_text("selected  \n")
    subprocess.run(["git", "add", path.name], cwd=tmp_path, check=True)
    with pytest.raises(subprocess.CalledProcessError):
        subprocess.run([str(repository / ".githooks/pre-commit")], cwd=tmp_path, check=True, capture_output=True)
    selected = subprocess.run(["git", "show", ":selected.txt"], cwd=tmp_path, capture_output=True, text=True, check=True)
    assert selected.stdout == "selected  \n"
