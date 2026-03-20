from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from api.auth import get_api_key
from api.observability import (
    RateLimiter,
    client_id_from_api_key,
    generate_request_id,
    normalize_request_id,
)
from config.settings import AppSettings


def _mock_request(request_id: str = "test-request-id") -> MagicMock:
    """Create a mock Request object with request_id in state."""
    request = MagicMock()
    request.state.request_id = request_id
    request.url.path = "/api/v1/test"
    request.method = "GET"
    return request


@pytest.mark.asyncio
async def test_get_api_key_valid():
    """Test valid API key acceptance."""
    key = "test-key"
    request = _mock_request()
    with patch("api.auth.get_settings") as mock_settings:
        mock_settings.return_value = AppSettings(api_access_key=key)
        result = await get_api_key(request, api_key_header=key)
        assert result == key


@pytest.mark.asyncio
async def test_get_api_key_strips_header_whitespace():
    key = "test-key"
    request = _mock_request()
    with patch("api.auth.get_settings") as mock_settings:
        mock_settings.return_value = AppSettings(api_access_key=key)
        result = await get_api_key(request, api_key_header=f"  {key}  ")
        assert result == key


@pytest.mark.asyncio
async def test_get_api_key_valid_with_rotated_keys():
    key1 = "key-1"
    key2 = "key-2"
    request = _mock_request()
    with patch("api.auth.get_settings") as mock_settings:
        mock_settings.return_value = AppSettings(api_access_keys=[key1, key2])
        result = await get_api_key(request, api_key_header=key2)
        assert result == key2


@pytest.mark.asyncio
async def test_get_api_key_valid_with_secondary_key():
    """Test secondary API key is accepted for rotation support."""
    primary = "primary-key-xyz"
    secondary = "secondary-key-abc"
    request = _mock_request()
    with patch("api.auth.get_settings") as mock_settings:
        mock_settings.return_value = AppSettings(
            api_access_key=primary,
            api_access_key_secondary=secondary,
        )
        # Both keys should be valid
        result1 = await get_api_key(request, api_key_header=primary)
        result2 = await get_api_key(request, api_key_header=secondary)
        assert result1 == primary
        assert result2 == secondary


@pytest.mark.asyncio
async def test_get_api_key_invalid():
    """Test invalid API key rejection."""
    key = "test-key"
    request = _mock_request()
    with patch("api.auth.get_settings") as mock_settings:
        mock_settings.return_value = AppSettings(api_access_key=key)
        with pytest.raises(HTTPException) as exc:
            await get_api_key(request, api_key_header="wrong-key")
        assert exc.value.status_code == 403
        # Verify safe error message (doesn't reveal if key exists)
        assert exc.value.detail == "Invalid credentials"


@pytest.mark.asyncio
async def test_get_api_key_invalid_when_not_in_rotated_set():
    request = _mock_request()
    with patch("api.auth.get_settings") as mock_settings:
        mock_settings.return_value = AppSettings(api_access_keys=["a", "b"])
        with pytest.raises(HTTPException) as exc:
            await get_api_key(request, api_key_header="c")
        assert exc.value.status_code == 403
        # Verify safe error message
        assert exc.value.detail == "Invalid credentials"


@pytest.mark.asyncio
async def test_get_api_key_missing():
    """Test missing API key handling."""
    request = _mock_request()
    with pytest.raises(HTTPException) as exc:
        await get_api_key(request, api_key_header=None)
    assert exc.value.status_code == 401
    # Verify safe error message
    assert exc.value.detail == "Invalid credentials"


@pytest.mark.asyncio
async def test_get_api_key_rejects_invalid_prod_configuration_with_default_key():
    request = _mock_request()
    with patch("api.auth.get_settings") as mock_settings:
        mock_settings.return_value = AppSettings(
            environment="production",
            api_access_keys=["dev-secret-key"],
            cors_allow_origins=["https://example.com"],
        )
        with pytest.raises(HTTPException) as exc:
            await get_api_key(request, api_key_header="dev-secret-key")
        assert exc.value.status_code == 403
        # Production misconfiguration error should be safe too
        assert exc.value.detail == "Invalid credentials"


@pytest.mark.asyncio
async def test_get_api_key_rejects_invalid_prod_configuration_with_no_keys():
    request = _mock_request()
    with patch("api.auth.get_settings") as mock_settings:
        mock_settings.return_value = AppSettings(
            environment="production",
            api_access_keys=[],
            api_access_key=None,
            cors_allow_origins=["https://example.com"],
        )
        with pytest.raises(HTTPException) as exc:
            await get_api_key(request, api_key_header="any")
        assert exc.value.status_code == 403
        assert exc.value.detail == "Invalid credentials"


def test_normalize_request_id_accepts_valid_values():
    assert normalize_request_id("abc-123_DEF.ghi") == "abc-123_DEF.ghi"
    assert normalize_request_id("   abc-123   ") == "abc-123"


def test_normalize_request_id_rejects_invalid_values():
    assert normalize_request_id(None) is None
    assert normalize_request_id("") is None
    assert normalize_request_id("   ") is None
    assert normalize_request_id("has space") is None
    assert normalize_request_id("x" * 129) is None


def test_generate_request_id_returns_nonempty_hex():
    rid = generate_request_id()
    assert isinstance(rid, str)
    assert len(rid) == 32
    int(rid, 16)


def test_client_id_from_api_key_is_stable_and_uniqueish():
    assert client_id_from_api_key(None) is None
    assert client_id_from_api_key("") is None

    a1 = client_id_from_api_key("key-a")
    a2 = client_id_from_api_key("key-a")
    b1 = client_id_from_api_key("key-b")

    assert a1 == a2
    assert a1 != b1
    assert len(a1) == 12


def test_rate_limiter_allows_requests_within_window():
    limiter = RateLimiter(max_requests=2, window_seconds=60)

    allowed1, limit1, remaining1, reset1 = limiter.check("client", now=1000.0)
    allowed2, limit2, remaining2, reset2 = limiter.check("client", now=1001.0)

    assert allowed1 is True
    assert allowed2 is True
    assert limit1 == 2
    assert limit2 == 2
    assert remaining1 == 1
    assert remaining2 == 0
    assert reset1 >= 1
    assert reset2 >= 1


def test_rate_limiter_blocks_when_exceeded_and_recovers_after_window():
    limiter = RateLimiter(max_requests=2, window_seconds=60)

    limiter.check("client", now=1000.0)
    limiter.check("client", now=1001.0)

    allowed3, limit3, remaining3, reset3 = limiter.check("client", now=1002.0)
    assert allowed3 is False
    assert limit3 == 2
    assert remaining3 == 0
    assert reset3 >= 1

    allowed4, _limit4, remaining4, _reset4 = limiter.check("client", now=1061.0)
    assert allowed4 is True
    assert remaining4 == 1
