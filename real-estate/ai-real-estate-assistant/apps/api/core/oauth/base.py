"""Base OAuth provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


class OAuthError(Exception):
    """OAuth-related error."""

    def __init__(self, message: str, provider: Optional[str] = None):
        self.message = message
        self.provider = provider
        super().__init__(message)


@dataclass
class OAuthUserInfo:
    """Standardized user info from OAuth provider."""

    provider: str
    provider_user_id: str
    email: Optional[str] = None
    email_verified: bool = False
    name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    picture: Optional[str] = None
    locale: Optional[str] = None


class OAuthProvider(ABC):
    """Abstract base class for OAuth providers."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g., 'google', 'apple')."""
        pass

    @abstractmethod
    def get_authorization_url(
        self,
        state: str,
        code_challenge: Optional[str] = None,
        scope: Optional[list[str]] = None,
    ) -> str:
        """
        Generate authorization URL for OAuth flow.

        Args:
            state: Random state string for CSRF protection
            code_challenge: PKCE code challenge (optional)
            scope: OAuth scopes to request

        Returns:
            Authorization URL to redirect user to
        """
        pass

    @abstractmethod
    async def exchange_code(
        self,
        code: str,
        code_verifier: Optional[str] = None,
    ) -> dict:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from callback
            code_verifier: PKCE code verifier (if used)

        Returns:
            Token response with access_token, id_token, etc.

        Raises:
            OAuthError: If exchange fails
        """
        pass

    @abstractmethod
    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """
        Get user info from provider using access token.

        Args:
            access_token: OAuth access token

        Returns:
            Standardized user info

        Raises:
            OAuthError: If request fails
        """
        pass

    async def verify_and_get_user(
        self,
        code: str,
        code_verifier: Optional[str] = None,
    ) -> OAuthUserInfo:
        """
        Exchange code and get user info in one call.

        Args:
            code: Authorization code
            code_verifier: PKCE code verifier

        Returns:
            Standardized user info
        """
        tokens = await self.exchange_code(code, code_verifier)
        access_token = tokens.get("access_token")
        if not access_token:
            raise OAuthError("No access token in response", self.name)
        return await self.get_user_info(access_token)
