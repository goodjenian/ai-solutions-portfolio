"""Google OAuth provider implementation."""

import base64
import hashlib
import secrets
from typing import Optional
from urllib.parse import urlencode

import httpx

from core.oauth.base import OAuthError, OAuthProvider, OAuthUserInfo

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

DEFAULT_SCOPES = [
    "openid",
    "email",
    "profile",
]


class GoogleOAuthProvider(OAuthProvider):
    """Google OAuth 2.0 provider."""

    @property
    def name(self) -> str:
        return "google"

    def get_authorization_url(
        self,
        state: str,
        code_challenge: Optional[str] = None,
        scope: Optional[list[str]] = None,
    ) -> str:
        """
        Generate Google OAuth authorization URL.

        Args:
            state: Random state for CSRF protection
            code_challenge: PKCE code challenge (optional)
            scope: OAuth scopes (defaults to openid, email, profile)

        Returns:
            Google authorization URL
        """
        scopes = scope or DEFAULT_SCOPES

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes),
            "state": state,
            "access_type": "offline",  # Get refresh token
            "prompt": "consent",  # Force consent screen
        }

        # Add PKCE parameters if provided
        if code_challenge:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"

        return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    async def exchange_code(
        self,
        code: str,
        code_verifier: Optional[str] = None,
    ) -> dict:
        """
        Exchange authorization code for tokens.

        Args:
            code: Authorization code from Google
            code_verifier: PKCE code verifier (if used)

        Returns:
            Token response with access_token, id_token, etc.

        Raises:
            OAuthError: If exchange fails
        """
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }

        if code_verifier:
            data["code_verifier"] = code_verifier

        async with httpx.AsyncClient() as client:
            response = await client.post(
                GOOGLE_TOKEN_URL,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

        if response.status_code != 200:
            error_data = response.json() if response.content else {}
            error_msg = error_data.get("error_description", response.text)
            raise OAuthError(f"Token exchange failed: {error_msg}", self.name)

        return response.json()

    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """
        Get user info from Google.

        Args:
            access_token: OAuth access token

        Returns:
            Standardized user info

        Raises:
            OAuthError: If request fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )

        if response.status_code != 200:
            raise OAuthError(
                f"Failed to get user info: {response.text}",
                self.name,
            )

        data = response.json()

        return OAuthUserInfo(
            provider=self.name,
            provider_user_id=data.get("sub", ""),
            email=data.get("email"),
            email_verified=data.get("email_verified", False),
            name=data.get("name"),
            given_name=data.get("given_name"),
            family_name=data.get("family_name"),
            picture=data.get("picture"),
            locale=data.get("locale"),
        )

    @staticmethod
    def generate_pkce_verifier() -> str:
        """Generate a PKCE code verifier."""
        return secrets.token_urlsafe(64)[:128]

    @staticmethod
    def generate_pkce_challenge(verifier: str) -> str:
        """Generate PKCE code challenge from verifier."""
        digest = hashlib.sha256(verifier.encode()).digest()
        return base64.urlsafe_b64encode(digest).decode().rstrip("=")
