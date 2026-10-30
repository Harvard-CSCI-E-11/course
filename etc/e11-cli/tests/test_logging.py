"""Check the shared AWS SDK logging policy without contacting AWS.

Each case starts a fresh Python process to exercise package initialization.
Real SDK descendant loggers emit messages at DEBUG, INFO and WARNING.
Root logging varies independently from application LOG_LEVEL=DEBUG.
Captured output must retain useful SDK messages and application diagnostics.
The tests ensure SDK DEBUG stays silent without mocking logging or clients.
"""

import os
import subprocess
import sys

import pytest

LOG_LEVEL_ENV = "LOG_LEVEL"


@pytest.mark.parametrize("root_level", ["INFO", "DEBUG"])
def test_sdk_debug_stays_silent_with_application_debug(root_level):
    script = f"""
import logging
logging.basicConfig(level=logging.{root_level})
from e11.e11core.utils import get_logger
for name in ("boto3.resources.factory", "botocore.endpoint"):
    logger = logging.getLogger(name)
    logger.debug("SDK_DEBUG")
    logger.info("SDK_INFO")
    logger.warning("SDK_WARNING")
get_logger("logging-policy").debug("APPLICATION_DEBUG")
"""
    env = os.environ.copy()
    env[LOG_LEVEL_ENV] = "DEBUG"
    result = subprocess.run([sys.executable, "-c", script], env=env,
                            capture_output=True, text=True, check=True)
    assert "SDK_DEBUG" not in result.stderr
    assert result.stderr.count("SDK_INFO") == 2
    assert result.stderr.count("SDK_WARNING") == 2
    assert "APPLICATION_DEBUG" in result.stderr
