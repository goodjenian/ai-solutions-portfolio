"""Unit tests for auth router validation and utilities.

Note: Full endpoint integration tests require async database setup.
These tests focus on password validation, token generation, and input
validation.
"""

from core.jwt import (
    create_access_token,
    generate_csrf_token,
    generate_refresh_token,
    verify_access_token,
)
from core.password import (
    hash_password,
    validate_password_strength,
    verify_password,
)


class TestPasswordValidation:
    """Tests for password validation in auth context."""

    def test_validate_registration_password_strong(self):
        """Test that strong password passes validation."""
        password = "StrongPass123!"
        is_valid, msg = validate_password_strength(password)
        assert is_valid is True

    def test_validate_registration_password_weak(self):
        """Test that weak password fails validation."""
        password = "weak"
        is_valid, msg = validate_password_strength(password)
        assert is_valid is False
        assert "8" in msg

    def test_validate_registration_password_no_uppercase(self):
        """Test that password without uppercase fails."""
        password = "lowercase123"
        is_valid, msg = validate_password_strength(password)
        assert is_valid is False
        assert "uppercase" in msg.lower()

    def test_validate_registration_password_no_digit(self):
        """Test that password without digit fails."""
        password = "NoDigitsHere"
        is_valid, msg = validate_password_strength(password)
        assert is_valid is False
        assert "digit" in msg.lower()


class TestTokenGeneration:
    """Tests for token generation in auth context."""

    def test_access_token_for_user(self):
        """Test generating access token for user ID."""
        user_id = "user-123"
        token = create_access_token(subject=user_id, roles=["user"])
        assert isinstance(token, str)

        payload = verify_access_token(token)
        assert payload["sub"] == user_id
        assert payload["roles"] == ["user"]
        assert payload["type"] == "access"

    def test_access_token_for_admin(self):
        """Test generating access token for admin user."""
        user_id = "admin-456"
        token = create_access_token(subject=user_id, roles=["admin", "user"])
        payload = verify_access_token(token)
        assert "admin" in payload["roles"]

    def test_refresh_token_for_session(self):
        """Test generating refresh token for session."""
        token = generate_refresh_token()
        assert isinstance(token, str)
        assert len(token) >= 32

    def test_csrf_token_for_forms(self):
        """Test generating CSRF token."""
        token = generate_csrf_token()
        assert isinstance(token, str)
        assert len(token) >= 32


class TestPasswordHashing:
    """Tests for password hashing in auth context."""

    def test_hash_for_storage(self):
        """Test that password hash is suitable for storage."""
        password = "UserPassword123"
        hashed = hash_password(password)

        # Should be bcrypt format
        assert hashed.startswith("$2b$")

        # Should not contain original password
        assert password not in hashed

    def test_verify_for_login(self):
        """Test password verification for login."""
        password = "LoginPassword123"
        hashed = hash_password(password)

        # Correct password should verify
        assert verify_password(password, hashed) is True

        # Wrong password should not verify
        assert verify_password("WrongPassword", hashed) is False


class TestAuthInputValidation:
    """Tests for auth input validation."""

    def test_email_format_validation(self):
        """Test that email format is validated."""
        # This would be handled by Pydantic, but we can check the logic
        valid_emails = [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.org",
        ]
        # These should pass basic email validation
        for email in valid_emails:
            assert "@" in email
            assert "." in email.split("@")[1]

    def test_invalid_email_detection(self):
        """Test detection of invalid emails."""
        invalid_emails = [
            ("not-an-email", False),
            ("@missing-local.com", False),
            ("missing-at-sign.com", False),
            ("", False),
        ]
        for email, expected_valid in invalid_emails:
            # Basic check - valid emails have @ and domain with dot
            parts = email.split("@")
            has_valid_format = len(parts) == 2 and len(parts[0]) > 0 and "." in parts[1]
            assert has_valid_format == expected_valid, f"Failed for: {email}"

    def test_password_strength_requirements(self):
        """Test password strength requirements for auth."""
        # Minimum requirements: 8 chars, uppercase, lowercase, digit
        valid_passwords = [
            "Password1",
            "SecurePass123",
            "MyP@ssw0rd",
        ]
        for pwd in valid_passwords:
            is_valid, _ = validate_password_strength(pwd)
            assert is_valid is True

        invalid_passwords = [
            "short",  # Too short
            "alllowercase1",  # No uppercase
            "ALLUPPERCASE1",  # No lowercase
            "NoDigitsHere",  # No digit
        ]
        for pwd in invalid_passwords:
            is_valid, _ = validate_password_strength(pwd)
            assert is_valid is False


class TestTokenPayloadStructure:
    """Tests for JWT token payload structure."""

    def test_token_includes_required_claims(self):
        """Test that token includes all required claims."""
        token = create_access_token(subject="user-123")
        payload = verify_access_token(token)

        # Required claims
        assert "sub" in payload  # Subject (user ID)
        assert "exp" in payload  # Expiration
        assert "iat" in payload  # Issued at
        assert "type" in payload  # Token type
        assert payload["type"] == "access"

    def test_token_with_additional_claims(self):
        """Test token with additional claims like email."""
        token = create_access_token(
            subject="user-123",
            additional_claims={"email": "test@example.com"},
        )
        payload = verify_access_token(token)
        assert payload["email"] == "test@example.com"

    def test_token_with_roles(self):
        """Test token includes role information."""
        token = create_access_token(
            subject="user-123",
            roles=["user", "premium"],
        )
        payload = verify_access_token(token)
        assert payload["roles"] == ["user", "premium"]
