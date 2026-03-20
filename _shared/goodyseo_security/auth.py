"""
API Key authentication — constant-time comparison, audit-logged.
Supports multiple keys (one per client/plan tier).
Adapted from ai-real-estate-assistant (MIT).

Usage in FastAPI:
    from goodyseo_security.auth import get_api_key
    @app.post("/run", dependencies=[Depends(get_api_key)])
"""

import hmac
import logging
import os
from typing import Optional

from fastapi import HTTPException, Request, Security, status
from fastapi.security.api_key import APIKeyHeader

from .audit import get_audit_logger

logger = logging.getLogger("goodyseo.auth")
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _load_valid_keys() -> list[str]:
    """Load API keys from env. Supports comma-separated list or single key."""
    multi = os.getenv("API_ACCESS_KEYS", "")
    if multi:
        keys = [k.strip() for k in multi.split(",") if k.strip()]
        if keys:
            return keys
    single = os.getenv("API_ACCESS_KEY", "").strip()
    return [single] if single else []


def _constant_time_check(candidate: str, valid_keys: list[str]) -> bool:
    """Prevent timing attacks via hmac.compare_digest for every key."""
    result = False
    for key in valid_keys:
        if key and hmac.compare_digest(candidate, key):
            result = True
    return result


async def get_api_key(
    request: Request,
    raw_key: Optional[str] = Security(_api_key_header),
) -> str:
    """
    FastAPI dependency — validates X-API-Key header.

    Returns the validated key on success.
    Raises HTTP 401/403 on failure (always logs to audit).
    """
    audit = get_audit_logger()
    request_id: str = getattr(request.state, "request_id", "unknown")

    candidate = (raw_key or "").strip()
    if not candidate:
        audit.log_auth_failure(
            reason="missing_api_key",
            request_id=request_id,
            path=request.url.path,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide X-API-Key header.",
        )

    environment = os.getenv("ENVIRONMENT", "development").strip().lower()
    valid_keys = _load_valid_keys()

    if environment == "production" and not valid_keys:
        logger.critical("No API keys configured in production!")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Service misconfigured.")

    # Dev fallback: if no keys configured, allow any non-empty key with a warning
    if not valid_keys and environment != "production":
        logger.warning(
            "No API_ACCESS_KEY(S) configured — running in open dev mode. "
            "Set API_ACCESS_KEY in .env before deploying."
        )
        audit.log_auth_success(client_id=candidate, request_id=request_id)
        return candidate

    if _constant_time_check(candidate, valid_keys):
        audit.log_auth_success(client_id=candidate, request_id=request_id)
        return candidate

    audit.log_auth_failure(
        reason="invalid_key",
        request_id=request_id,
        path=request.url.path,
    )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Invalid API key.",
    )
