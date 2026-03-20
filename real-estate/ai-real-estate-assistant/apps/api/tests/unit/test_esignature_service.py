"""Unit tests for e-signature service.

Task #57: E-Signature Integration
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.esignature_service import HelloSignService


class TestHelloSignService:
    """Tests for HelloSign service."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        settings = MagicMock()
        settings.hellosign_api_key = "test_api_key"
        settings.hellosign_webhook_secret = "test_webhook_secret"
        settings.environment = "development"
        return settings

    @pytest.fixture
    def hellosign_service(self, mock_settings):
        """Create HelloSign service with mock settings."""
        service = HelloSignService(
            api_key=mock_settings.hellosign_api_key,
            test_mode=True,
        )
        # Replace the client with a mock
        service.client = AsyncMock()
        return service

    @pytest.mark.asyncio
    async def test_create_envelope(self, hellosign_service):
        """Test creating an envelope."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "signature_request_id": "test_req_id",
            "title": "Test Document",
        }
        hellosign_service.client.post.return_value = mock_response
        hellosign_service.client.post.raise_for_status = MagicMock()

        # Mock the file open operation
        mock_file = MagicMock()
        mock_file.__enter__ = MagicMock()
        mock_file.read.return_value = b"mock pdf content"
        mock_file.__exit__ = MagicMock()

        with patch("builtins.open", return_value=mock_file):
            result = await hellosign_service.create_envelope(
                document_path=Path("/tmp/test.pdf"),
                signers=[{"email": "signer@example.com", "name": "Test Signer"}],
                title="Test Document",
            )

        assert result["envelope_id"] == "test_req_id"
        assert result["status"] == "sent"
        hellosign_service.client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_download_signed_document(self, hellosign_service):
        """Test downloading signed document."""
        files_response = MagicMock()
        files_response.json.return_value = {
            "files": [{"file_url": "https://example.com/signed_document.pdf"}]
        }

        file_response = MagicMock()
        file_response.content = b"%PDF content%"

        hellosign_service.client.get.side_effect = [files_response, file_response]
        hellosign_service.client.get.raise_for_status = MagicMock()

        result = await hellosign_service.download_signed_document("test_envelope_id")

        assert result == b"%PDF content%"
        hellosign_service.client.get.assert_called()

    @pytest.mark.asyncio
    async def test_cancel_envelope(self, hellosign_service):
        """Test canceling an envelope."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        hellosign_service.client.post.return_value = mock_response
        hellosign_service.client.post.raise_for_status = MagicMock()

        result = await hellosign_service.cancel_envelope("test_envelope_id")

        assert result is True
        hellosign_service.client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_reminder(self, hellosign_service):
        """Test sending a reminder."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        hellosign_service.client.post.return_value = mock_response
        hellosign_service.client.post.raise_for_status = MagicMock()

        result = await hellosign_service.send_reminder("test_envelope_id")

        assert result is True
        hellosign_service.client.post.assert_called_once()
