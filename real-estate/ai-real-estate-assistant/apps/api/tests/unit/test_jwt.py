"""Unit tests for JWT token creation and validation."""

import jwt
import pytest

from core.jwt import (
    create_access_token,
    decode_access_token,
    generate_csrf_token,
    generate_password_reset_token,
    generate_refresh_token,
    generate_verification_token,
    verify_access_token,
)


class TestAccessToken:
    """Tests for access token creation and verification."""

    def test_create_access_token_returns_string(self):
        """Test that create_access_token returns a string."""
        token = create_access_token(subject="user123")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_contains_three_parts(self):
        """Test that JWT has three parts separated by dots."""
        token = create_access_token(subject="user123")
        parts = token.split(".")
        assert len(parts) == 3

    def test_verify_access_token_returns_payload(self):
        """Test that verify_access_token returns the decoded payload."""
        subject = "user123"
        token = create_access_token(subject=subject)
        payload = verify_access_token(token)
        assert payload is not None
        assert payload["sub"] == subject
        assert payload["type"] == "access"

    def test_verify_access_token_with_roles(self):
        """Test that roles are included in the token."""
        subject = "user123"
        roles = ["admin", "user"]
        token = create_access_token(subject=subject, roles=roles)
        payload = verify_access_token(token)
        assert payload is not None
        assert payload["roles"] == roles

    def test_verify_access_token_with_additional_claims(self):
        """Test that additional claims are included in the token."""
        subject = "user123"
        additional_claims = {"email": "test@example.com", "tenant_id": "tenant1"}
        token = create_access_token(subject=subject, additional_claims=additional_claims)
        payload = verify_access_token(token)
        assert payload is not None
        assert payload["email"] == "test@example.com"
        assert payload["tenant_id"] == "tenant1"

    def test_verify_access_token_invalid_token_raises(self):
        """Test that verify_access_token raises for invalid token."""
        invalid_token = "invalid.token.here"
        with pytest.raises(jwt.InvalidTokenError):
            verify_access_token(invalid_token)

    def test_verify_access_token_malformed_token_raises(self):
        """Test that verify_access_token raises for malformed token."""
        malformed = "not-a-jwt"
        with pytest.raises(jwt.InvalidTokenError):
            verify_access_token(malformed)

    def test_create_access_token_includes_expiry(self):
        """Test that token includes expiration claim."""
        token = create_access_token(subject="user123")
        payload = verify_access_token(token)
        assert payload is not None
        assert "exp" in payload
        assert "iat" in payload

    def test_decode_access_token_without_verification(self):
        """Test decoding token without verification."""
        token = create_access_token(subject="user123")
        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded["sub"] == "user123"

    def test_decode_access_token_invalid_returns_none(self):
        """Test that decode_access_token returns None for invalid token."""
        invalid_token = "not-a-valid-jwt"
        decoded = decode_access_token(invalid_token)
        assert decoded is None


class TestRefreshToken:
    """Tests for refresh token generation."""

    def test_generate_refresh_token_returns_string(self):
        """Test that generate_refresh_token returns a string."""
        token = generate_refresh_token()
        assert isinstance(token, str)
        assert len(token) > 0

    def test_generate_refresh_token_unique(self):
        """Test that each refresh token is unique."""
        token1 = generate_refresh_token()
        token2 = generate_refresh_token()
        assert token1 != token2

    def test_generate_refresh_token_length(self):
        """Test that refresh token has reasonable length."""
        token = generate_refresh_token()
        # URL-safe base64 encoded 32 bytes should be ~43 chars
        assert len(token) >= 32


class TestCSRFToken:
    """Tests for CSRF token generation."""

    def test_generate_csrf_token_returns_string(self):
        """Test that generate_csrf_token returns a string."""
        token = generate_csrf_token()
        assert isinstance(token, str)
        assert len(token) > 0

    def test_generate_csrf_token_unique(self):
        """Test that each CSRF token is unique."""
        token1 = generate_csrf_token()
        token2 = generate_csrf_token()
        assert token1 != token2


class TestPasswordResetToken:
    """Tests for password reset token generation."""

    def test_generate_password_reset_token_returns_string(self):
        """Test that token generation returns a string."""
        token = generate_password_reset_token()
        assert isinstance(token, str)
        assert len(token) > 0

    def test_password_reset_token_unique(self):
        """Test that tokens are unique."""
        token1 = generate_password_reset_token()
        token2 = generate_password_reset_token()
        assert token1 != token2

    def test_password_reset_token_length(self):
        """Test that reset token has reasonable length."""
        token = generate_password_reset_token()
        # URL-safe base64 encoded 32 bytes should be ~43 chars
        assert len(token) >= 32


class TestEmailVerificationToken:
    """Tests for email verification token generation."""

    def test_generate_verification_token_returns_string(self):
        """Test that token generation returns a string."""
        token = generate_verification_token()
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verification_token_unique(self):
        """Test that tokens are unique."""
        token1 = generate_verification_token()
        token2 = generate_verification_token()
        assert token1 != token2

    def test_verification_token_length(self):
        """Test that verification token has reasonable length."""
        token = generate_verification_token()
        # URL-safe base64 encoded 32 bytes should be ~43 chars
        assert len(token) >= 32
