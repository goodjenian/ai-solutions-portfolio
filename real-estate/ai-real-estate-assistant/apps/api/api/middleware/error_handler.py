"""
Centralized error handling middleware for FastAPI.

Provides:
- Production-safe error message sanitization
- Consistent error response format
- Structured logging for all errors
- Request correlation via request_id
"""

import logging
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from config.settings import get_settings

logger = logging.getLogger(__name__)

# Error messages that are safe to expose in production
SAFE_ERROR_MESSAGES = {
    400: "Bad request",
    401: "Invalid credentials",
    403: "Access denied",
    404: "Resource not found",
    405: "Method not allowed",
    409: "Conflict",
    422: "Validation error",
    429: "Too many requests",
    500: "Internal server error",
    502: "Bad gateway",
    503: "Service unavailable",
    504: "Gateway timeout",
}


def _is_production() -> bool:
    """Check if running in production environment."""
    settings = get_settings()
    environment = getattr(settings, "environment", "development")
    return str(environment).strip().lower() == "production"


def _get_request_id(request: Request) -> str:
    """Extract request ID from request state."""
    return getattr(request.state, "request_id", "unknown")


def _sanitize_error_detail(
    status_code: int,
    detail: Any,
    is_production: bool,
) -> Any:
    """
    Sanitize error detail for response.

    In production: Returns generic safe message (or preserves safe structured details)
    In development: Returns actual error detail
    """
    # Preserve structured detail objects (dicts) - these are intentionally formatted
    # by the endpoint for user-facing error messages
    if isinstance(detail, dict):
        return detail

    if not is_production:
        # Development: return actual detail
        if isinstance(detail, str):
            return detail
        return str(detail)

    # Production: return safe generic message
    # Allow specific HTTPException details that are intentionally user-facing
    if isinstance(detail, str):
        # Check if this looks like a user-facing validation error
        safe_prefixes = (
            "Missing",
            "Invalid",
            "Unknown provider",
            "Unknown model",
            "No data",
            "No URLs",
            "Portal adapter",
            "preferred_provider is required",
        )
        if any(detail.startswith(prefix) for prefix in safe_prefixes):
            return detail

    return SAFE_ERROR_MESSAGES.get(status_code, "An error occurred")


def _build_error_response(
    status_code: int,
    detail: Any,
    request_id: str,
    errors: Optional[list[dict[str, Any]]] = None,
    wrap_detail: bool = True,
) -> dict[str, Any]:
    """
    Build consistent error response structure.

    When detail is already a dict (structured error from endpoint), it's preserved as-is
    in the 'detail' field for backward compatibility with existing API consumers.
    """
    response: dict[str, Any] = {
        "detail": detail,
    }

    # Only add extra fields if detail is not already structured
    if not isinstance(detail, dict):
        response["status_code"] = status_code
        response["request_id"] = request_id
        if errors:
            response["errors"] = errors

    return response


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle HTTPException with sanitization.

    Logs the error with full context and returns sanitized response.
    """
    request_id = _get_request_id(request)
    is_production = _is_production()

    # Log the actual error for debugging
    logger.warning(
        "HTTP exception",
        extra={
            "event": "http_exception",
            "request_id": request_id,
            "status_code": exc.status_code,
            "detail": str(exc.detail),
            "path": request.url.path,
            "method": request.method,
        },
    )

    # Sanitize the detail for response
    sanitized_detail = _sanitize_error_detail(
        exc.status_code,
        exc.detail,
        is_production,
    )

    response_body = _build_error_response(
        status_code=exc.status_code,
        detail=sanitized_detail,
        request_id=request_id,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=response_body,
        headers=exc.headers,
    )


async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """
    Handle Pydantic ValidationError with structured error details.

    Validation errors are generally safe to expose as they relate to input format.
    """
    request_id = _get_request_id(request)

    # Extract validation errors
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "field": ".".join(str(loc) for loc in error.get("loc", [])),
                "message": error.get("msg", "Invalid value"),
                "type": error.get("type", "value_error"),
            }
        )

    logger.warning(
        "Validation error",
        extra={
            "event": "validation_error",
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "error_count": len(errors),
        },
    )

    response_body = _build_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Validation error",
        request_id=request_id,
        errors=errors,
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response_body,
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions with full sanitization.

    Logs the full traceback but returns sanitized response.
    """
    request_id = _get_request_id(request)
    is_production = _is_production()

    # Log the full error with traceback for debugging
    logger.error(
        "Unhandled exception",
        extra={
            "event": "unhandled_exception",
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
        },
        exc_info=True,
    )

    # Build response
    if is_production:
        detail = SAFE_ERROR_MESSAGES[500]
    else:
        # Include more detail in development
        detail = f"{type(exc).__name__}: {str(exc)}"

    response_body = _build_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=detail,
        request_id=request_id,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_body,
    )


def add_error_handlers(app: FastAPI) -> None:
    """
    Add centralized error handlers to the FastAPI application.

    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(ValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, general_exception_handler)
    logger.info("Centralized error handlers added to application")
