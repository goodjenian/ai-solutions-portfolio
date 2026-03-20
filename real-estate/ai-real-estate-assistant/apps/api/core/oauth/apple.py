"""Apple Sign-In OAuth provider implementation.

Apple Sign-In uses a different flow than standard OAuth:
1. Client secret is a JWT signed with the Apple private key
2. ID token validation uses Apple's public keys
3. User info may only be provided on first login
"""

import base64
import hashlib
import json
import secrets
import time
from typing import Optional
from urllib.parse import urlencode

import httpx
import jwt

from core.oauth.base import OAuthError, OAuthProvider, OAuthUserInfo

APPLE_AUTH_URL = "https://appleid.apple.com/auth/authorize"
APPLE_TOKEN_URL = "https://appleid.apple.com/auth/token"
APPLE_KEYS_URL = "https://appleid.apple.com/auth/keys"

DEFAULT_SCOPES = ["email", "name"]


class AppleOAuthProvider(OAuthProvider):
    """Apple Sign-In OAuth 2.0 provider."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,  # Not used for Apple, but required by base class
        redirect_uri: str,
        team_id: str,
        key_id: str,
        private_key: str,
    ):
        super().__init__(client_id, client_secret, redirect_uri)
        self.team_id = team_id
        self.key_id = key_id
        self.private_key = private_key
        self._cached_keys: Optional[dict] = None
        self._keys_cache_time: float = 0

    @property
    def name(self) -> str:
        return "apple"

    def _generate_client_secret(self) -> str:
        """Generate Apple client secret JWT.

        Apple requires a JWT signed with the private key as the client secret.
        """
        now = int(time.time())
        payload = {
            "iss": self.team_id,
            "iat": now,
            "exp": now + 3600 * 24 * 180,  # 6 months max
            "aud": "https://appleid.apple.com",
            "sub": self.client_id,
        }
        headers = {
            "kid": self.key_id,
            "alg": "ES256",
        }
        return jwt.encode(payload, self.private_key, algorithm="ES256", headers=headers)

    def get_authorization_url(
        self,
        state: str,
        code_challenge: Optional[str] = None,
        scope: Optional[list[str]] = None,
    ) -> str:
        """Generate Apple authorization URL.

        Args:
            state: Random state for CSRF protection
            code_challenge: PKCE code challenge (optional, Apple supports this)
            scope: OAuth scopes (defaults to email, name)

        Returns:
            Apple authorization URL
        """
        scopes = scope or DEFAULT_SCOPES

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes),
            "state": state,
            "response_mode": "form_post",  # Apple requires form_post for security
        }

        # Apple supports PKCE
        if code_challenge:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"

        return f"{APPLE_AUTH_URL}?{urlencode(params)}"

    async def exchange_code(
        self,
        code: str,
        code_verifier: Optional[str] = None,
    ) -> dict:
        """Exchange authorization code for tokens.

        Args:
            code: Authorization code from Apple
            code_verifier: PKCE code verifier (if used)

        Returns:
            Token response with access_token, id_token, etc.

        Raises:
            OAuthError: If exchange fails
        """
        client_secret = self._generate_client_secret()

        data = {
            "client_id": self.client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }

        if code_verifier:
            data["code_verifier"] = code_verifier

        async with httpx.AsyncClient() as client:
            response = await client.post(
                APPLE_TOKEN_URL,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

        if response.status_code != 200:
            error_data = response.json() if response.content else {}
            error_msg = error_data.get("error_description", response.text)
            raise OAuthError(f"Token exchange failed: {error_msg}", self.name)

        return response.json()

    async def _get_apple_public_keys(self) -> list[dict]:
        """Fetch Apple's public keys for token verification."""
        # Cache keys for 1 hour
        if self._cached_keys and time.time() - self._keys_cache_time < 3600:
            return self._cached_keys

        async with httpx.AsyncClient() as client:
            response = await client.get(APPLE_KEYS_URL)

        if response.status_code != 200:
            raise OAuthError("Failed to fetch Apple public keys", self.name)

        data = response.json()
        self._cached_keys = data.get("keys", [])
        self._keys_cache_time = time.time()
        return self._cached_keys

    async def _verify_id_token(self, id_token: str) -> dict:
        """Verify Apple ID token and return payload."""
        # Get the token header to find the key ID
        unverified_header = jwt.get_unverified_header(id_token)
        kid = unverified_header.get("kid")

        if not kid:
            raise OAuthError("Invalid ID token: missing key ID", self.name)

        # Get Apple's public keys
        keys = await self._get_apple_public_keys()

        # Find the matching key
        matching_key = None
        for key in keys:
            if key.get("kid") == kid:
                matching_key = key
                break

        if not matching_key:
            raise OAuthError("Invalid ID token: key not found", self.name)

        # Convert JWK to PEM
        from jwt.algorithms import RSAAlgorithm

        public_key = RSAAlgorithm.from_jwk(json.dumps(matching_key))

        # Verify and decode the token
        try:
            payload = jwt.decode(
                id_token,
                public_key,
                algorithms=["RS256"],
                audience=self.client_id,
                issuer="https://appleid.apple.com",
            )
            return payload
        except jwt.ExpiredSignatureError as e:
            raise OAuthError("ID token has expired", self.name) from e
        except jwt.InvalidTokenError as e:
            raise OAuthError(f"Invalid ID token: {e}", self.name) from e

    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """Get user info from Apple.

        Note: Apple doesn't have a userinfo endpoint.
        User info must be extracted from the ID token.

        This method is not typically used for Apple Sign-In.
        Use verify_and_get_user instead.

        Args:
            access_token: Apple access token (actually the ID token)

        Returns:
            Standardized user info
        """
        # For Apple, the access_token is used to get the ID token payload
        # This is a simplified implementation
        raise OAuthError(
            "Use verify_and_get_user for Apple Sign-In",
            self.name,
        )

    async def verify_and_get_user(
        self,
        code: str,
        code_verifier: Optional[str] = None,
    ) -> OAuthUserInfo:
        """Exchange code and get user info from ID token.

        Args:
            code: Authorization code
            code_verifier: PKCE code verifier

        Returns:
            Standardized user info
        """
        tokens = await self.exchange_code(code, code_verifier)
        id_token = tokens.get("id_token")

        if not id_token:
            raise OAuthError("No ID token in Apple response", self.name)

        # Verify and decode the ID token
        payload = await self._verify_id_token(id_token)

        # Extract user info from ID token
        # Apple may provide email in the ID token
        email = payload.get("email")
        email_verified = payload.get("email_verified", False)

        # The 'sub' claim is the unique user identifier
        user_id = payload.get("sub", "")

        return OAuthUserInfo(
            provider=self.name,
            provider_user_id=user_id,
            email=email,
            email_verified=bool(email_verified),
            name=None,  # Apple doesn't provide name in ID token
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

    def parse_user_info_from_form_post(self, form_data: dict) -> Optional[OAuthUserInfo]:
        """Parse user info from Apple's form_post response.

        On first login, Apple may include user info in the form POST.
        This should be combined with the ID token info.

        Args:
            form_data: Form data from Apple's POST request

        Returns:
            User info if available
        """
        user_json = form_data.get("user")
        if not user_json:
            return None

        try:
            user_data = json.loads(user_json)
            name_info = user_data.get("name", {})
            return OAuthUserInfo(
                provider=self.name,
                provider_user_id="",  # Must be combined with ID token
                email=user_data.get("email"),
                email_verified=False,
                name=name_info.get("firstName") or name_info.get("lastName"),
                given_name=name_info.get("firstName"),
                family_name=name_info.get("lastName"),
            )
        except json.JSONDecodeError:
            return None
