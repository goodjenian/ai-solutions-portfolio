"""Pytest configuration for unit API tests.

Sets environment variables before any test modules are imported.
This ensures that TestClient(app) is created with the correct settings.
"""

import os

# Must be set before importing app in test modules
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("API_ACCESS_KEY", "dev-secret-key")
