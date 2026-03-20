from __future__ import annotations

import os  # noqa: E402
import sys  # noqa: E402
from pathlib import Path
from unittest.mock import patch

# noqa: E501
# Add project root to Python path for scripts imports (top-level, before any test imports)
# From apps/api/tests/unit/ to project root: 4 levels up
_project_root = Path(__file__).resolve().parents[4]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from scripts.start import (  # noqa: E402
    _build_backend_env,
    _build_frontend_env,
    _get_default_api_access_key_from_env,
    main,
)


def test_get_default_api_access_key_from_env_prefers_primary_key() -> None:
    with patch.dict(
        os.environ,
        {"API_ACCESS_KEY": "primary", "API_ACCESS_KEYS": "rot1,rot2"},
        clear=True,
        # noqa: E501
    ):
        assert _get_default_api_access_key_from_env() == "primary"


def test_get_default_api_access_key_from_env_falls_back_to_rotated_keys() -> None:
    with patch.dict(
        os.environ,
        {"API_ACCESS_KEY": "   ", "API_ACCESS_KEYS": " rot1 , rot2 "},
        clear=True,
        # noqa: E501
    ):
        assert _get_default_api_access_key_from_env() == "rot1"


def test_build_backend_env_defaults_dev_key_when_missing() -> None:
    with patch.dict(os.environ, {}, clear=True):
        env = _build_backend_env()
    assert env["ENVIRONMENT"] == "development"
    assert env["API_ACCESS_KEY"] == "dev-secret-key"


def test_build_backend_env_does_not_override_rotated_keys() -> None:
    with patch.dict(os.environ, {"API_ACCESS_KEYS": "k1,k2"}, clear=True):
        env = _build_backend_env()
    assert env["ENVIRONMENT"] == "development"
    assert env.get("API_ACCESS_KEY", "") != "dev-secret-key"
    assert env["API_ACCESS_KEYS"] == "k1,k2"


def test_build_frontend_env_inherits_backend_key() -> None:
    with patch.dict(os.environ, {}, clear=True):
        env = _build_frontend_env(backend_env={"API_ACCESS_KEY": "backend-key"})
    assert env["API_ACCESS_KEY"] == "backend-key"
    assert env["NEXT_PUBLIC_API_URL"] == "/api/v1"
    assert env["BACKEND_API_URL"] == "http://localhost:8000/api/v1"


def test_main_local_dry_run_redacts_api_keys(capsys) -> None:
    with patch.dict(os.environ, {"API_ACCESS_KEY": "supersecret"}, clear=True):
        rc = main(["--mode", "local", "--dry-run"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "BACKEND_CMD:" in out
    assert "FRONTEND_CMD:" in out
    assert "supersecret" not in out
    assert "<redacted>" in out
