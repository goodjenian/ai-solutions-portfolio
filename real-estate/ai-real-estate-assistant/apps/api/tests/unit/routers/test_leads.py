"""
Tests for Lead Scoring and Tracking API endpoints.

Task #58: Comprehensive Test Suite Update
"""

from collections.abc import AsyncGenerator
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps.auth import get_current_active_user
from api.routers import leads
from db.database import get_db


@pytest.fixture
def mock_admin():
    """Create a mock admin user."""
    user = MagicMock()
    user.id = "admin-123"
    user.email = "admin@example.com"
    user.role = "admin"
    return user


@pytest.fixture
def mock_lead():
    """Create a mock lead."""
    lead = MagicMock()
    lead.id = "lead-123"
    lead.visitor_id = "visitor-abc"
    lead.email = "lead@example.com"
    lead.status = "new"
    lead.current_score = 75
    lead.created_at = datetime(2024, 1, 1)
    lead.updated_at = datetime(2024, 1, 15)
    return lead


@pytest.fixture(scope="function")
async def leads_client(
    mock_admin: MagicMock,
    db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """Create test client for leads endpoints."""
    test_app = FastAPI()
    test_app.include_router(leads.router, prefix="/api/v1")

    async def override_get_db():
        yield db_session

    async def override_get_current_user():
        return mock_admin

    test_app.dependency_overrides[get_db] = override_get_db
    test_app.dependency_overrides[get_current_active_user] = override_get_current_user

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    test_app.dependency_overrides.clear()


class TestUpdateLeadStatus:
    """Tests for updating lead status."""

    @pytest.mark.asyncio
    async def test_update_status_invalid(self, leads_client: AsyncClient):
        """Verify error for invalid status."""
        response = await leads_client.patch(
            "/api/v1/leads/lead-123/status",
            params={"status": "invalid"},
        )

        assert response.status_code == 400


class TestDeleteLead:
    """Tests for lead deletion."""

    @pytest.mark.asyncio
    async def test_delete_success(
        self,
        leads_client: AsyncClient,
        mock_lead: MagicMock,
    ):
        """Verify successful lead deletion."""
        with patch("api.routers.leads.LeadRepository") as repo_cls:
            repo = MagicMock()
            repo.get_by_id = AsyncMock(return_value=mock_lead)
            repo.delete = AsyncMock()
            repo_cls.return_value = repo

            response = await leads_client.delete("/api/v1/leads/lead-123")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_not_found(self, leads_client: AsyncClient):
        """Verify 404 when lead not found."""
        with patch("api.routers.leads.LeadRepository") as repo_cls:
            repo = MagicMock()
            repo.get_by_id = AsyncMock(return_value=None)
            repo_cls.return_value = repo

            response = await leads_client.delete("/api/v1/leads/nonexistent")

        assert response.status_code == 404
