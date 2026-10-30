"""
Fast import checks for the prepared Lambda source tree.
Make installs the shared e11 package into src before these checks run.
The development environment supplies dependencies and testing tools here.
These checks catch import refactors without claiming artifact compatibility.
The separate lambda-build-check target verifies actual Linux arm64 bundles.
Run vend-e11 first so that the prepared package exists.
"""

import sys
from pathlib import Path


def _setup_bundle_path():
    """Add the bundle source root used by normal Lambda package imports."""
    bundle_path = Path(__file__).parent.parent / "src"

    if not (bundle_path / "e11" / "__init__.py").exists():
        raise FileNotFoundError(
            f"Vendored e11 package not found in {bundle_path}. "
            "Run 'make vend-e11' first to install the package."
        )

    bundle_str = str(bundle_path)
    if bundle_str not in sys.path:
        sys.path.insert(0, bundle_str)


def test_lambda_handler_imports():
    """
    Test that the Lambda handler module can be imported the way AWS Lambda does.

    AWS Lambda imports: home_app.home.lambda_handler
    This will fail if any imports in home.py are broken (e.g., the S3_BUCKET import issue).
    """
    _setup_bundle_path()

    # Import the Lambda handler module the way AWS Lambda does
    # This will trigger all imports in home.py, including the problematic grader import
    import home_app.home  # pylint: disable=import-outside-toplevel

    # Verify the lambda_handler function exists
    assert hasattr(home_app.home, "lambda_handler")
    assert callable(home_app.home.lambda_handler)


def test_grader_imports_s3_bucket_correctly():
    """
    Specifically test that grader.py can import S3_BUCKET correctly.

    This was the original bug - grader.py was trying to import S3_BUCKET
    from e11.e11core.constants, but it's actually in e11.e11_common.
    """
    _setup_bundle_path()

    # Import grader module - this will fail if S3_BUCKET import is broken
    from e11.e11core import grader  # pylint: disable=import-outside-toplevel

    assert grader is not None

    # Verify that constants module doesn't have S3_BUCKET (it shouldn't)
    from e11.e11core import constants  # pylint: disable=import-outside-toplevel

    assert not hasattr(constants, "S3_BUCKET"), (
        "S3_BUCKET should not be in e11.e11core.constants. "
        "It should be imported from e11.e11_common in grader.py"
    )

    # Verify that e11_common has S3_BUCKET and compare to the constant
    import e11.e11_common as e11_common_module  # pylint: disable=import-outside-toplevel
    from e11.e11_common import S3_BUCKET  # pylint: disable=import-outside-toplevel

    # Compare imported value to the constant from the module (avoiding hard-coded strings)
    assert S3_BUCKET is not None
    assert S3_BUCKET == e11_common_module.S3_BUCKET
