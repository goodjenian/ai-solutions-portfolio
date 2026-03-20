from unittest.mock import patch

from fastapi.testclient import TestClient

from api.main import app
from config.settings import AppSettings

client = TestClient(app)


def _test_settings() -> AppSettings:
    return AppSettings(
        environment="development",
        auth_email_enabled=True,
        auth_code_ttl_minutes=10,
        session_ttl_days=30,
        auth_storage_dir=".auth_test",
    )


def test_request_code_and_verify_flow(tmp_path):
    with patch("api.routers.auth.get_settings") as mock_settings:
        s = _test_settings()
        s.auth_storage_dir = str(tmp_path)
        mock_settings.return_value = s
        r1 = client.post("/api/v1/auth/request-code", json={"email": "user@example.com"})
        assert r1.status_code == 200
        data = r1.json()
        assert data.get("status") == "code_sent"
        code = data.get("code")
        assert isinstance(code, str) and len(code) == 6
        r2 = client.post(
            "/api/v1/auth/verify-code", json={"email": "user@example.com", "code": code}
        )
        assert r2.status_code == 200
        info = r2.json()
        assert "session_token" in info
        assert info["user_email"] == "user@example.com"
        token = info["session_token"]
        r3 = client.get("/api/v1/auth/session", headers={"X-Session-Token": token})
        assert r3.status_code == 200
        info2 = r3.json()
        assert info2["user_email"] == "user@example.com"


def test_request_code_disabled(tmp_path):
    with patch("api.routers.auth.get_settings") as mock_settings:
        s = _test_settings()
        s.auth_email_enabled = False
        s.auth_storage_dir = str(tmp_path)
        mock_settings.return_value = s
        r = client.post("/api/v1/auth/request-code", json={"email": "user@example.com"})
        assert r.status_code == 400


def test_verify_code_invalid_format(tmp_path):
    with patch("api.routers.auth.get_settings") as mock_settings:
        s = _test_settings()
        s.auth_storage_dir = str(tmp_path)
        mock_settings.return_value = s
        r = client.post(
            "/api/v1/auth/verify-code", json={"email": "user@example.com", "code": "abc123"}
        )
        assert r.status_code == 400
