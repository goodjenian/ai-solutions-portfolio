from unittest.mock import patch

from fastapi import APIRouter, HTTPException
from fastapi.testclient import TestClient

from api.main import app

# Create a test router with endpoints that raise errors
test_router = APIRouter(prefix="/test-errors")


@test_router.get("/500")
async def trigger_500():
    raise Exception("This is a sensitive internal error")


@test_router.get("/400")
async def trigger_400():
    raise HTTPException(status_code=400, detail="Invalid input parameter")


@test_router.get("/422-dict")
async def trigger_422_dict():
    # Simulate Pydantic-like validation error structure
    raise HTTPException(
        status_code=422, detail={"message": "Validation failed", "errors": ["Field X is required"]}
    )


# Mount the router to the app for testing
app.include_router(test_router)

client = TestClient(app)


def test_production_hides_sensitive_errors():
    """Test that 500 errors are sanitized in production."""
    with patch("api.middleware.error_handler.get_settings") as mock_settings:
        mock_settings.return_value.environment = "production"

        response = client.get("/test-errors/500")
        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Internal server error"
        assert "sensitive" not in str(data)
        assert "request_id" in data


def test_development_shows_sensitive_errors():
    """Test that 500 errors are shown in development."""
    with patch("api.middleware.error_handler.get_settings") as mock_settings:
        mock_settings.return_value.environment = "development"

        response = client.get("/test-errors/500")
        assert response.status_code == 500
        data = response.json()
        assert "This is a sensitive internal error" in data["detail"]


def test_production_allows_safe_errors():
    """Test that 400 errors are passed through in production."""
    with patch("api.middleware.error_handler.get_settings") as mock_settings:
        mock_settings.return_value.environment = "production"

        response = client.get("/test-errors/400")
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Invalid input parameter"


def test_structured_errors_preserved():
    """Test that dict details are preserved."""
    with patch("api.middleware.error_handler.get_settings") as mock_settings:
        mock_settings.return_value.environment = "production"

        response = client.get("/test-errors/422-dict")
        assert response.status_code == 422
        data = response.json()
        assert data["detail"]["message"] == "Validation failed"
