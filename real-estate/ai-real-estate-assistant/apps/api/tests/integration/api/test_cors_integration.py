import os
import sys

import pytest
from fastapi.testclient import TestClient

# Import app separately to avoid dependency issues in other tests
try:
    from api.main import app

    def test_cors_dev_environment_allows_all_origin_header():
        client = TestClient(app)
        r = client.get("/health", headers={"Origin": "http://example.com"})
        assert r.status_code == 200
        assert r.headers.get("access-control-allow-origin") == "*"
        exposed = (r.headers.get("access-control-expose-headers") or "").lower()
        assert "x-request-id" in exposed

except ImportError:
    # If langchain or other dependencies are missing, skip this test
    def test_cors_dev_environment_allows_all_origin_header():
        pytest.skip("Skipping: langchain dependencies not available")


def test_production_wildcard_cors_fails_during_app_initialization():
    """
    Integration test: Verify that the application fails to initialize
    when ENVIRONMENT=production and CORS_ALLOW_ORIGINS contains wildcard '*'.

    This test ensures the production safety validator is properly wired
    and prevents accidental deployment with overly permissive CORS.
    The validation error is raised during module import (fail-fast behavior).
    """
    # Save original environment values
    old_env = os.environ.get("ENVIRONMENT")
    old_cors = os.environ.get("CORS_ALLOW_ORIGINS")

    try:
        # Set production environment with wildcard CORS (invalid configuration)
        os.environ["ENVIRONMENT"] = "production"
        os.environ["CORS_ALLOW_ORIGINS"] = "*"

        # Remove the settings module from cache to force reload with new env vars
        if "config.settings" in sys.modules:
            del sys.modules["config.settings"]

        # Attempting to import the settings module should raise ValidationError
        # (the module-level settings = AppSettings() is executed on import)
        try:
            import config.settings  # noqa: F401

            pytest.fail(
                "Expected ValidationError when importing config.settings with production + wildcard CORS"
            )
        except Exception as e:
            # The error is a pydantic ValidationError wrapping our ValueError
            error_msg = str(e).lower()
            assert "cannot contain wildcard '*'" in error_msg or "validation error" in error_msg

    finally:
        # Restore original environment variables
        if old_env is None:
            os.environ.pop("ENVIRONMENT", None)
        else:
            os.environ["ENVIRONMENT"] = old_env
        if old_cors is None:
            os.environ.pop("CORS_ALLOW_ORIGINS", None)
        else:
            os.environ["CORS_ALLOW_ORIGINS"] = old_cors

        # Clear module cache to restore original configuration
        if "config.settings" in sys.modules:
            del sys.modules["config.settings"]
        if "config" in sys.modules:
            del sys.modules["config"]
