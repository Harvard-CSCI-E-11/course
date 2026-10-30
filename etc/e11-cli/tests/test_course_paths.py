# Verify that installation, grading, services, and key lookup share a checkout.
# The documented student directory is /home/ubuntu/course, independent of version.
# Remote contexts must target real files in that directory rather than a repo label.
# Service configurations are checked as consumers of the same runtime contract.
# A subprocess verifies that an explicit local override beats an existing default.
"""Regression checks for the documented student checkout layout."""

import configparser
import os
import subprocess
import sys
from pathlib import Path

from e11.e11core import constants
from e11.e11core.context import build_ctx


def test_remote_grading_and_services_use_documented_checkout():
    root = Path("/home/ubuntu/course")
    assert build_ctx("lab1", for_instance=True).labdir == str(root / "lab1")
    assert constants.GITHUB_REPO_URL == "https://github.com/Harvard-CSCI-E-11/course"
    repository = Path(__file__).resolve().parents[3]
    services = [(repository / lab / f"{lab}.service", lab) for lab in ["lab4", "lab5", "lab6"]]
    services += [(repository / "lab3" / name, "lab3") for name in
                 ["lab3.service-simple_flask_application", "lab3.service-student_server"]]
    services.append((repository / "etc/template.service", "$LAB"))
    for path, lab in services:
        service = configparser.ConfigParser(interpolation=None)
        service.read(path)
        assert service["Service"]["WorkingDirectory"] == str(root / lab)
        assert service["Service"]["ExecStart"].split()[0] == str(root / lab / ".venv/bin/gunicorn")


def test_explicit_course_root_overrides_existing_default(tmp_path):
    (tmp_path / "course").mkdir(exist_ok=True)
    selected = tmp_path / "selected-checkout"
    environment = {**os.environ, "HOME": str(tmp_path), "COURSE_ROOT": str(selected)}
    result = subprocess.run([sys.executable, "-c", "from e11.e11core.constants import COURSE_ROOT; print(COURSE_ROOT)"],
                            env=environment, capture_output=True, text=True, check=True)
    assert result.stdout.strip() == str(selected)


def test_legacy_checkout_remains_usable_until_canonical_checkout_exists(tmp_path):
    isolated_home = tmp_path / "legacy-home"
    isolated_home.mkdir()
    legacy = isolated_home / "spring26"
    legacy.mkdir()
    environment = {**os.environ, "HOME": str(isolated_home)}
    environment.pop("COURSE_ROOT", None)
    command = [sys.executable, "-c", "from e11.e11core.constants import COURSE_ROOT; print(COURSE_ROOT)"]
    result = subprocess.run(command, env=environment, capture_output=True, text=True, check=True)
    assert result.stdout.strip() == str(legacy)
    canonical = isolated_home / "course"
    canonical.mkdir()
    result = subprocess.run(command, env=environment, capture_output=True, text=True, check=True)
    assert result.stdout.strip() == str(canonical)


def test_installer_initializes_lab3_relative_to_checkout(tmp_path):
    repository = Path(__file__).resolve().parents[3]
    installer = repository / "etc/install-e11"
    subprocess.run(["bash", "-n", str(installer)], check=True)
    setup = next(line for line in installer.read_text().splitlines() if 'cp -p simple_flask_application.py server.py' in line)
    checkout = tmp_path / "arbitrary-checkout"
    lab = checkout / "lab3"
    lab.mkdir(parents=True)
    (checkout / "etc").mkdir()
    (lab / "simple_flask_application.py").write_text("application")
    subprocess.run(["bash", "-euc", setup], env={**os.environ, "SCRIPT_DIR": str(checkout / "etc")}, check=True)
    assert (lab / "server.py").read_text() == "application"
