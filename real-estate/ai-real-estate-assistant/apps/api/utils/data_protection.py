"""
Data Protection Utilities for PII and sensitive data (TASK-018).

This module provides utilities for:
1. Sensitive data masking (for logs, UI display, etc.)
2. PII detection and redaction
3. Encryption helpers for data at rest
4. Secure token generation

These utilities help prevent accidental leakage of sensitive information
in logs, error messages, and API responses.
"""

import base64
import hashlib
import os
import re
import secrets
from typing import Any, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class DataMasker:
    """
    Utility for masking sensitive data in logs and displays.

    Provides various masking strategies:
    - Full mask: ****
    - Partial mask: ab***cd
    - Email mask: a***@example.com
    - API key mask: sk_***1234
    - Credit card mask: **** **** **** 1234
    """

    # Patterns for detecting sensitive data
    PATTERNS = {
        "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
        "api_key": re.compile(
            r"(sk_|pk_|api_key|apikey|api-key)[:\s]*[a-zA-Z0-9_\-]{16,}", re.IGNORECASE
        ),
        "credit_card": re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
        "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        "phone": re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b"),
        "ip_address": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
        "url_with_credentials": re.compile(r"https?://[^:]+:[^@]+@"),
        "token": re.compile(r"(bearer|token)[:\s]*[a-zA-Z0-9_\-\.]{20,}", re.IGNORECASE),
        "password": re.compile(r"(password|passwd|pwd)[:\s]*[^\s]+", re.IGNORECASE),
    }

    @staticmethod
    def mask_full(value: str, mask_char: str = "*") -> str:
        """
        Fully mask a value.

        Args:
            value: Value to mask
            mask_char: Character to use for masking

        Returns:
            Masked value
        """
        if not value:
            return value
        return mask_char * min(len(value), 8)

    @staticmethod
    def mask_partial(value: str, visible_chars: int = 2, mask_char: str = "*") -> str:
        """
        Mask a value showing only the first few characters.

        Args:
            value: Value to mask
            visible_chars: Number of characters to show at start
            mask_char: Character to use for masking

        Returns:
            Partially masked value
        """
        if not value:
            return value
        if len(value) <= visible_chars:
            return mask_char * len(value)
        return value[:visible_chars] + mask_char * (len(value) - visible_chars)

    @staticmethod
    def mask_email(email: str) -> str:
        """
        Mask an email address.

        Args:
            email: Email address to mask

        Returns:
            Masked email (e.g., a***@example.com)
        """
        if not email or "@" not in email:
            return email
        local, domain = email.split("@", 1)
        return f"{local[0] if local else ''}***@{domain}"

    @staticmethod
    def mask_api_key(api_key: str, visible_chars: int = 4) -> str:
        """
        Mask an API key.

        Args:
            api_key: API key to mask
            visible_chars: Number of characters to show at end

        Returns:
            Masked API key (e.g., sk_***1234)
        """
        if not api_key:
            return api_key
        # Keep prefix if it exists (sk_, pk_, etc.)
        prefix = ""
        if "_" in api_key:
            prefix_end = api_key.index("_") + 1
            prefix = api_key[:prefix_end]
            api_key = api_key[prefix_end:]
        return f"{prefix}***{api_key[-visible_chars:] if len(api_key) > visible_chars else ''}"

    @staticmethod
    def mask_credit_card(card: str) -> str:
        """
        Mask a credit card number.

        Args:
            card: Credit card number to mask

        Returns:
            Masked card (e.g., **** **** **** 1234)
        """
        if not card:
            return card
        # Remove non-digits
        digits = re.sub(r"\D", "", card)
        if len(digits) < 13:
            return card
        # Show last 4 digits
        return f"{'*' * (len(digits) - 4)} {digits[-4:]}"

    @staticmethod
    def mask_dict(
        data: dict[str, Any], sensitive_keys: Optional[set[str]] = None
    ) -> dict[str, Any]:
        """
        Mask sensitive values in a dictionary.

        Args:
            data: Dictionary to sanitize
            sensitive_keys: Set of keys that contain sensitive data

        Returns:
            Dictionary with sensitive values masked
        """
        if sensitive_keys is None:
            sensitive_keys = {
                "password",
                "passwd",
                "pwd",
                "secret",
                "token",
                "api_key",
                "apikey",
                "api-key",
                "access_token",
                "refresh_token",
                "authorization",
                "auth_token",
                "session_token",
                "csrf_token",
                "ssn",
                "social_security",
                "credit_card",
                "card_number",
                "account_number",
                "routing_number",
                "pin",
                "private_key",
                "secret_key",
                "webhook_secret",
                "webhook_url",
                "database_url",
            }

        result: dict[str, Any] = {}
        for key, value in data.items():
            key_lower = key.lower()
            if key_lower in sensitive_keys or any(s in key_lower for s in sensitive_keys):
                if isinstance(value, str):
                    result[key] = DataMasker.mask_full(value)
                else:
                    result[key] = "***"
            elif isinstance(value, dict):
                result[key] = DataMasker.mask_dict(value, sensitive_keys)
            elif isinstance(value, list):
                result[key] = [
                    DataMasker.mask_dict(item, sensitive_keys) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                result[key] = value
        return result

    @staticmethod
    def detect_and_mask(text: str) -> str:
        """
        Detect and mask sensitive data in text.

        Args:
            text: Text to scan and mask

        Returns:
            Text with sensitive data masked
        """
        if not text:
            return text

        result = text
        for pattern_name, pattern in DataMasker.PATTERNS.items():
            if pattern_name == "email":
                result = pattern.sub(lambda m: DataMasker.mask_email(m.group(0)), result)
            elif pattern_name == "api_key":
                result = pattern.sub(lambda m: DataMasker.mask_api_key(m.group(0)), result)
            elif pattern_name == "credit_card":
                result = pattern.sub(lambda m: DataMasker.mask_credit_card(m.group(0)), result)
            else:
                # Default: full mask
                result = pattern.sub("***", result)

        return result


class EncryptionHelper:
    """
    Helper for encryption/decryption of sensitive data.

    Uses Fernet (symmetric encryption) with PBKDF2 key derivation.
    """

    @staticmethod
    def generate_key() -> bytes:
        """
        Generate a new Fernet encryption key.

        Returns:
            URL-safe base64-encoded 32-byte key
        """
        return Fernet.generate_key()

    @staticmethod
    def derive_key_from_password(
        password: str, salt: Optional[bytes] = None
    ) -> tuple[bytes, bytes]:
        """
        Derive encryption key from password using PBKDF2.

        Args:
            password: Password to derive key from
            salt: Salt for key derivation (generated if not provided)

        Returns:
            Tuple of (key, salt)
        """
        if salt is None:
            salt = os.urandom(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend(),
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt

    @staticmethod
    def encrypt(data: str, key: bytes) -> str:
        """
        Encrypt data using Fernet.

        Args:
            data: Data to encrypt
            key: Fernet key

        Returns:
            Encrypted data (base64-encoded)
        """
        f = Fernet(key)
        encrypted = f.encrypt(data.encode("utf-8"))
        return base64.urlsafe_b64encode(encrypted).decode("utf-8")

    @staticmethod
    def decrypt(encrypted_data: str, key: bytes) -> str:
        """
        Decrypt data using Fernet.

        Args:
            encrypted_data: Encrypted data (base64-encoded)
            key: Fernet key

        Returns:
            Decrypted data

        Raises:
            ValueError: If decryption fails
        """
        f = Fernet(key)
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode("utf-8"))
            decrypted = f.decrypt(encrypted_bytes)
            return decrypted.decode("utf-8")
        except Exception as err:
            raise ValueError(f"Decryption failed: {err}") from err

    @staticmethod
    def hash_data(data: str, salt: Optional[str] = None) -> str:
        """
        Hash data using SHA-256.

        Args:
            data: Data to hash
            salt: Optional salt for hashing

        Returns:
            Hex-encoded hash
        """
        if salt:
            data = f"{salt}{data}"
        return hashlib.sha256(data.encode("utf-8")).hexdigest()


class TokenGenerator:
    """Secure token generation for various purposes."""

    @staticmethod
    def generate_api_key(prefix: str = "sk") -> str:
        """
        Generate a secure API key.

        Args:
            prefix: Key prefix (e.g., sk, pk)

        Returns:
            API key with prefix and random component
        """
        random_bytes = secrets.token_bytes(24)
        random_part = base64.urlsafe_b64encode(random_bytes).decode("utf-8").rstrip("=")
        return f"{prefix}_{random_part}"

    @staticmethod
    def generate_session_token() -> str:
        """
        Generate a secure session token.

        Returns:
            Session token
        """
        return secrets.token_urlsafe(32)

    @staticmethod
    def generate_reset_token() -> str:
        """
        Generate a password reset token.

        Returns:
            Reset token
        """
        return secrets.token_urlsafe(32)

    @staticmethod
    def generate_verification_code(length: int = 6) -> str:
        """
        Generate a numeric verification code.

        Args:
            length: Number of digits

        Returns:
            Numeric verification code
        """
        return "".join(secrets.choice("0123456789") for _ in range(length))


def sanitize_for_logging(data: Any, max_length: int = 1000) -> Any:
    """
    Sanitize data for logging (mask sensitive fields, limit length).

    Args:
        data: Data to sanitize
        max_length: Maximum string length after sanitization

    Returns:
        Sanitized data safe for logging
    """
    if isinstance(data, dict):
        sanitized = DataMasker.mask_dict(data)
        # Also recursively sanitize nested values
        return {
            k: sanitize_for_logging(v, max_length)
            if not any(s in k.lower() for s in DataMasker.PATTERNS.keys())
            else v
            for k, v in sanitized.items()
        }
    elif isinstance(data, str):
        masked = DataMasker.detect_and_mask(data)
        return masked[:max_length] + "..." if len(masked) > max_length else masked
    elif isinstance(data, list):
        return [sanitize_for_logging(item, max_length) for item in data]
    else:
        return data
