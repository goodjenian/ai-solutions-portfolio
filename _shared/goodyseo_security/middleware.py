"""
FastAPI middleware stack:
- Security headers (CSP, HSTS, X-Frame-Options, etc.)
- Request size limiter
- Structured request/response logging + request ID
Adapted from ai-real-estate-assistant (MIT).
"""

import logging
import os
import time
import uuid
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("goodyseo.middleware")

_MAX_BODY_MB = float(os.getenv("MAX_REQUEST_BODY_MB", "10"))
_MAX_BODY_BYTES = int(_MAX_BODY_MB * 1024 * 1024)

_SKIP_RATE_LIMIT = ("/health", "/docs", "/redoc", "/openapi.json", "/metrics")


# ── Security headers ─────────────────────────────────────────────────────────

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    _CSP_DEV = (
        "default-src 'self'; script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
        "connect-src 'self' http://localhost:* ws://localhost:*; "
        "frame-ancestors 'self'; form-action 'self';"
    )
    _CSP_PROD = (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; "
        "form-action 'self'; upgrade-insecure-requests;"
    )
    _PERMISSIONS = (
        "geolocation=(), microphone=(), camera=(), payment=(), usb=()"
    )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        is_prod = os.getenv("ENVIRONMENT", "development").lower() == "production"
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = self._PERMISSIONS
        response.headers["Content-Security-Policy"] = self._CSP_PROD if is_prod else self._CSP_DEV
        if is_prod and request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
        return response


# ── Request size limiter ──────────────────────────────────────────────────────

class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > _MAX_BODY_BYTES:
            return JSONResponse(
                status_code=413,
                content={"detail": f"Request body exceeds {_MAX_BODY_MB}MB limit."},
            )
        return await call_next(request)


# ── Observability (request ID + timing + logging) ────────────────────────────

def add_observability(app: FastAPI) -> None:
    """Attach request ID, timing, and structured logging middleware."""

    @app.middleware("http")
    async def _observe(request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        request.state.request_id = request_id

        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:
            elapsed = (time.perf_counter() - start) * 1000
            logger.exception(
                "unhandled_exception",
                extra={"request_id": request_id, "path": request.url.path,
                       "duration_ms": elapsed},
            )
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error."},
                headers={"X-Request-ID": request_id},
            )

        elapsed = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round(elapsed, 2),
            },
        )
        return response


def apply_all(app: FastAPI) -> None:
    """Apply the full middleware stack to a FastAPI app."""
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestSizeLimitMiddleware)
    add_observability(app)
    logger.info("GoodySEO security middleware stack applied.")
