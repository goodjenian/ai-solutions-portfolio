"""OAuth integration module."""

from core.oauth.base import OAuthError, OAuthProvider, OAuthUserInfo
from core.oauth.google import GoogleOAuthProvider

# Apple OAuth is optional - requires ES256 private key
try:
    from core.oauth.apple import AppleOAuthProvider
except ImportError:
    AppleOAuthProvider = None  # type: ignore[misc,assignment]

__all__ = [
    "OAuthError",
    "OAuthProvider",
    "OAuthUserInfo",
    "GoogleOAuthProvider",
    "AppleOAuthProvider",
]
