from unittest.mock import patch

from fastapi.testclient import TestClient

from api.main import app
from config.settings import AppSettings

client = TestClient(app)


def _test_settings() -> AppSettings:
    return AppSettings(
        environment="development",
        auth_email_enabled=True,
        auth_code_ttl_minutes=1,
        session_ttl_days=1,
        auth_storage_dir=".auth_integration",
    )


def test_email_auth_end_to_end(tmp_path):
    with patch("api.routers.auth.get_settings") as mock_settings:
        s = _test_settings()
        s.auth_storage_dir = str(tmp_path)
        mock_settings.return_value = s
        resp = client.post("/api/v1/auth/request-code", json={"email": "alice@example.com"})
        assert resp.status_code == 200
        code = resp.json().get("code")
        assert code is not None
        resp2 = client.post(
            "/api/v1/auth/verify-code", json={"email": "alice@example.com", "code": code}
        )
        assert resp2.status_code == 200
        token = resp2.json().get("session_token")
        assert token is not None
        resp3 = client.get("/api/v1/auth/session", headers={"X-Session-Token": token})
        assert resp3.status_code == 200
        assert resp3.json().get("user_email") == "alice@example.com"
