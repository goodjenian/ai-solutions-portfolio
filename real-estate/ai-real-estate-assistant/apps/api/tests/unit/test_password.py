"""Unit tests for password hashing and validation."""

from core.password import (
    hash_password,
    needs_rehash,
    validate_password_strength,
    verify_password,
)


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password_returns_string(self):
        """Test that hash_password returns a string."""
        password = "TestPwd1"
        hashed = hash_password(password)
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_is_bcrypt_format(self):
        """Test that hashed password follows bcrypt format."""
        password = "TestPwd1"
        hashed = hash_password(password)
        # bcrypt hashes start with $2b$
        assert hashed.startswith("$2b$")

    def test_hash_password_different_each_time(self):
        """Test that same password produces different hashes (salt)."""
        password = "TestPwd1"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Test verifying correct password."""
        password = "TestPwd1"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        password = "TestPwd1"
        wrong_password = "WrongPwd2"
        hashed = hash_password(password)
        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_case_sensitive(self):
        """Test that password verification is case sensitive."""
        password = "TestPwd1"
        hashed = hash_password(password)
        assert verify_password(password.lower(), hashed) is False


class TestPasswordRehash:
    """Tests for password rehash detection."""

    def test_needs_rehash_returns_false_for_fresh_hash(self):
        """Test that fresh bcrypt hash doesn't need rehash."""
        password = "TestPwd1"
        hashed = hash_password(password)
        assert needs_rehash(hashed) is False


class TestPasswordStrength:
    """Tests for password strength validation."""

    def test_validate_strong_password(self):
        """Test validation of strong password with special char."""
        password = "StrongPass123!"
        is_valid, msg = validate_password_strength(password)
        assert is_valid is True
        assert msg is None

    def test_validate_password_without_special(self):
        """Test validation accepts password without special char."""
        password = "StrongPass123"
        is_valid, msg = validate_password_strength(password)
        assert is_valid is True
        assert "special" in msg.lower()

    def test_validate_password_too_short(self):
        """Test validation rejects short password."""
        password = "Short1"
        is_valid, msg = validate_password_strength(password)
        assert is_valid is False
        assert "8" in msg

    def test_validate_password_no_uppercase(self):
        """Test validation rejects password without uppercase."""
        password = "lowercase123"
        is_valid, msg = validate_password_strength(password)
        assert is_valid is False
        assert "uppercase" in msg.lower()

    def test_validate_password_no_lowercase(self):
        """Test validation rejects password without lowercase."""
        password = "UPPERCASE123"
        is_valid, msg = validate_password_strength(password)
        assert is_valid is False
        assert "lowercase" in msg.lower()

    def test_validate_password_no_digit(self):
        """Test validation rejects password without digit."""
        password = "NoDigitsHere"
        is_valid, msg = validate_password_strength(password)
        assert is_valid is False
        assert "digit" in msg.lower()

    def test_validate_password_minimum_length(self):
        """Test validation accepts exactly 8 character password."""
        password = "JustEi1!"
        is_valid, msg = validate_password_strength(password)
        assert is_valid is True

    def test_validate_password_empty(self):
        """Test validation rejects empty password."""
        password = ""
        is_valid, msg = validate_password_strength(password)
        assert is_valid is False
        assert msg is not None
