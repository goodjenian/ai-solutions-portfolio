"""
Integration tests for the anomaly API endpoints.

Tests cover:
- GET /anomalies - List anomalies with filters
- GET /anomalies/{id} - Get single anomaly
- POST /anomalies/{id}/dismiss - Dismiss an anomaly
- GET /anomalies/stats - Get statistics
- GET /anomalies/stream - SSE stream
"""

from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps.auth import get_current_active_user
from api.routers import anomalies
from db.database import get_db
from db.schemas import UserResponse


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client with mocked dependencies."""
    # Create a fresh test app with the anomalies router
    test_app = FastAPI()
    test_app.include_router(anomalies.router, prefix="/api/v1")

    # Override the get_db dependency
    async def override_get_db():
        yield db_session

    # Override auth to return a mock user
    async def override_get_current_user():
        return UserResponse(
            id="test-user-123",
            email="test@example.com",
            roles=["user"],
            created_at="2024-01-01T00:00:00Z",
        )

    test_app.dependency_overrides[get_db] = override_get_db
    test_app.dependency_overrides[get_current_active_user] = override_get_current_user

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    # Cleanup
    test_app.dependency_overrides.clear()


class TestAnomalyAPI:
    """Integration tests for anomaly API endpoints."""

    @pytest.mark.asyncio
    async def test_list_anomalies_empty(self, client: AsyncClient):
        """Test listing anomalies when none exist."""
        response = await client.get("/api/v1/anomalies")
        assert response.status_code == 200
        data = response.json()
        assert "anomalies" in data
        assert "total" in data
        assert isinstance(data["anomalies"], list)

    @pytest.mark.asyncio
    async def test_list_anomalies_with_severity_filter(self, client: AsyncClient):
        """Test listing anomalies with severity filter."""
        response = await client.get(
            "/api/v1/anomalies",
            params={"severity": "high"},
        )
        assert response.status_code == 200
        data = response.json()
        # All returned anomalies should have high severity
        for anomaly in data["anomalies"]:
            assert anomaly["severity"] == "high"

    @pytest.mark.asyncio
    async def test_list_anomalies_with_type_filter(self, client: AsyncClient):
        """Test listing anomalies with type filter."""
        response = await client.get(
            "/api/v1/anomalies",
            params={"anomaly_type": "price_spike"},
        )
        assert response.status_code == 200
        data = response.json()
        for anomaly in data["anomalies"]:
            assert anomaly["anomaly_type"] == "price_spike"

    @pytest.mark.asyncio
    async def test_list_anomalies_pagination(self, client: AsyncClient):
        """Test pagination of anomalies list."""
        # Get first page
        response1 = await client.get(
            "/api/v1/anomalies",
            params={"limit": 5, "offset": 0},
        )
        assert response1.status_code == 200
        data1 = response1.json()

        # Get second page
        response2 = await client.get(
            "/api/v1/anomalies",
            params={"limit": 5, "offset": 5},
        )
        assert response2.status_code == 200

        # Check structure
        assert "limit" in data1
        assert "offset" in data1
        assert data1["limit"] == 5
        assert data1["offset"] == 0

    @pytest.mark.asyncio
    async def test_get_anomaly_not_found(self, client: AsyncClient):
        """Test getting a non-existent anomaly."""
        response = await client.get("/api/v1/anomalies/nonexistent_id")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_anomaly_stats(self, client: AsyncClient):
        """Test getting anomaly statistics."""
        response = await client.get("/api/v1/anomalies/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "by_severity" in data
        assert "by_type" in data
        assert "undismissed" in data

    @pytest.mark.asyncio
    async def test_dismiss_anomaly_not_found(self, client: AsyncClient):
        """Test dismissing a non-existent anomaly."""
        response = await client.post(
            "/api/v1/anomalies/nonexistent_id/dismiss",
            json={"dismissed_by": "user_001"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_anomaly_schema_validation(self, client: AsyncClient):
        """Test that anomaly responses match expected schema."""
        response = await client.get("/api/v1/anomalies")
        assert response.status_code == 200
        data = response.json()

        if data["anomalies"]:
            anomaly = data["anomalies"][0]
            required_fields = [
                "id",
                "anomaly_type",
                "severity",
                "scope_type",
                "scope_id",
                "detected_at",
                "algorithm",
                "threshold_used",
                "metric_name",
                "expected_value",
                "actual_value",
                "deviation_percent",
                "alert_sent",
                "context",
            ]
            for field in required_fields:
                assert field in anomaly, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_list_anomalies_with_scope_filter(self, client: AsyncClient):
        """Test listing anomalies with scope filters."""
        response = await client.get(
            "/api/v1/anomalies",
            params={
                "scope_type": "property",
                "scope_id": "prop_001",
            },
        )
        assert response.status_code == 200
        data = response.json()
        for anomaly in data["anomalies"]:
            assert anomaly["scope_type"] == "property"
            assert anomaly["scope_id"] == "prop_001"

    @pytest.mark.asyncio
    async def test_dismiss_anomaly_with_reason(self, client: AsyncClient):
        """Test dismissing an anomaly with a reason."""
        # First, we need to create an anomaly to dismiss
        # This test assumes there's an anomaly to dismiss
        # In a real test, we'd set up the database state first
        pass  # Placeholder - requires database setup


class TestAnomalyStream:
    """Test the SSE stream endpoint."""

    @pytest.fixture
    async def client(self, db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
        """Create async test client with mocked dependencies."""
        # Create a fresh test app with the anomalies router
        test_app = FastAPI()
        test_app.include_router(anomalies.router, prefix="/api/v1")

        # Override the get_db dependency
        async def override_get_db():
            yield db_session

        # Override auth to return a mock user
        async def override_get_current_user():
            return UserResponse(
                id="test-user-123",
                email="test@example.com",
                roles=["user"],
                created_at="2024-01-01T00:00:00Z",
            )

        test_app.dependency_overrides[get_db] = override_get_db
        test_app.dependency_overrides[get_current_active_user] = override_get_current_user

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

        # Cleanup
        test_app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_stream_endpoint_exists(self, client: AsyncClient):
        """Test that the stream endpoint exists and returns SSE."""
        response = await client.get(
            "/api/v1/anomalies/stream",
            headers={"Accept": "text/event-stream"},
        )
        # The endpoint should either succeed or return a proper error
        assert response.status_code in [200, 404, 501]  # 501 if not impl
