"""
Tests for E-Signature API endpoints.

Task #58: Comprehensive Test Suite Update
"""

from collections.abc import AsyncGenerator
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps.auth import get_current_active_user
from api.routers import esignatures
from db.database import get_db


@pytest.fixture
def mock_user():
    """Create a mock user."""
    user = MagicMock()
    user.id = "test-user-123"
    user.email = "test@example.com"
    user.role = "user"
    return user


@pytest.fixture
def mock_signature_request():
    """Create a mock signature request."""
    req = MagicMock()
    req.id = "sig-req-123"
    req.user_id = "test-user-123"
    req.title = "Employment Contract"
    req.provider = "hellosign"
    req.document_id = "doc-456"
    req.template_id = "template-789"
    req.property_id = "prop-123"
    req.subject = "Please sign this document"
    req.message = "This is your employment contract"
    req.signers = [
        {
            "email": "signer@example.com",
            "name": "John Doe",
            "role": "tenant",
            "order": 1,
            "status": "pending",
            "signed_at": None,
            "signature_url": "https://sign.hellosign.com/abc",
        }
    ]
    req.status = "sent"
    req.provider_envelope_id = "env-abc123"
    req.document_content_hash = "hash123"
    req.sent_at = datetime(2024, 1, 10)
    req.completed_at = None
    req.expires_at = datetime.now() + timedelta(days=7)
    req.reminder_count = 0
    req.created_at = datetime(2024, 1, 1)
    req.updated_at = datetime(2024, 1, 10)
    return req


@pytest.fixture(scope="function")
async def esignatures_client(
    mock_user,
    db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing esignatures endpoints."""
    test_app = FastAPI()
    test_app.include_router(esignatures.router, prefix="/api/v1")

    async def override_get_db():
        yield db_session

    async def override_get_current_user():
        return mock_user

    test_app.dependency_overrides[get_db] = override_get_db
    test_app.dependency_overrides[get_current_active_user] = override_get_current_user

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    test_app.dependency_overrides.clear()


class TestListSignatureRequests:
    """Tests for listing signature requests."""

    @pytest.mark.asyncio
    async def test_list_signature_requests_success(
        self,
        esignatures_client: AsyncClient,
        mock_signature_request: MagicMock,
    ):
        """Verify successful signature request listing."""
        with patch.object(esignatures, "SignatureRequestRepository") as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_by_user = AsyncMock(return_value=[mock_signature_request])
            mock_repo.count_by_user = AsyncMock(return_value=1)
            mock_repo_class.return_value = mock_repo

            response = await esignatures_client.get("/api/v1/signatures")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_list_signature_requests_pagination(
        self,
        esignatures_client: AsyncClient,
    ):
        """Verify pagination works correctly."""
        with patch.object(esignatures, "SignatureRequestRepository") as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_by_user = AsyncMock(return_value=[])
            mock_repo.count_by_user = AsyncMock(return_value=50)
            mock_repo_class.return_value = mock_repo

            response = await esignatures_client.get(
                "/api/v1/signatures",
                params={"page": 2, "page_size": 10},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 10


class TestGetSignatureRequest:
    """Tests for getting signature request details."""

    @pytest.mark.asyncio
    async def test_get_signature_request_success(
        self,
        esignatures_client: AsyncClient,
        mock_signature_request: MagicMock,
    ):
        """Verify successful signature request retrieval."""
        with patch.object(esignatures, "SignatureRequestRepository") as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_by_id = AsyncMock(return_value=mock_signature_request)
            mock_repo_class.return_value = mock_repo

            response = await esignatures_client.get("/api/v1/signatures/sig-req-123")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "sig-req-123"

    @pytest.mark.asyncio
    async def test_get_signature_request_not_found(
        self,
        esignatures_client: AsyncClient,
    ):
        """Verify 404 when signature request not found."""
        with patch.object(esignatures, "SignatureRequestRepository") as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_by_id = AsyncMock(return_value=None)
            mock_repo_class.return_value = mock_repo

            response = await esignatures_client.get("/api/v1/signatures/nonexistent")

        assert response.status_code == 404


class TestCancelSignatureRequest:
    """Tests for canceling signature requests."""

    @pytest.mark.asyncio
    async def test_cancel_signature_request_not_found(
        self,
        esignatures_client: AsyncClient,
    ):
        """Verify 404 when signature request not found."""
        with patch.object(esignatures, "SignatureRequestRepository") as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_by_id = AsyncMock(return_value=None)
            mock_repo_class.return_value = mock_repo

            response = await esignatures_client.post("/api/v1/signatures/nonexistent/cancel")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_cancel_signature_request_invalid_status(
        self,
        esignatures_client: AsyncClient,
        mock_signature_request: MagicMock,
    ):
        """Verify 400 when request cannot be cancelled."""
        mock_signature_request.status = "completed"

        with patch.object(esignatures, "SignatureRequestRepository") as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_by_id = AsyncMock(return_value=mock_signature_request)
            mock_repo_class.return_value = mock_repo

            response = await esignatures_client.post("/api/v1/signatures/sig-req-123/cancel")

        assert response.status_code == 400


class TestSendReminder:
    """Tests for sending signature reminders."""

    @pytest.mark.asyncio
    async def test_send_reminder_max_reached(
        self,
        esignatures_client: AsyncClient,
        mock_signature_request: MagicMock,
    ):
        """Verify 429 when max reminders reached."""
        mock_signature_request.status = "sent"
        mock_signature_request.reminder_count = 3

        with patch.object(esignatures, "SignatureRequestRepository") as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_by_id = AsyncMock(return_value=mock_signature_request)
            mock_repo_class.return_value = mock_repo

            response = await esignatures_client.post("/api/v1/signatures/sig-req-123/reminder")

        assert response.status_code == 429
        assert "Maximum number of reminders" in response.json()["detail"]


class TestDownloadSignedDocument:
    """Tests for downloading signed documents."""

    @pytest.mark.asyncio
    async def test_download_signed_document_not_completed(
        self,
        esignatures_client: AsyncClient,
        mock_signature_request: MagicMock,
    ):
        """Verify 400 when document not yet signed."""
        mock_signature_request.status = "sent"

        with patch.object(esignatures, "SignatureRequestRepository") as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_by_id = AsyncMock(return_value=mock_signature_request)
            mock_repo_class.return_value = mock_repo

            response = await esignatures_client.get("/api/v1/signatures/sig-req-123/download")

        assert response.status_code == 400
        assert "not yet available" in response.json()["detail"]


class TestCreateSignatureRequest:
    """Tests for creating signature requests."""

    @pytest.mark.asyncio
    async def test_create_signature_request_service_unavailable(
        self,
        esignatures_client: AsyncClient,
    ):
        """Verify 503 when e-signature service not configured."""
        request_data = {
            "title": "Test",
            "signers": [
                {
                    "email": "test@test.com",
                    "name": "Test",
                    "role": "tenant",
                    "order": 1,
                }
            ],
        }

        with patch.object(esignatures, "get_esignature_service") as mock_esig_getter:
            mock_esig_getter.return_value = None

            response = await esignatures_client.post(
                "/api/v1/signatures/request",
                json=request_data,
            )

        assert response.status_code == 503
        assert "not configured" in response.json()["detail"]
