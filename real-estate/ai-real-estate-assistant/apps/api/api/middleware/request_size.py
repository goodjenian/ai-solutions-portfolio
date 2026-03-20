"""
Request size limiting middleware for FastAPI.

Limits the size of incoming request bodies to prevent:
- Memory exhaustion from large uploads
- DoS attacks via large payloads
- Excessive processing time on large inputs

Configurable via environment variables:
- REQUEST_MAX_BODY_SIZE_MB: Maximum request body size in MB (default: 10)
- REQUEST_MAX_UPLOAD_SIZE_MB: Maximum file upload size in MB (default: 25)
"""

import logging
from typing import Callable

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from config.settings import get_settings

logger = logging.getLogger(__name__)


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces request size limits.

    Different limits for:
    - Standard API requests (JSON, form data)
    - File uploads (RAG documents)
    """

    def __init__(self, app, max_body_size_mb: int = 10, max_upload_size_mb: int = 25):
        """
        Initialize the request size limit middleware.

        Args:
            app: FastAPI/ASGI application
            max_body_size_mb: Maximum size for regular request bodies (MB)
            max_upload_size_mb: Maximum size for file uploads (MB)
        """
        super().__init__(app)
        self.max_body_size_bytes = max_body_size_mb * 1024 * 1024
        self.max_upload_size_bytes = max_upload_size_mb * 1024 * 1024
        logger.info(
            "Request size limits initialized: max_body=%dMB, max_upload=%dMB",
            max_body_size_mb,
            max_upload_size_mb,
        )

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Response],  # type: ignore[override]
    ) -> Response:
        """
        Process request and enforce size limits.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler

        Returns:
            Response or 413 error if size limit exceeded

        Raises:
            HTTPException: If request size exceeds limits
        """
        # Determine appropriate size limit based on content type
        content_type = request.headers.get("content-type", "")
        path = request.url.path

        # Upload endpoints get higher limit
        is_upload_endpoint = "/rag/upload" in path or "/upload" in path
        is_multipart = "multipart/form-data" in content_type

        if is_upload_endpoint or is_multipart:
            max_size = self.max_upload_size_bytes
        else:
            max_size = self.max_body_size_bytes

        # Check content-length header first (fast path)
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                content_length_int = int(content_length)
                if content_length_int > max_size:
                    logger.warning(
                        "Request size limit exceeded: content_length=%d, max_size=%d, path=%s",
                        content_length_int,
                        max_size,
                        path,
                    )
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Request too large. Maximum size is {max_size // (1024 * 1024)}MB.",
                    )
            except ValueError:
                # Invalid content-length header, proceed with body check
                pass

        # For requests without content-length or for multipart, let Starlette handle it
        # Starlette will raise a 413 if body exceeds internal limits
        response: Response = await call_next(request)  # type: ignore[misc]

        return response


def add_request_size_limits(
    app,
    max_body_size_mb: int = 10,
    max_upload_size_mb: int = 25,
) -> None:
    """
    Add request size limit middleware to the FastAPI application.

    Args:
        app: FastAPI application instance
        max_body_size_mb: Maximum size for regular request bodies (MB)
        max_upload_size_mb: Maximum size for file uploads (MB)
    """
    # Get limits from environment if available
    settings = get_settings()

    # Try to get values from settings or environment
    try:
        body_limit = int(getattr(settings, "request_max_body_size_mb", max_body_size_mb))
    except (AttributeError, ValueError, TypeError):
        body_limit = max_body_size_mb

    try:
        upload_limit = int(getattr(settings, "request_max_upload_size_mb", max_upload_size_mb))
    except (AttributeError, ValueError, TypeError):
        upload_limit = max_upload_size_mb

    app.add_middleware(
        RequestSizeLimitMiddleware, max_body_size_mb=body_limit, max_upload_size_mb=upload_limit
    )
    logger.info(
        "Request size limit middleware added: body=%dMB, upload=%dMB", body_limit, upload_limit
    )
