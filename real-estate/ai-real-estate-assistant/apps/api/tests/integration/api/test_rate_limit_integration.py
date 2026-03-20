from unittest.mock import patch

from fastapi.testclient import TestClient

from api.main import app
from config.settings import AppSettings


def _rl_settings() -> AppSettings:
    return AppSettings(
        environment="development",
        api_access_key="test-key-123",
        api_rate_limit_enabled=True,
        api_rate_limit_rpm=1,
    )


def _multi_key_settings() -> AppSettings:
    return AppSettings(
        environment="development",
        api_access_keys=["client-a-key", "client-b-key"],
        api_rate_limit_enabled=True,
        api_rate_limit_rpm=1,
    )


def test_rate_limit_headers_and_429():
    client = TestClient(app)
    with (
        patch("config.settings.get_settings") as mock_settings,
        patch("api.auth.get_settings") as mock_auth_settings,
    ):
        mock_settings.return_value = _rl_settings()
        mock_auth_settings.return_value = mock_settings.return_value
        headers = {"X-API-Key": "test-key-123"}
        r1 = client.get("/api/v1/verify-auth", headers=headers)
        assert r1.status_code == 200
        assert "X-RateLimit-Limit" in r1.headers
        assert "X-RateLimit-Remaining" in r1.headers
        assert "X-RateLimit-Reset" in r1.headers
        r2 = client.get("/api/v1/verify-auth", headers=headers)
        assert r2.status_code == 429
        assert "Retry-After" in r2.headers


def test_per_client_rate_limits_differ_by_api_key():
    """Test that different API keys have independent rate limits."""
    client = TestClient(app)
    with (
        patch("config.settings.get_settings") as mock_settings,
        patch("api.auth.get_settings") as mock_auth_settings,
    ):
        mock_settings.return_value = _multi_key_settings()
        mock_auth_settings.return_value = mock_settings.return_value

        headers_a = {"X-API-Key": "client-a-key"}
        headers_b = {"X-API-Key": "client-b-key"}

        # Client A makes a request (count: 1/1)
        r_a1 = client.get("/api/v1/verify-auth", headers=headers_a)
        assert r_a1.status_code == 200
        assert r_a1.headers["X-RateLimit-Remaining"] == "0"

        # Client A is rate limited
        r_a2 = client.get("/api/v1/verify-auth", headers=headers_a)
        assert r_a2.status_code == 429

        # Client B should still be able to make requests (independent limit)
        r_b1 = client.get("/api/v1/verify-auth", headers=headers_b)
        assert r_b1.status_code == 200
        assert r_b1.headers["X-RateLimit-Remaining"] == "0"

        # Client B is also rate limited now
        r_b2 = client.get("/api/v1/verify-auth", headers=headers_b)
        assert r_b2.status_code == 429


def test_per_client_rate_limits_with_secondary_key():
    """Test that secondary API key gets its own rate limit bucket."""
    client = TestClient(app)
    with (
        patch("config.settings.get_settings") as mock_settings,
        patch("api.auth.get_settings") as mock_auth_settings,
    ):
        settings = AppSettings(
            environment="development",
            api_access_key="primary-key",
            api_access_key_secondary="secondary-key",
            api_rate_limit_enabled=True,
            api_rate_limit_rpm=1,
        )
        mock_settings.return_value = settings
        mock_auth_settings.return_value = settings

        headers_primary = {"X-API-Key": "primary-key"}
        headers_secondary = {"X-API-Key": "secondary-key"}

        # Primary key request
        r1 = client.get("/api/v1/verify-auth", headers=headers_primary)
        assert r1.status_code == 200

        # Primary key rate limited
        r2 = client.get("/api/v1/verify-auth", headers=headers_primary)
        assert r2.status_code == 429

        # Secondary key should work independently
        r3 = client.get("/api/v1/verify-auth", headers=headers_secondary)
        assert r3.status_code == 200


def test_health_endpoint_no_auth_required():
    """Test that /health endpoint works without API key."""
    client = TestClient(app)
    with patch("config.settings.get_settings") as mock_settings:
        mock_settings.return_value = AppSettings(
            environment="development",
            api_access_key="test-key-123",
            api_rate_limit_enabled=True,
            api_rate_limit_rpm=1,
        )
        # /health should work without API key
        r = client.get("/health")
        assert r.status_code == 200


def test_docs_endpoint_no_auth_required():
    """Test that /docs endpoint works without API key."""
    client = TestClient(app)
    with patch("config.settings.get_settings") as mock_settings:
        mock_settings.return_value = AppSettings(
            environment="development",
            api_access_key="test-key-123",
            api_rate_limit_enabled=True,
            api_rate_limit_rpm=1,
        )
        # /docs should work without API key
        r = client.get("/docs")
        assert r.status_code == 200


def test_redoc_endpoint_no_auth_required():
    """Test that /redoc endpoint works without API key."""
    client = TestClient(app)
    with patch("config.settings.get_settings") as mock_settings:
        mock_settings.return_value = AppSettings(
            environment="development",
            api_access_key="test-key-123",
            api_rate_limit_enabled=True,
            api_rate_limit_rpm=1,
        )
        # /redoc should work without API key
        r = client.get("/redoc")
        assert r.status_code == 200


def test_excluded_endpoints_not_rate_limited():
    """Test that /health, /docs, /redoc are excluded from rate limiting."""
    client = TestClient(app)
    with patch("config.settings.get_settings") as mock_settings:
        settings = AppSettings(
            environment="development",
            api_access_key="test-key-123",
            api_rate_limit_enabled=True,
            api_rate_limit_rpm=1,
        )
        mock_settings.return_value = settings

        # Make multiple requests to /health (should not be rate limited)
        for _ in range(5):
            r = client.get("/health")
            assert r.status_code == 200
            assert "X-RateLimit-Limit" not in r.headers

        # Make multiple requests to /docs (should not be rate limited)
        for _ in range(5):
            r = client.get("/docs")
            assert r.status_code == 200
            assert "X-RateLimit-Limit" not in r.headers
