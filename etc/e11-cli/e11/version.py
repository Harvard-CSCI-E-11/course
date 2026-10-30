"""Describe the packaged release and its public build/runtime provenance.

Lambda builds embed a small JSON record beside this module before vendoring.
Runtime diagnostics read that artifact rather than invoking Git in Lambda.
Only explicit public fields are rendered; configuration and secrets stay private.
The same renderer serves both version aliases without request-specific values.
Source checkouts without a stamped artifact report unknown build provenance.
"""

import os
import platform
from pathlib import Path

from pydantic import BaseModel, Field

__version__ = "1.1.0a1"
BUILD_INFO_FILE = Path(__file__).with_name("_build_info.json")
UNKNOWN = "unknown"
STAGE_ENV = "STAGE_NAME"
DEPLOYMENT_ENV = "DEPLOYMENT_TIMESTAMP"
CONTENT_TYPE_HEADER = "Content-Type"
CACHE_CONTROL_HEADER = "Cache-Control"
NOSNIFF_HEADER = "X-Content-Type-Options"
VERSION_HEADERS = {CONTENT_TYPE_HEADER: "text/plain; charset=utf-8",
                   CACHE_CONTROL_HEADER: "no-store", NOSNIFF_HEADER: "nosniff"}


class BuildInfo(BaseModel):
    """The source checkout captured when the shared wheel was built."""

    git_commit: str = UNKNOWN
    git_checkout: str = UNKNOWN
    git_dirty: bool | None = None
    build_timestamp: str = UNKNOWN


class VersionInfo(BuildInfo):
    """Allowlisted release, build and runtime facts safe for public display."""

    version: str = __version__
    python: str = Field(default_factory=platform.python_version)
    architecture: str = Field(default_factory=platform.machine)
    environment: str = UNKNOWN
    deployment_timestamp: str = UNKNOWN

    def text(self) -> str:
        """Return stable plain text shared by the two route aliases."""
        dirty = UNKNOWN if self.git_dirty is None else "dirty" if self.git_dirty else "clean"
        return (f"version: {self.version}\n"
                f"git checkout: {self.git_checkout}\n"
                f"git commit: {self.git_commit}\n"
                f"working tree: {dirty}\n"
                f"python: {self.python}\n"
                f"architecture: {self.architecture}\n"
                f"environment: {self.environment}\n"
                f"built: {self.build_timestamp}\n"
                f"deployed: {self.deployment_timestamp}\n")


def version_info(build_file: Path = BUILD_INFO_FILE) -> VersionInfo:
    """Combine immutable packaged provenance with selected runtime properties."""
    try:
        build = BuildInfo.model_validate_json(build_file.read_text())
    except (OSError, ValueError):
        build = BuildInfo()
    return VersionInfo(**build.model_dump(), environment=os.getenv(STAGE_ENV, UNKNOWN),
                       deployment_timestamp=os.getenv(DEPLOYMENT_ENV, UNKNOWN))
