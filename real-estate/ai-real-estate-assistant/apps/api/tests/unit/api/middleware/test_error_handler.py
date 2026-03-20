"""Unit tests for centralized error handler middleware."""

from unittest.mock import MagicMock, patch

from api.middleware.error_handler import (
    SAFE_ERROR_MESSAGES,
    _build_error_response,
    _is_production,
    _sanitize_error_detail,
)


class TestIsProduction:
    """Tests for _is_production helper."""

    def test_production_environment(self):
        """Returns True when environment is 'production'."""
        with patch("api.middleware.error_handler.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(environment="production")
            assert _is_production() is True

    def test_development_environment(self):
        """Returns False when environment is 'development'."""
        with patch("api.middleware.error_handler.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(environment="development")
            assert _is_production() is False

    def test_local_environment(self):
        """Returns False when environment is 'local'."""
        with patch("api.middleware.error_handler.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(environment="local")
            assert _is_production() is False

    def test_production_case_insensitive(self):
        """Handles uppercase/mixed case 'PRODUCTION'."""
        with patch("api.middleware.error_handler.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(environment="PRODUCTION")
            assert _is_production() is True


class TestSanitizeErrorDetail:
    """Tests for _sanitize_error_detail function."""

    def test_preserves_dict_details(self):
        """Dict details are preserved as-is (structured errors)."""
        detail = {"message": "Error", "errors": ["e1", "e2"]}
        result = _sanitize_error_detail(422, detail, is_production=True)
        assert result == detail

    def test_development_returns_actual_detail(self):
        """Development mode returns actual error detail."""
        result = _sanitize_error_detail(500, "Database connection failed", is_production=False)
        assert result == "Database connection failed"

    def test_production_sanitizes_generic_errors(self):
        """Production mode sanitizes generic internal errors."""
        result = _sanitize_error_detail(500, "Database connection failed", is_production=True)
        assert result == SAFE_ERROR_MESSAGES[500]

    def test_production_allows_safe_prefixes(self):
        """Production allows errors with safe prefixes."""
        safe_details = [
            "Missing user email",
            "Invalid credentials",
            "Unknown provider: foo",
            "Unknown model for provider",
            "No data in cache",
            "No URLs provided",
            "Portal adapter not found",
            "preferred_provider is required",
        ]
        for detail in safe_details:
            result = _sanitize_error_detail(400, detail, is_production=True)
            assert result == detail, f"Expected '{detail}' to pass through"

    def test_production_sanitizes_unknown_status_codes(self):
        """Production uses generic message for unknown status codes."""
        result = _sanitize_error_detail(418, "I'm a teapot", is_production=True)
        assert result == "An error occurred"


class TestBuildErrorResponse:
    """Tests for _build_error_response function."""

    def test_string_detail_includes_metadata(self):
        """String details include status_code and request_id."""
        result = _build_error_response(
            status_code=500,
            detail="Internal error",
            request_id="req-123",
        )
        assert result["detail"] == "Internal error"
        assert result["status_code"] == 500
        assert result["request_id"] == "req-123"

    def test_dict_detail_preserves_structure(self):
        """Dict details preserve structure without extra metadata."""
        detail = {"message": "Validation failed", "errors": ["field required"]}
        result = _build_error_response(
            status_code=422,
            detail=detail,
            request_id="req-456",
        )
        assert result["detail"] == detail
        assert "status_code" not in result
        assert "request_id" not in result

    def test_includes_errors_when_provided(self):
        """Includes errors list when provided with string detail."""
        result = _build_error_response(
            status_code=422,
            detail="Validation error",
            request_id="req-789",
            errors=[{"field": "email", "message": "invalid"}],
        )
        assert result["errors"] == [{"field": "email", "message": "invalid"}]
