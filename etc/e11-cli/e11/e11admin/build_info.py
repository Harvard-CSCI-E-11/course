"""Stamp source provenance into the shared package before building its wheel.

Make invokes this module for each Lambda vendoring operation.
Git supplies a commit, checkout ref and tracked/untracked working-tree state.
The JSON artifact contains only public provenance, never paths or credentials.
Its UTC timestamp describes the build rather than a later deployment checkout.
Non-Git source distributions retain unknown Git fields instead of failing.
"""

import argparse
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from e11.version import BUILD_INFO_FILE, UNKNOWN, BuildInfo


def capture_build_info(directory: Path) -> BuildInfo:
    """Capture Git facts once, preserving an honest unknown when unavailable."""
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

    def git(*args: str) -> str:
        return subprocess.check_output(["git", "-C", str(directory), *args],
                                       text=True, stderr=subprocess.DEVNULL).strip()

    try:
        commit = git("rev-parse", "HEAD")
        checkout = git("rev-parse", "--abbrev-ref", "HEAD")
        if checkout == "HEAD":
            checkout = "detached"
        dirty = bool(git("status", "--porcelain", "--untracked-files=normal"))
    except (OSError, subprocess.CalledProcessError):
        commit, checkout, dirty = UNKNOWN, UNKNOWN, None
    return BuildInfo(git_commit=commit, git_checkout=checkout, git_dirty=dirty,
                     build_timestamp=timestamp)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path, default=BUILD_INFO_FILE)
    args = parser.parse_args()
    data = capture_build_info(args.directory).model_dump_json(indent=2) + "\n"
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=args.output.parent, suffix=".json", delete=False) as output:
            temporary = Path(output.name)
            output.write(data)
        temporary.replace(args.output)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
