from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Any, Dict, List


class DocumentTextExtractionError(Exception):
    pass


class UnsupportedDocumentTypeError(DocumentTextExtractionError):
    pass


class OptionalDependencyMissingError(DocumentTextExtractionError):
    def __init__(self, message: str, dependency: str):
        super().__init__(message)
        self.dependency = dependency


@dataclass(frozen=True)
class ExtractedTextSegment:
    text: str
    metadata: Dict[str, Any]


def extract_text_from_upload(*, filename: str, content_type: str, data: bytes) -> str:
    segments = extract_text_segments_from_upload(
        filename=filename,
        content_type=content_type,
        data=data,
    )
    return "\n".join([s.text for s in segments]).strip()


def extract_text_segments_from_upload(
    *, filename: str, content_type: str, data: bytes
) -> List[ExtractedTextSegment]:
    name = (filename or "").lower()
    ctype = (content_type or "").lower()

    if ctype in {"text/plain", "text/markdown"} or name.endswith((".txt", ".md")):
        return [ExtractedTextSegment(text=data.decode("utf-8", errors="ignore"), metadata={})]

    if ctype == "application/pdf" or name.endswith(".pdf"):
        return _extract_pdf_text_segments(data)

    if (
        ctype == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        or name.endswith(".docx")
    ):
        return _extract_docx_text_segments(data)

    raise UnsupportedDocumentTypeError(
        f"Unsupported file type: {filename} ({content_type}). Allowed: .txt, .md, .pdf, .docx"
    )


def _extract_pdf_text_segments(data: bytes) -> List[ExtractedTextSegment]:
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise OptionalDependencyMissingError(
            "PDF parsing requires optional dependency 'pypdf'. Install with: pip install pypdf",
            dependency="pypdf",
        ) from e

    reader = PdfReader(io.BytesIO(data))
    segments: List[ExtractedTextSegment] = []
    for idx, page in enumerate(reader.pages):
        segments.append(
            ExtractedTextSegment(
                text=(page.extract_text() or ""),
                metadata={"page_number": idx + 1},
            )
        )
    return segments


def _extract_docx_text_segments(data: bytes) -> List[ExtractedTextSegment]:
    try:
        from docx import Document
    except ImportError as e:
        raise OptionalDependencyMissingError(
            "DOCX parsing requires optional dependency 'python-docx'. Install with: pip install python-docx",
            dependency="python-docx",
        ) from e

    doc = Document(io.BytesIO(data))
    segments: List[ExtractedTextSegment] = []
    for idx, paragraph in enumerate(doc.paragraphs):
        text = getattr(paragraph, "text", "") or ""
        if not text.strip():
            continue
        segments.append(
            ExtractedTextSegment(
                text=text,
                metadata={"paragraph_number": idx + 1},
            )
        )
    return segments
