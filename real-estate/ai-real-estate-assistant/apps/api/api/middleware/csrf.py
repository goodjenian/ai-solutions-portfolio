"""CSRF Protection Middleware.

Implements double-submit cookie pattern for CSRF protection:
- Validates X-CSRF-Token header on state-changing requests (POST, PUT, DELETE, PATCH)
- Compares header value with csrf_token cookie
- Skips validation for safe methods (GET, HEAD, OPTIONS)
"""

import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Safe methods that don't require CSRF protection
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF protection middleware using double-submit cookie pattern.

    For state-changing requests (POST, PUT, DELETE, PATCH):
    1. Reads csrf_token from cookies
    2. Validates X-CSRF-Token header matches the cookie
    3. Returns 403 Forbidden if validation fails

    For safe requests (GET, HEAD, OPTIONS):
    - CSRF validation is skipped
    """

    # Paths to exclude from CSRF validation
    EXCLUDED_PATHS = {
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/metrics",
    }

    # Path prefixes to exclude
    EXCLUDED_PREFIXES = (
        "/api/v1/auth/oauth/",  # OAuth callbacks use GET
    )

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        """Process request and validate CSRF token for state-changing requests."""
        import os

        # Skip CSRF in test/local environment
        env = os.environ.get("ENVIRONMENT", "").lower()
        if env in ("test", "local"):
            return await call_next(request)

        # Skip CSRF for safe methods
        if request.method in SAFE_METHODS:
            return await call_next(request)

        # Skip CSRF for excluded paths
        path = request.url.path
        if path in self.EXCLUDED_PATHS:
            return await call_next(request)

        # Skip CSRF for excluded prefixes
        for prefix in self.EXCLUDED_PREFIXES:
            if path.startswith(prefix):
                return await call_next(request)

        # Get CSRF token from cookie
        cookie_token = request.cookies.get("csrf_token")

        # Get CSRF token from header
        header_token = request.headers.get("X-CSRF-Token")

        # Validate tokens match
        if not cookie_token or not header_token:
            logger.warning(
                "csrf_validation_failed",
                extra={
                    "event": "csrf_validation_failed",
                    "reason": "missing_token",
                    "path": path,
                    "method": request.method,
                    "has_cookie": bool(cookie_token),
                    "has_header": bool(header_token),
                },
            )
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token missing"},
            )

        if cookie_token != header_token:
            logger.warning(
                "csrf_validation_failed",
                extra={
                    "event": "csrf_validation_failed",
                    "reason": "token_mismatch",
                    "path": path,
                    "method": request.method,
                },
            )
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token mismatch"},
            )

        # CSRF validation passed
        return await call_next(request)


def add_csrf_middleware(app) -> None:
    """Add CSRF middleware to the FastAPI application.

    Args:
        app: FastAPI application instance
    """
    app.add_middleware(CSRFMiddleware)
    logger.info("CSRF middleware added to application")
