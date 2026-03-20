import builtins
import sys
import types

import pytest

from utils.document_text_extractor import (
    OptionalDependencyMissingError,
    UnsupportedDocumentTypeError,
    extract_text_from_upload,
    extract_text_segments_from_upload,
)


def test_extract_text_from_upload_decodes_txt_by_extension():
    text = extract_text_from_upload(
        filename="notes.txt",
        content_type="application/octet-stream",
        data="Zażółć gęślą jaźń".encode("utf-8"),
    )
    assert "Zażółć" in text


def test_extract_text_from_upload_decodes_markdown_by_content_type():
    text = extract_text_from_upload(
        filename="notes.bin",
        content_type="text/markdown",
        data=b"# Title\n\nHello",
    )
    assert text.startswith("# Title")


def test_extract_text_from_upload_unsupported_type_raises():
    with pytest.raises(UnsupportedDocumentTypeError):
        extract_text_from_upload(
            filename="img.png",
            content_type="image/png",
            data=b"\x89PNG",
        )


def test_extract_text_from_upload_pdf_missing_dependency_is_reported(monkeypatch):
    real_import = builtins.__import__

    def _fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "pypdf" or name.startswith("pypdf."):
            raise ImportError("no pypdf")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", _fake_import)

    with pytest.raises(OptionalDependencyMissingError) as exc:
        extract_text_from_upload(
            filename="doc.pdf",
            content_type="application/pdf",
            data=b"%PDF-",
        )
    assert exc.value.dependency == "pypdf"


def test_extract_text_from_upload_docx_missing_dependency_is_reported(monkeypatch):
    real_import = builtins.__import__

    def _fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "docx" or name.startswith("docx."):
            raise ImportError("no docx")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", _fake_import)

    with pytest.raises(OptionalDependencyMissingError) as exc:
        extract_text_from_upload(
            filename="doc.docx",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            data=b"PK\x03\x04",
        )
    assert exc.value.dependency == "python-docx"


def test_extract_text_from_upload_pdf_success_with_stub_module(monkeypatch):
    class _Page:
        def __init__(self, text: str):
            self._text = text

        def extract_text(self):
            return self._text

    class _Reader:
        def __init__(self, _stream):
            self.pages = [_Page("Hello PDF"), _Page("Second page")]

    monkeypatch.setitem(sys.modules, "pypdf", types.SimpleNamespace(PdfReader=_Reader))

    text = extract_text_from_upload(
        filename="doc.pdf",
        content_type="application/pdf",
        data=b"%PDF-",
    )
    assert "Hello PDF" in text


def test_extract_text_from_upload_docx_success_with_stub_module(monkeypatch):
    class _Paragraph:
        def __init__(self, text: str):
            self.text = text

    class _Doc:
        def __init__(self, _stream):
            self.paragraphs = [_Paragraph("Hello DOCX"), _Paragraph("")]

    monkeypatch.setitem(sys.modules, "docx", types.SimpleNamespace(Document=_Doc))

    text = extract_text_from_upload(
        filename="doc.docx",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        data=b"PK\x03\x04",
    )
    assert text == "Hello DOCX"


def test_extract_text_segments_from_upload_txt_returns_single_segment():
    segments = extract_text_segments_from_upload(
        filename="notes.txt",
        content_type="application/octet-stream",
        data=b"Hello\nWorld",
    )
    assert len(segments) == 1
    assert segments[0].text.startswith("Hello")
    assert segments[0].metadata == {}


def test_extract_text_segments_from_upload_pdf_includes_page_numbers(monkeypatch):
    class _Page:
        def __init__(self, text: str):
            self._text = text

        def extract_text(self):
            return self._text

    class _Reader:
        def __init__(self, _stream):
            self.pages = [_Page("Page1"), _Page("Page2")]

    monkeypatch.setitem(sys.modules, "pypdf", types.SimpleNamespace(PdfReader=_Reader))

    segments = extract_text_segments_from_upload(
        filename="doc.pdf",
        content_type="application/pdf",
        data=b"%PDF-",
    )
    assert [s.metadata.get("page_number") for s in segments] == [1, 2]
    assert [s.text for s in segments] == ["Page1", "Page2"]


def test_extract_text_segments_from_upload_docx_includes_paragraph_numbers(monkeypatch):
    class _Paragraph:
        def __init__(self, text: str):
            self.text = text

    class _Doc:
        def __init__(self, _stream):
            self.paragraphs = [_Paragraph("A"), _Paragraph(""), _Paragraph("B")]

    monkeypatch.setitem(sys.modules, "docx", types.SimpleNamespace(Document=_Doc))

    segments = extract_text_segments_from_upload(
        filename="doc.docx",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        data=b"PK\x03\x04",
    )
    assert [s.metadata.get("paragraph_number") for s in segments] == [1, 3]
    assert [s.text for s in segments] == ["A", "B"]
