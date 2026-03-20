"""
Tests for Document Storage Service.

Task #58: Comprehensive Test Suite Update
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import UploadFile

from services.document_storage import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE_BYTES,
    MIME_TYPE_MAP,
    DocumentStorageError,
    DocumentStorageService,
)


class TestDocumentStorageConstants:
    """Tests for module constants."""

    def test_allowed_extensions(self):
        """Verify allowed extensions include common types."""
        assert ".pdf" in ALLOWED_EXTENSIONS
        assert ".doc" in ALLOWED_EXTENSIONS
        assert ".docx" in ALLOWED_EXTENSIONS
        assert ".jpg" in ALLOWED_EXTENSIONS
        assert ".jpeg" in ALLOWED_EXTENSIONS
        assert ".png" in ALLOWED_EXTENSIONS

    def test_max_file_size(self):
        """Verify max file size is 10MB."""
        assert MAX_FILE_SIZE_BYTES == 10 * 1024 * 1024

    def test_mime_type_map(self):
        """Verify MIME type mappings."""
        assert MIME_TYPE_MAP[".pdf"] == "application/pdf"
        assert MIME_TYPE_MAP[".doc"] == "application/msword"
        assert MIME_TYPE_MAP[".png"] == "image/png"


class TestDocumentStorageService:
    """Tests for DocumentStorageService."""

    @pytest.fixture
    def storage_service(self, tmp_path):
        """Create DocumentStorageService with temp directory."""
        return DocumentStorageService(storage_path=str(tmp_path / "documents"))

    @pytest.fixture
    def mock_upload_file(self):
        """Create a mock UploadFile with chunked read simulation."""
        file = MagicMock(spec=UploadFile)
        file.filename = "test_document.pdf"
        file.content_type = "application/pdf"
        # Simulate chunked reading: return content once, then empty
        file.read = AsyncMock(side_effect=[b"%PDF-1.4 test content", b"", b"", b""])
        return file

    @pytest.fixture
    def mock_image_file(self):
        """Create a mock image UploadFile with chunked read simulation."""
        file = MagicMock(spec=UploadFile)
        file.filename = "test_image.jpg"
        file.content_type = "image/jpeg"
        # Simulate chunked reading: return content once, then empty
        file.read = AsyncMock(side_effect=[b"\xff\xd8\xff\xe0 test image", b"", b"", b""])
        return file

    def test_service_initialization(self, storage_service, tmp_path):
        """Verify service initializes correctly."""
        expected_path = tmp_path / "documents"
        assert storage_service.storage_path == expected_path
        assert storage_service.storage_path.exists()

    def test_service_initialization_default_path(self):
        """Verify service uses default path when not specified."""
        with patch(
            "services.document_storage.settings",
            MagicMock(DOCUMENT_STORAGE_PATH="uploads/documents"),
        ):
            service = DocumentStorageService()
            assert service.storage_path == Path("uploads/documents")

    def test_get_user_dir(self, storage_service):
        """Verify user directory creation."""
        user_dir = storage_service._get_user_dir("user-123")

        assert user_dir.exists()
        assert user_dir.name == "user-123"
        assert user_dir.parent == storage_service.storage_path

    def test_generate_filename(self, storage_service):
        """Verify unique filename generation."""
        filename1 = storage_service._generate_filename("document.pdf")
        filename2 = storage_service._generate_filename("document.pdf")

        assert filename1 != filename2
        assert filename1.endswith(".pdf")
        assert filename2.endswith(".pdf")
        assert len(filename1) < 100  # Should be reasonably short

    def test_generate_filename_sanitizes_special_chars(self, storage_service):
        """Verify special characters are sanitized."""
        filename = storage_service._generate_filename("My Document @#$%^& 2024!.pdf")

        assert "@" not in filename
        assert "#" not in filename
        assert "$" not in filename
        assert filename.endswith(".pdf")

    def test_generate_filename_truncates_long_name(self, storage_service):
        """Verify long filenames are truncated."""
        long_name = "a" * 200 + ".pdf"
        filename = storage_service._generate_filename(long_name)

        assert len(filename) < 100

    def test_validate_file_valid(self, storage_service, mock_upload_file):
        """Verify valid file passes validation."""
        is_valid, error = storage_service.validate_file(mock_upload_file)

        assert is_valid is True
        assert error is None

    def test_validate_file_no_filename(self, storage_service):
        """Verify file without filename fails validation."""
        file = MagicMock(spec=UploadFile)
        file.filename = None
        file.content_type = "application/pdf"

        is_valid, error = storage_service.validate_file(file)

        assert is_valid is False
        assert "No filename" in error

    def test_validate_file_invalid_extension(self, storage_service):
        """Verify invalid extension fails validation."""
        file = MagicMock(spec=UploadFile)
        file.filename = "malware.exe"
        file.content_type = "application/octet-stream"

        is_valid, error = storage_service.validate_file(file)

        assert is_valid is False
        assert "Invalid file type" in error

    def test_validate_file_content_type_mismatch(self, storage_service):
        """Verify content type mismatch logs warning but passes."""
        file = MagicMock(spec=UploadFile)
        file.filename = "document.pdf"
        file.content_type = "image/jpeg"  # Mismatch with extension

        with patch("services.document_storage.logger") as mock_logger:
            is_valid, error = storage_service.validate_file(file)

        # Should pass but log warning
        assert is_valid is True
        assert error is None
        mock_logger.warning.assert_called_once()

    def test_get_file_type_known(self, storage_service):
        """Verify getting MIME type for known extensions."""
        assert storage_service.get_file_type("doc.pdf") == "application/pdf"
        assert storage_service.get_file_type("image.jpg") == "image/jpeg"
        assert storage_service.get_file_type("image.png") == "image/png"

    def test_get_file_type_unknown(self, storage_service):
        """Verify getting MIME type for unknown extensions."""
        assert storage_service.get_file_type("file.xyz") == "application/octet-stream"

    @pytest.mark.asyncio
    async def test_save_file_success(self, storage_service, mock_upload_file):
        """Verify successful file save."""
        path, filename, size = await storage_service.save_file(
            user_id="user-123",
            file=mock_upload_file,
        )

        assert Path(path).exists()
        assert filename.endswith(".pdf")
        assert size > 0
        assert "user-123" in path

    @pytest.mark.asyncio
    async def test_save_file_creates_user_dir(self, storage_service, mock_upload_file):
        """Verify user directory is created."""
        await storage_service.save_file(
            user_id="new-user-456",
            file=mock_upload_file,
        )

        user_dir = storage_service.storage_path / "new-user-456"
        assert user_dir.exists()

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="Windows file locking prevents cleanup during write",
    )
    async def test_save_file_too_large(self, storage_service):
        """Verify file too large raises error."""
        # Create a fresh mock with large content
        large_file = MagicMock(spec=UploadFile)
        large_file.filename = "large.pdf"
        large_file.content_type = "application/pdf"
        # Return large content then empty
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        large_file.read = AsyncMock(side_effect=[large_content, b"", b""])

        with pytest.raises(DocumentStorageError, match="File too large"):
            await storage_service.save_file(
                user_id="user-123",
                file=large_file,
                max_size_bytes=10 * 1024 * 1024,
            )

    @pytest.mark.asyncio
    async def test_save_file_image(self, storage_service, mock_image_file):
        """Verify image file is saved correctly."""
        path, filename, size = await storage_service.save_file(
            user_id="user-123",
            file=mock_image_file,
        )

        assert Path(path).exists()
        assert filename.endswith(".jpg")

    @pytest.mark.asyncio
    async def test_read_file_success(self, storage_service):
        """Verify reading existing file."""
        # First save a file
        test_content = b"test file content"
        test_path = storage_service.storage_path / "user-123" / "test.txt"
        test_path.parent.mkdir(parents=True, exist_ok=True)
        test_path.write_bytes(test_content)

        content = await storage_service.read_file(str(test_path))

        assert content == test_content

    @pytest.mark.asyncio
    async def test_read_file_not_found(self, storage_service):
        """Verify reading non-existent file raises error."""
        with pytest.raises(DocumentStorageError, match="File not found"):
            await storage_service.read_file(str(storage_service.storage_path / "nonexistent.txt"))

    @pytest.mark.asyncio
    async def test_delete_file_success(self, storage_service):
        """Verify deleting existing file."""
        # First save a file
        test_path = storage_service.storage_path / "user-123" / "test.txt"
        test_path.parent.mkdir(parents=True, exist_ok=True)
        test_path.write_bytes(b"test content")

        # delete_file returns None on success
        await storage_service.delete_file(str(test_path))

        assert not test_path.exists()

    @pytest.mark.asyncio
    async def test_delete_file_not_found(self, storage_service):
        """Verify deleting non-existent file does not raise."""
        # delete_file doesn't raise for non-existent files, just logs warning
        await storage_service.delete_file(str(storage_service.storage_path / "nonexistent.txt"))
        # No exception means success

    @pytest.mark.asyncio
    async def test_delete_user_files(self, storage_service):
        """Verify deleting all user files."""
        # Create some test files
        user_dir = storage_service._get_user_dir("user-123")
        (user_dir / "file1.pdf").write_bytes(b"content1")
        (user_dir / "file2.jpg").write_bytes(b"content2")
        (user_dir / "file3.png").write_bytes(b"content3")

        count = await storage_service.delete_user_files("user-123")

        assert count == 3
        assert not user_dir.exists()

    @pytest.mark.asyncio
    async def test_delete_user_files_no_directory(self, storage_service):
        """Verify deleting files for user with no directory."""
        count = await storage_service.delete_user_files("new-user")

        assert count == 0

    def test_get_storage_stats(self, storage_service):
        """Verify getting storage statistics."""
        # Create some test files
        user_dir = storage_service._get_user_dir("user-123")
        (user_dir / "file1.pdf").write_bytes(b"content1")
        (user_dir / "file2.jpg").write_bytes(b"content22")

        stats = storage_service.get_storage_stats("user-123")

        assert stats["file_count"] == 2
        assert stats["total_size_bytes"] == 17  # 9 + 8
        assert "total_size_mb" in stats

    def test_get_storage_stats_empty(self, storage_service):
        """Verify stats for user with no files."""
        stats = storage_service.get_storage_stats("new-user")

        assert stats["file_count"] == 0
        assert stats["total_size_bytes"] == 0


class TestDocumentStorageError:
    """Tests for DocumentStorageError."""

    def test_error_message(self):
        """Verify error message is preserved."""
        error = DocumentStorageError("Test error message")
        assert str(error) == "Test error message"

    def test_error_inheritance(self):
        """Verify error inherits from Exception."""
        error = DocumentStorageError("Test")
        assert isinstance(error, Exception)
