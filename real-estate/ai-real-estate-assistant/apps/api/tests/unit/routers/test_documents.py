"""
Tests for Document Management API endpoints.

Task #58: Comprehensive Test Suite Update
"""

from collections.abc import AsyncGenerator
from datetime import datetime, timedelta
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps.auth import get_current_active_user
from api.routers import documents
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
def mock_document():
    """Create a mock document."""
    doc = MagicMock()
    doc.id = "doc-123"
    doc.user_id = "test-user-123"
    doc.property_id = "prop-456"
    doc.filename = "unique-filename.pdf"
    doc.original_filename = "contract.pdf"
    doc.file_type = "application/pdf"
    doc.file_size = 102400
    doc.category = "contract"
    doc.tags = '["important", "signed"]'
    doc.description = "Sales contract"
    doc.expiry_date = datetime.now() + timedelta(days=30)
    doc.ocr_status = "completed"
    doc.created_at = datetime(2024, 1, 1)
    doc.updated_at = datetime(2024, 1, 15)
    doc.storage_path = "/storage/documents/test-user-123/unique-filename.pdf"
    return doc


@pytest.fixture(scope="function")
async def documents_client(
    mock_user,
    db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing documents endpoints."""
    test_app = FastAPI()
    test_app.include_router(documents.router, prefix="/api/v1")

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


class TestUploadDocument:
    """Tests for document upload endpoint."""

    @pytest.mark.asyncio
    async def test_upload_document_invalid_type(
        self,
        documents_client: AsyncClient,
    ):
        """Verify error for invalid file type."""
        files = {"file": ("script.exe", BytesIO(b"MZ content"), "application/octet-stream")}

        response = await documents_client.post("/api/v1/documents", files=files)

        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_upload_document_missing_file(
        self,
        documents_client: AsyncClient,
    ):
        """Verify error when no file provided."""
        response = await documents_client.post("/api/v1/documents")

        assert response.status_code == 422


class TestListDocuments:
    """Tests for listing documents."""

    @pytest.mark.asyncio
    async def test_list_documents_success(
        self,
        documents_client: AsyncClient,
        mock_document: MagicMock,
    ):
        """Verify successful document listing."""
        with patch.object(documents, "DocumentRepository") as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_by_user = AsyncMock(return_value=[mock_document])
            mock_repo.count_by_user = AsyncMock(return_value=1)
            mock_repo_class.return_value = mock_repo

            response = await documents_client.get("/api/v1/documents")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_list_documents_with_filters(
        self,
        documents_client: AsyncClient,
        mock_document: MagicMock,
    ):
        """Verify document listing with filters."""
        with patch.object(documents, "DocumentRepository") as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_by_user = AsyncMock(return_value=[mock_document])
            mock_repo.count_by_user = AsyncMock(return_value=1)
            mock_repo_class.return_value = mock_repo

            response = await documents_client.get(
                "/api/v1/documents",
                params={
                    "category": "contract",
                    "ocr_status": "completed",
                },
            )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_documents_pagination(
        self,
        documents_client: AsyncClient,
    ):
        """Verify document listing pagination."""
        with patch.object(documents, "DocumentRepository") as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_by_user = AsyncMock(return_value=[])
            mock_repo.count_by_user = AsyncMock(return_value=100)
            mock_repo_class.return_value = mock_repo

            response = await documents_client.get(
                "/api/v1/documents",
                params={"page": 2, "page_size": 10},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 10


class TestExpiringDocuments:
    """Tests for expiring documents endpoint."""

    @pytest.mark.asyncio
    async def test_get_expiring_documents_success(
        self,
        documents_client: AsyncClient,
        mock_document: MagicMock,
    ):
        """Verify successful expiring documents retrieval."""
        with patch.object(documents, "DocumentRepository") as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_expiring_soon = AsyncMock(return_value=[mock_document])
            mock_repo_class.return_value = mock_repo

            response = await documents_client.get(
                "/api/v1/documents/expiring",
                params={"days_ahead": 30},
            )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["days_ahead"] == 30

    @pytest.mark.asyncio
    async def test_get_expiring_documents_default_days(
        self,
        documents_client: AsyncClient,
    ):
        """Verify default days parameter (30)."""
        with patch.object(documents, "DocumentRepository") as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_expiring_soon = AsyncMock(return_value=[])
            mock_repo_class.return_value = mock_repo

            response = await documents_client.get("/api/v1/documents/expiring")

        assert response.status_code == 200


class TestDownloadDocument:
    """Tests for document download endpoint."""

    @pytest.mark.asyncio
    async def test_download_document_not_found(
        self,
        documents_client: AsyncClient,
    ):
        """Verify 404 when document not found."""
        with patch.object(documents, "DocumentRepository") as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_by_id = AsyncMock(return_value=None)
            mock_repo_class.return_value = mock_repo

            response = await documents_client.get("/api/v1/documents/nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestDeleteDocument:
    """Tests for document deletion endpoint."""

    @pytest.mark.asyncio
    async def test_delete_document_not_found(
        self,
        documents_client: AsyncClient,
    ):
        """Verify 404 when document not found."""
        with patch.object(documents, "DocumentRepository") as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_by_id = AsyncMock(return_value=None)
            mock_repo_class.return_value = mock_repo

            response = await documents_client.delete("/api/v1/documents/nonexistent")

        assert response.status_code == 404


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_parse_tags_json_array(self):
        """Verify parsing JSON array tags."""
        from api.routers.documents import _parse_tags

        result = _parse_tags('["tag1", "tag2"]')
        assert result == ["tag1", "tag2"]

    def test_parse_tags_comma_separated(self):
        """Verify parsing comma-separated tags."""
        from api.routers.documents import _parse_tags

        result = _parse_tags("tag1, tag2, tag3")
        assert result == ["tag1", "tag2", "tag3"]

    def test_parse_tags_empty(self):
        """Verify parsing empty tags."""
        from api.routers.documents import _parse_tags

        result = _parse_tags("")
        assert result is None

        result = _parse_tags(None)
        assert result is None
