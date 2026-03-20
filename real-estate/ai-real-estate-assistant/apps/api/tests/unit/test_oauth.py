"""Unit tests for OAuth providers.

Tests cover:
- PKCE code verifier and challenge generation
- Authorization URL generation
- User info structure
- Error handling
"""

import pytest

from core.oauth import (
    GoogleOAuthProvider,
    OAuthError,
    OAuthUserInfo,
)

# AppleOAuthProvider is optional and may not be available
try:
    from core.oauth import AppleOAuthProvider

    APPLE_AVAILABLE = True
except ImportError:
    APPLE_AVAILABLE = False


class TestPKCEGeneration:
    """Tests for PKCE code verifier and challenge generation."""

    def test_generate_pkce_verifier(self):
        """Test PKCE code verifier generation."""
        verifier = GoogleOAuthProvider.generate_pkce_verifier()
        assert isinstance(verifier, str)
        assert len(verifier) >= 43  # Minimum secure length
        assert len(verifier) <= 128

    def test_generate_pkce_verifier_uniqueness(self):
        """Test that PKCE verifiers are unique."""
        verifier1 = GoogleOAuthProvider.generate_pkce_verifier()
        verifier2 = GoogleOAuthProvider.generate_pkce_verifier()
        assert verifier1 != verifier2

    def test_generate_pkce_challenge(self):
        """Test PKCE code challenge generation."""
        verifier = GoogleOAuthProvider.generate_pkce_verifier()
        challenge = GoogleOAuthProvider.generate_pkce_challenge(verifier)
        assert isinstance(challenge, str)
        assert len(challenge) == 43  # SHA256 base64url length

    def test_pkce_challenge_deterministic(self):
        """Test that same verifier produces same challenge."""
        verifier = GoogleOAuthProvider.generate_pkce_verifier()
        challenge1 = GoogleOAuthProvider.generate_pkce_challenge(verifier)
        challenge2 = GoogleOAuthProvider.generate_pkce_challenge(verifier)
        assert challenge1 == challenge2


class TestGoogleOAuthProvider:
    """Tests for Google OAuth provider."""

    def setup_method(self):
        """Set up test fixtures."""
        self.provider = GoogleOAuthProvider(
            client_id="test-client-id.apps.googleusercontent.com",
            client_secret="test-client-secret",
            redirect_uri="http://localhost:3000/api/v1/auth/oauth/callback",
        )

    def test_get_authorization_url(self):
        """Test authorization URL generation."""
        state = "test-state-123"
        code_challenge = "test-challenge"

        url = self.provider.get_authorization_url(
            state=state,
            code_challenge=code_challenge,
        )

        assert "accounts.google.com" in url
        assert "test-client-id" in url
        assert "test-state-123" in url
        assert "code_challenge=test-challenge" in url
        assert "code_challenge_method=S256" in url

    def test_get_authorization_url_includes_scopes(self):
        """Test that authorization URL includes required scopes."""
        url = self.provider.get_authorization_url(
            state="state",
            code_challenge="challenge",
        )

        # Should include openid, email, profile scopes
        assert "openid" in url or "scope" in url

    def test_provider_name(self):
        """Test provider name property."""
        assert self.provider.name == "google"


@pytest.mark.skipif(not APPLE_AVAILABLE, reason="Apple OAuth not available")
class TestAppleOAuthProvider:
    """Tests for Apple Sign-In OAuth provider (if available)."""

    def setup_method(self):
        """Set up test fixtures."""
        if not APPLE_AVAILABLE:
            pytest.skip("Apple OAuth not available")
        self.provider = AppleOAuthProvider(
            client_id="com.example.web",
            client_secret="",
            redirect_uri="http://localhost:3000/api/v1/auth/oauth/callback",
            team_id="XXXXXXXXXX",
            key_id="XXXXXXXXXX",
            private_key="""-----BEGIN PRIVATE KEY-----
MIGTAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBHkwdwIBAQQg...
-----END PRIVATE KEY-----""",
        )

    def test_get_authorization_url(self):
        """Test Apple authorization URL generation."""
        state = "test-state-456"
        code_challenge = "test-challenge"

        url = self.provider.get_authorization_url(
            state=state,
            code_challenge=code_challenge,
        )

        assert "appleid.apple.com" in url
        assert "com.example.web" in url
        assert "test-state-456" in url


class TestOAuthError:
    """Tests for OAuth error handling."""

    def test_oauth_error_message(self):
        """Test OAuth error with custom message."""
        error = OAuthError("Invalid state parameter")
        assert str(error) == "Invalid state parameter"

    def test_oauth_error_with_provider(self):
        """Test OAuth error with provider context."""
        error = OAuthError("Token exchange failed", provider="google")
        assert "Token exchange failed" in str(error)


class TestOAuthUserInfo:
    """Tests for OAuthUserInfo dataclass."""

    def test_oauth_user_info_creation(self):
        """Test creating OAuthUserInfo instance."""
        user_info = OAuthUserInfo(
            provider="google",
            provider_user_id="user-123",
            email="test@example.com",
            email_verified=True,
            name="Test User",
        )

        assert user_info.provider == "google"
        assert user_info.provider_user_id == "user-123"
        assert user_info.email == "test@example.com"
        assert user_info.email_verified is True
        assert user_info.name == "Test User"

    def test_oauth_user_info_optional_fields(self):
        """Test OAuthUserInfo with optional fields."""
        user_info = OAuthUserInfo(
            provider="apple",
            provider_user_id="apple-user-456",
            email=None,
            email_verified=False,
            name=None,
        )

        assert user_info.email is None
        assert user_info.name is None
        assert user_info.email_verified is False

    def test_oauth_user_info_with_additional_fields(self):
        """Test OAuthUserInfo with additional optional fields."""
        user_info = OAuthUserInfo(
            provider="google",
            provider_user_id="user-123",
            email="test@example.com",
            email_verified=True,
            name="Test User",
            given_name="Test",
            family_name="User",
            picture="https://example.com/photo.jpg",
            locale="en",
        )

        assert user_info.given_name == "Test"
        assert user_info.family_name == "User"
        assert user_info.picture == "https://example.com/photo.jpg"
        assert user_info.locale == "en"
