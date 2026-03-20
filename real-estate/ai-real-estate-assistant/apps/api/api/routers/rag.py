import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from langchain_core.language_models import BaseChatModel

from api.dependencies import get_knowledge_store, get_rag_qa_llm_details, parse_rag_qa_request
from api.models import RagQaRequest, RagQaResponse, RagResetResponse
from config.settings import get_settings
from utils.document_text_extractor import (
    DocumentTextExtractionError,
    OptionalDependencyMissingError,
    UnsupportedDocumentTypeError,
    extract_text_segments_from_upload,
)
from vector_store.knowledge_store import KnowledgeStore

logger = logging.getLogger(__name__)
router = APIRouter()

_READ_CHUNK_BYTES = 1024 * 1024


async def _read_upload_file_limited(file: UploadFile, max_bytes: int) -> tuple[bytes, bool]:
    buf = bytearray()
    while True:
        chunk = await file.read(_READ_CHUNK_BYTES)
        if not chunk:
            return bytes(buf), False
        if len(buf) + len(chunk) > max_bytes:
            return bytes(buf), True
        buf.extend(chunk)


@router.post("/rag/upload", tags=["RAG"])
async def upload_documents(
    files: list[UploadFile],
    store: Annotated[Optional[KnowledgeStore], Depends(get_knowledge_store)],
):
    """
    Upload documents and index for local RAG (CE-safe).
    PDF/DOCX require optional dependencies; unsupported types return a 422 when nothing is indexed.
    """
    if not store:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Knowledge store is not available",
        )

    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    settings = get_settings()
    max_files = max(1, int(getattr(settings, "rag_max_files", 10)))
    max_file_bytes = max(1, int(getattr(settings, "rag_max_file_bytes", 10 * 1024 * 1024)))
    max_total_bytes = max(1, int(getattr(settings, "rag_max_total_bytes", 25 * 1024 * 1024)))

    if len(files) > max_files:
        raise HTTPException(status_code=400, detail=f"Too many files (max {max_files})")

    total_chunks = 0
    total_bytes = 0
    errors: list[str] = []
    buffered: list[tuple[str, str, bytes]] = []

    for f in files:
        try:
            content_type = (f.content_type or "").lower()
            name = f.filename or "unknown"
            data, too_large = await _read_upload_file_limited(f, max_bytes=max_file_bytes)
            if too_large:
                errors.append(f"{name}: File too large (max {max_file_bytes} bytes)")
                continue

            total_bytes += len(data)
            buffered.append((name, content_type, data))
        except Exception as e:
            logger.warning("Failed to read %s: %s", f.filename, e)
            errors.append(f"{f.filename}: {e}")

    if total_bytes > max_total_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "message": "Upload payload too large",
                "max_total_bytes": max_total_bytes,
                "total_bytes": total_bytes,
                "errors": errors,
            },
        )

    for name, content_type, data in buffered:
        try:
            try:
                segments = extract_text_segments_from_upload(
                    filename=name,
                    content_type=content_type,
                    data=data,
                )
            except (UnsupportedDocumentTypeError, OptionalDependencyMissingError) as e:
                errors.append(str(e))
                continue
            except DocumentTextExtractionError as e:
                errors.append(f"{name}: {e}")
                continue

            filtered_segments = [(s.text, s.metadata) for s in segments if (s.text or "").strip()]
            if not filtered_segments:
                errors.append(f"{name}: No extractable text found")
                continue

            try:
                added = store.ingest_text_segments(segments=filtered_segments, source=name)
                total_chunks += added
            except Exception as e:
                logger.warning("Failed to ingest %s: %s", name, e)
                errors.append(f"{name}: {e}")
        except Exception as e:
            logger.warning("Failed to ingest %s: %s", name, e)
            errors.append(f"{name}: {e}")

    if total_chunks == 0 and errors:
        raise HTTPException(
            status_code=422,
            detail={"message": "No documents were indexed", "errors": errors},
        )

    return {"message": "Upload processed", "chunks_indexed": total_chunks, "errors": errors}


@router.post("/rag/reset", tags=["RAG"], response_model=RagResetResponse)
async def reset_rag_knowledge(
    store: Annotated[Optional[KnowledgeStore], Depends(get_knowledge_store)],
):
    """
    Clear all indexed knowledge documents for local RAG (CE-safe).
    """
    if not store:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Knowledge store is not available",
        )

    removed = store.clear()
    stats = store.get_stats()
    return {
        "message": "Knowledge cleared",
        "documents_removed": removed,
        "documents_remaining": int(stats.get("documents", 0)),
    }


@router.post("/rag/qa", tags=["RAG"], response_model=RagQaResponse)
async def rag_qa(
    rag_request: Annotated[RagQaRequest, Depends(parse_rag_qa_request)],
    store: Annotated[Optional[KnowledgeStore], Depends(get_knowledge_store)],
    llm_details: Annotated[
        tuple[Optional[BaseChatModel], Optional[str], Optional[str]],
        Depends(get_rag_qa_llm_details),
    ],
):
    """
    Simple QA over uploaded knowledge with citations.
    If LLM is unavailable, returns concatenated context as answer.
    """
    if not store:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Knowledge store is not available",
        )

    llm, effective_provider, effective_model = llm_details

    results = store.similarity_search_with_score(rag_request.question, k=rag_request.top_k)
    docs = [d for d, _s in results]
    if not docs:
        return {
            "answer": "",
            "citations": [],
            "llm_used": False,
            "provider": effective_provider,
            "model": effective_model,
        }

    context = "\n\n".join([doc.page_content for doc in docs])
    citations = [
        {
            "source": doc.metadata.get("source"),
            "chunk_index": doc.metadata.get("chunk_index"),
            "page_number": doc.metadata.get("page_number"),
            "paragraph_number": doc.metadata.get("paragraph_number"),
        }
        for doc in docs
    ]

    if llm:
        try:
            prompt = (
                "Answer the question based only on the following context.\n\n"
                f"{context}\n\nQuestion: {rag_request.question}\n\n"
                "If the answer cannot be found in the context, say you don't know."
            )
            msg = llm.invoke(prompt)
            content = getattr(msg, "content", str(msg))
            return {
                "answer": content,
                "citations": citations,
                "llm_used": True,
                "provider": effective_provider,
                "model": effective_model,
            }
        except Exception as e:
            logger.warning("LLM invocation failed: %s", e)

    # Fallback: return context snippet
    snippet = context[:500]
    return {
        "answer": snippet,
        "citations": citations,
        "llm_used": False,
        "provider": effective_provider,
        "model": effective_model,
    }
