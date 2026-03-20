"""
Security headers middleware for FastAPI.

Adds security-related HTTP headers to all responses:
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY (or SAMEORIGIN for development)
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security: max-age=31536000; includeSubDomains (production only)
- Content-Security-Policy: restrictive policy for frontend
- Referrer-Policy: strict-origin-when-cross-origin
- Permissions-Policy: restricts browser features
"""

import logging
from typing import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from config.settings import get_settings

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds security headers to all HTTP responses.

    Security headers included:
    - X-Content-Type-Options: Prevents MIME type sniffing
    - X-Frame-Options: Prevents clickjacking attacks
    - X-XSS-Protection: Enables browser XSS filter
    - Strict-Transport-Security: Enforces HTTPS (production only)
    - Content-Security-Policy: Controls resource loading
    - Referrer-Policy: Controls referrer information
    - Permissions-Policy: Restricts browser features/capabilities
    """

    # CSP for development (more permissive)
    CSP_DEV = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https://tiles.mapbox.com https://*.tile.openstreetmap.org; "
        "font-src 'self'; "
        "connect-src 'self' http://localhost:* http://127.0.0.1:* ws://localhost:* ws://127.0.0.1:*; "
        "frame-ancestors 'self'; "
        "form-action 'self'; "
        "base-uri 'self';"
    )

    # CSP for production (strict)
    CSP_PROD = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https://tiles.mapbox.com https://*.tile.openstreetmap.org; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "form-action 'self'; "
        "base-uri 'self'; "
        "upgrade-insecure-requests;"
    )

    # Permissions-Policy (restrict browser features)
    PERMISSIONS_POLICY = (
        "geolocation=(), "
        "microphone=(), "
        "camera=(), "
        "payment=(), "
        "usb=(), "
        "magnetometer=(), "
        "gyroscope=(), "
        "accelerometer=()"
    )

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Response],  # type: ignore[override]
    ) -> Response:
        """
        Process request and add security headers to response.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler

        Returns:
            Response with security headers added
        """
        settings = get_settings()
        environment = settings.environment if hasattr(settings, "environment") else "development"
        is_production = environment.strip().lower() == "production"

        # Get the response from the next middleware/route
        response: Response = await call_next(request)  # type: ignore[misc]

        # Add security headers
        # Prevents MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevents clickjacking (DENY in production, SAMEORIGIN for dev if needed)
        response.headers["X-Frame-Options"] = "DENY"

        # Enables browser XSS filter (legacy, but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # HSTS: Enforces HTTPS in production (1 year)
        if is_production and request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # CSP: Controls resource loading
        response.headers["Content-Security-Policy"] = (
            self.CSP_PROD if is_production else self.CSP_DEV
        )

        # Referrer-Policy: Controls referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy: Restricts browser features
        response.headers["Permissions-Policy"] = self.PERMISSIONS_POLICY

        # Cross-Origin Opener Policy: Isolates top-level window
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"

        # Cross-Origin Embedder Policy: Requires CORP/COEP for certain features
        # response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"

        # Cache security for API responses
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        return response


def add_security_headers(app: FastAPI) -> None:
    """
    Add security headers middleware to the FastAPI application.

    Args:
        app: FastAPI application instance
    """
    # Add the security headers middleware
    # The middleware should be added before other middleware for proper ordering
    app.add_middleware(SecurityHeadersMiddleware)
    logger.info("Security headers middleware added to application")
