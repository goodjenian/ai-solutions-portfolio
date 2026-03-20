"""Unit tests for token expiration and refresh behavior.

Tests cover:
- Access token expiration
- Expired token detection
- Refresh token properties
- Token rotation scenarios
"""

import time

import jwt
import pytest

from core.jwt import (
    create_access_token,
    generate_refresh_token,
    get_access_token_expire_minutes,
    get_refresh_token_expire_days,
    verify_access_token,
)


class TestAccessTokenExpiration:
    """Tests for access token expiration behavior."""

    def test_access_token_includes_expiration(self):
        """Test that access token includes exp claim."""
        token = create_access_token(subject="user123")
        payload = verify_access_token(token)

        assert payload is not None
        assert "exp" in payload
        assert "iat" in payload

    def test_access_token_expiration_is_future(self):
        """Test that token expiration is in the future."""
        token = create_access_token(subject="user123")
        payload = verify_access_token(token)

        assert payload is not None
        exp = payload["exp"]
        now = int(time.time())

        # Expiration should be in the future
        assert exp > now

    def test_access_token_expiration_within_expected_range(self):
        """Test that token expires within expected time range."""
        token = create_access_token(subject="user123")
        payload = verify_access_token(token)

        assert payload is not None
        exp = payload["exp"]
        iat = payload["iat"]
        expected_duration = get_access_token_expire_minutes() * 60

        # Token should be valid for approximately the expected duration
        actual_duration = exp - iat
        # Allow 1 second tolerance
        assert abs(actual_duration - expected_duration) <= 1

    def test_verify_expired_token_raises(self):
        """Test that verifying an expired token raises an error."""
        # Create a token that's already expired
        # By setting exp to a time in the past
        expired_payload = {
            "sub": "user123",
            "type": "access",
            "exp": int(time.time()) - 3600,  # Expired 1 hour ago
            "iat": int(time.time()) - 7200,
        }

        # We need to sign it with the same secret that verify_access_token uses
        from core.jwt import get_jwt_secret

        secret = get_jwt_secret()
        expired_token = jwt.encode(expired_payload, secret, algorithm="HS256")

        with pytest.raises(jwt.ExpiredSignatureError):
            verify_access_token(expired_token)


class TestRefreshTokenProperties:
    """Tests for refresh token properties."""

    def test_refresh_token_is_random_string(self):
        """Test that refresh token is a random string, not a JWT."""
        token = generate_refresh_token()

        # Refresh tokens should not be JWTs (no dots)
        assert "." not in token
        assert isinstance(token, str)

    def test_refresh_tokens_are_unique(self):
        """Test that multiple refresh tokens are different."""
        tokens = [generate_refresh_token() for _ in range(10)]

        # All tokens should be unique
        assert len(set(tokens)) == 10

    def test_refresh_token_has_sufficient_entropy(self):
        """Test that refresh token has sufficient entropy."""
        token = generate_refresh_token()

        # Should be at least 32 characters for security
        assert len(token) >= 32

    def test_refresh_token_is_url_safe(self):
        """Test that refresh token is URL-safe."""
        token = generate_refresh_token()

        # Should only contain URL-safe characters
        import string

        allowed_chars = string.ascii_letters + string.digits + "-_"
        assert all(c in allowed_chars for c in token)


class TestTokenRotation:
    """Tests for token rotation scenarios."""

    def test_refresh_produces_different_tokens_over_time(self):
        """Test that tokens issued at different times are different."""
        # Create first token
        old_token = create_access_token(subject="user123")
        old_payload = verify_access_token(old_token)

        # Wait to ensure different iat timestamp
        time.sleep(1)

        # Create second token
        new_token = create_access_token(subject="user123")
        new_payload = verify_access_token(new_token)

        # Tokens should be different due to different iat
        assert old_token != new_token

        # But both should decode to same subject
        assert old_payload is not None
        assert new_payload is not None
        assert old_payload["sub"] == new_payload["sub"]

        # iat should differ
        assert new_payload["iat"] > old_payload["iat"]

    def test_refresh_produces_new_refresh_token(self):
        """Test that refresh produces a new refresh token."""
        old_refresh = generate_refresh_token()
        new_refresh = generate_refresh_token()

        # Refresh tokens should always be unique
        assert old_refresh != new_refresh

    def test_token_issuance_time_differs(self):
        """Test that tokens issued at different times have different iat."""
        token1 = create_access_token(subject="user123")
        time.sleep(1)  # Ensure different timestamp
        token2 = create_access_token(subject="user123")

        payload1 = verify_access_token(token1)
        payload2 = verify_access_token(token2)

        assert payload1 is not None
        assert payload2 is not None
        # iat should differ by at least 1 second
        assert payload2["iat"] > payload1["iat"]


class TestTokenPayloadStructure:
    """Tests for token payload structure."""

    def test_access_token_has_required_claims(self):
        """Test that access token has all required claims."""
        token = create_access_token(subject="user123", roles=["user"])
        payload = verify_access_token(token)

        assert payload is not None
        # Required claims
        assert "sub" in payload  # Subject (user ID)
        assert "exp" in payload  # Expiration
        assert "iat" in payload  # Issued at
        assert "type" in payload  # Token type
        assert "roles" in payload  # User roles

    def test_access_token_type_is_access(self):
        """Test that access token type is 'access'."""
        token = create_access_token(subject="user123")
        payload = verify_access_token(token)

        assert payload is not None
        assert payload["type"] == "access"

    def test_access_token_with_roles(self):
        """Test that access token includes roles."""
        token = create_access_token(subject="user123", roles=["admin", "editor"])
        payload = verify_access_token(token)

        assert payload is not None
        assert payload["roles"] == ["admin", "editor"]

    def test_access_token_default_role(self):
        """Test access token with no roles specified."""
        token = create_access_token(subject="user123")
        payload = verify_access_token(token)

        assert payload is not None
        # Roles should be empty list when not specified
        assert payload.get("roles", []) == []


class TestExpirationConfiguration:
    """Tests for token expiration configuration."""

    def test_access_token_expire_minutes_is_positive(self):
        """Test that access token expiration is positive."""
        minutes = get_access_token_expire_minutes()
        assert minutes > 0

    def test_refresh_token_expire_days_is_positive(self):
        """Test that refresh token expiration is positive."""
        days = get_refresh_token_expire_days()
        assert days > 0

    def test_access_token_shorter_than_refresh(self):
        """Test that access token expires before refresh token."""
        access_minutes = get_access_token_expire_minutes()
        refresh_days = get_refresh_token_expire_days()
        refresh_minutes = refresh_days * 24 * 60

        # Access token should expire before refresh token
        assert access_minutes < refresh_minutes
