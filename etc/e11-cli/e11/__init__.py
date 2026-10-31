"""Initialize the shared package used by the CLI and both Lambda applications.

Package import establishes the AWS SDK logging policy before clients are used.
SDK child loggers inherit INFO, suppressing verbose request/debug diagnostics.
Application loggers retain their independently configured LOG_LEVEL setting.
Root DEBUG logging, including pytest diagnostics, does not enable SDK DEBUG.
"""

import logging

logging.getLogger("boto3").setLevel(logging.INFO)
logging.getLogger("botocore").setLevel(logging.INFO)
