import inspect
import json
import logging
import uuid
from typing import Annotated, Any, Optional

import anyio
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from langchain.memory import ConversationBufferMemory
from langchain_core.language_models import BaseChatModel

from agents.hybrid_agent import create_hybrid_agent
from ai.memory import get_session_history
from api.chat_sources import serialize_chat_sources, serialize_web_sources
from api.dependencies import get_llm, get_vector_store
from api.models import ChatRequest, ChatResponse
from config.settings import get_settings
from utils.sanitization import sanitize_chat_message, sanitize_intermediate_steps

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat_endpoint(
    request: ChatRequest,
    req: Request,
    llm: Annotated[BaseChatModel, Depends(get_llm)],
    store: Annotated[Optional[Any], Depends(get_vector_store)],
):
    """
    Process a chat message using the hybrid agent with session persistence.
    """
    # Get request_id from middleware for correlation
    request_id = getattr(req.state, "request_id", None) or str(uuid.uuid4())
    # Sanitize chat message to prevent injection attacks
    try:
        sanitized_message = sanitize_chat_message(request.message)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None

    try:
        if not store:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Vector store unavailable"
            )

        settings = get_settings()
        sources_max_items = max(0, int(settings.chat_sources_max_items))
        sources_max_content_chars = max(0, int(settings.chat_source_content_max_chars))
        sources_max_total_bytes = max(0, int(settings.chat_sources_max_total_bytes))

        # Handle Session ID
        session_id = request.session_id
        if not session_id:
            session_id = str(uuid.uuid4())

        # Initialize Memory with Persistence
        chat_history = get_session_history(session_id)
        memory = ConversationBufferMemory(
            chat_memory=chat_history,
            memory_key="chat_history",
            return_messages=True,
            output_key="answer",
        )

        # Create Agent
        agent_kwargs = {
            "llm": llm,
            "retriever": store.get_retriever(),
            "memory": memory,
            "internet_enabled": bool(getattr(settings, "internet_enabled", False)),
            "searxng_url": getattr(settings, "searxng_url", None),
            "web_search_max_results": int(getattr(settings, "web_search_max_results", 5)),
            "web_fetch_timeout_seconds": float(getattr(settings, "web_fetch_timeout_seconds", 10)),
            "web_fetch_max_bytes": int(getattr(settings, "web_fetch_max_bytes", 300_000)),
            "web_allowlist_domains": list(getattr(settings, "web_allowlist_domains", []) or []),
        }
        sig = inspect.signature(create_hybrid_agent)
        if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
            filtered_kwargs = agent_kwargs
        else:
            filtered_kwargs = {k: v for k, v in agent_kwargs.items() if k in sig.parameters}
        agent = create_hybrid_agent(**filtered_kwargs)

        if request.stream:
            analysis = getattr(getattr(agent, "analyzer", None), "analyze", None)
            analyzed = analysis(sanitized_message) if callable(analysis) else None
            requires_web = False
            if analyzed is not None:
                from agents.query_analyzer import QueryAnalysis

                if not isinstance(analyzed, QueryAnalysis):
                    analyzed = None
            if analyzed is not None:
                requires_web = bool(
                    getattr(analyzed, "requires_external_data", False)
                    or any(
                        getattr(t, "value", str(t)) == "web_search"
                        for t in getattr(analyzed, "tools_needed", []) or []
                    )
                )

            async def event_generator():
                sources_payload: dict[str, object] = {
                    "sources": [],
                    "sources_truncated": False,
                    "session_id": session_id,
                    "request_id": request_id,
                }

                try:
                    # Add timeout protection for streaming (5 minutes)
                    with anyio.fail_after(300):
                        if requires_web:
                            result = agent.process_query(sanitized_message)
                            raw_answer = result.get("answer", "")
                            answer_text = (
                                raw_answer if isinstance(raw_answer, str) else str(raw_answer)
                            )
                            if answer_text:
                                yield f"data: {json.dumps({'content': answer_text}, ensure_ascii=False, default=str)}\n\n"

                            raw_sources = (
                                result.get("sources")
                                if isinstance(result.get("sources"), list)
                                else []
                            )
                            if (
                                raw_sources
                                and isinstance(raw_sources, list)
                                and isinstance(raw_sources[0], dict)
                                and "content" in raw_sources[0]
                                and "metadata" in raw_sources[0]
                            ):
                                sources = raw_sources
                                sources_truncated = False
                            else:
                                sources, sources_truncated = serialize_web_sources(
                                    raw_sources or [],
                                    max_items=sources_max_items,
                                    max_content_chars=sources_max_content_chars,
                                    max_total_bytes=sources_max_total_bytes,
                                )
                            sources_payload["sources"] = sources
                            sources_payload["sources_truncated"] = sources_truncated

                            if request.include_intermediate_steps:
                                raw_steps = result.get("intermediate_steps") or []
                                # Sanitize steps to redact sensitive data (API keys, tokens, passwords)
                                safe_steps = sanitize_intermediate_steps(raw_steps)
                                sources_payload["intermediate_steps"] = safe_steps
                        else:
                            async for chunk in agent.astream_query(sanitized_message):
                                yield f"data: {chunk}\n\n"
                            if hasattr(agent, "get_sources_for_query"):
                                try:
                                    docs = agent.get_sources_for_query(sanitized_message)
                                    sources, sources_truncated = serialize_chat_sources(
                                        docs,
                                        max_items=sources_max_items,
                                        max_content_chars=sources_max_content_chars,
                                        max_total_bytes=sources_max_total_bytes,
                                    )
                                    sources_payload["sources"] = sources
                                    sources_payload["sources_truncated"] = sources_truncated
                                except Exception:
                                    sources_payload["sources"] = []
                                    sources_payload["sources_truncated"] = False

                        yield "event: meta\n"
                        yield f"data: {json.dumps(sources_payload)}\n\n"
                        yield "data: [DONE]\n\n"
                except TimeoutError:
                    # Send timeout error event
                    error_payload = {"error": "Stream timeout exceeded", "request_id": request_id}
                    yield "event: error\n"
                    yield f"data: {json.dumps(error_payload)}\n\n"
                    yield "data: [DONE]\n\n"
                except Exception as e:
                    # Log error and send error event for client recovery
                    logger.error(f"Stream error (request_id={request_id}): {e}")
                    error_payload = {"error": str(e), "request_id": request_id}
                    yield "event: error\n"
                    yield f"data: {json.dumps(error_payload)}\n\n"
                    yield "data: [DONE]\n\n"
                finally:
                    # Always ensure stream terminates
                    pass

            return StreamingResponse(event_generator(), media_type="text/event-stream")

        result = agent.process_query(sanitized_message)

        answer = result.get("answer", "")
        if "sources" in result and isinstance(result.get("sources"), list):
            raw_sources = result.get("sources") or []
            if (
                raw_sources
                and isinstance(raw_sources, list)
                and isinstance(raw_sources[0], dict)
                and "content" in raw_sources[0]
                and "metadata" in raw_sources[0]
            ):
                sources = raw_sources
                sources_truncated = False
            else:
                sources, sources_truncated = serialize_web_sources(
                    raw_sources,
                    max_items=sources_max_items,
                    max_content_chars=sources_max_content_chars,
                    max_total_bytes=sources_max_total_bytes,
                )
        else:
            sources, sources_truncated = serialize_chat_sources(
                result.get("source_documents") or [],
                max_items=sources_max_items,
                max_content_chars=sources_max_content_chars,
                max_total_bytes=sources_max_total_bytes,
            )

        # Sanitize intermediate steps if requested
        intermediate_steps = None
        if request.include_intermediate_steps:
            raw_steps = result.get("intermediate_steps") or []
            intermediate_steps = sanitize_intermediate_steps(raw_steps) if raw_steps else None

        return ChatResponse(
            response=answer,
            sources=sources,
            sources_truncated=sources_truncated,
            session_id=session_id,
            intermediate_steps=intermediate_steps,
        )

    except Exception as e:
        logger.error(f"Chat processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing failed: {str(e)}",
        ) from e
