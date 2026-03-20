import logging
from functools import lru_cache
from typing import Annotated, Any, Optional

from fastapi import Body, Depends, Header, HTTPException, Query, status
from langchain_core.language_models import BaseChatModel

import models.user_model_preferences as user_model_preferences
from agents.hybrid_agent import create_hybrid_agent
from agents.services.crm_connector import CRMConnector, WebhookCRMConnector
from agents.services.data_enrichment import BasicDataEnrichmentService, DataEnrichmentService
from agents.services.legal_check import BasicLegalCheckService, LegalCheckService
from agents.services.valuation import SimpleValuationProvider, ValuationProvider
from api.models import RagQaRequest
from config.settings import settings
from models.provider_factory import ModelProviderFactory

logger = logging.getLogger(__name__)

try:
    from vector_store.chroma_store import ChromaPropertyStore  # type: ignore
except Exception:
    ChromaPropertyStore = None  # type: ignore

try:
    from vector_store.knowledge_store import KnowledgeStore  # type: ignore
except Exception:
    KnowledgeStore = None  # type: ignore


@lru_cache()
def get_vector_store() -> Optional["ChromaPropertyStore"]:
    """
    Get cached vector store instance for API.
    Returns None if embeddings are not available.
    """
    if ChromaPropertyStore is None:
        return None
    try:
        store = ChromaPropertyStore(
            persist_directory=str(settings.chroma_dir),
            collection_name="properties",
            embedding_model=settings.embedding_model,
        )
        return store
    except Exception:
        return None


def _create_llm(provider_name: str, model_id: Optional[str]) -> BaseChatModel:
    llm, _resolved_model_id = _create_llm_with_resolved_model_id(
        provider_name=provider_name, model_id=model_id
    )
    return llm


def _create_llm_with_resolved_model_id(
    provider_name: str, model_id: Optional[str]
) -> tuple[BaseChatModel, str]:
    factory_provider = ModelProviderFactory.get_provider(provider_name)
    resolved_model_id = model_id

    if not resolved_model_id:
        if provider_name == "ollama" and getattr(settings, "ollama_default_model", None):
            resolved_model_id = settings.ollama_default_model
        else:
            models = factory_provider.list_models()
            if not models:
                raise RuntimeError(f"No models available for provider '{provider_name}'")
            resolved_model_id = models[0].id

    llm = factory_provider.create_model(
        model_id=resolved_model_id,
        temperature=settings.default_temperature,
        max_tokens=settings.default_max_tokens,
    )
    return llm, resolved_model_id


def get_llm(
    x_user_email: Annotated[str | None, Header(alias="X-User-Email")] = None,
) -> BaseChatModel:
    """
    Get Language Model instance.
    Uses settings to determine provider and model.
    """
    default_provider_name = settings.default_provider
    default_model_id = settings.default_model

    preferred_provider: Optional[str] = None
    preferred_model: Optional[str] = None
    if x_user_email and x_user_email.strip():
        try:
            prefs = user_model_preferences.MODEL_PREFS_MANAGER.get_preferences(x_user_email.strip())
            preferred_provider = prefs.preferred_provider
            preferred_model = prefs.preferred_model
        except Exception as e:
            logger.warning("Failed to load model preferences: %s", e)

    primary_provider = preferred_provider or default_provider_name
    primary_model = preferred_model if preferred_provider else (preferred_model or default_model_id)

    try:
        return _create_llm(primary_provider, primary_model)
    except Exception as e:
        if preferred_provider or preferred_model:
            try:
                return _create_llm(default_provider_name, default_model_id)
            except Exception:
                pass
        if primary_provider != "ollama":
            try:
                ollama_provider = ModelProviderFactory.get_provider("ollama")
                runtime_ok, _runtime_error = ollama_provider.validate_connection()
                if runtime_ok:
                    return _create_llm("ollama", settings.ollama_default_model)
            except Exception:
                pass
        raise RuntimeError(
            f"Could not initialize LLM with provider '{primary_provider}': {e}"
        ) from e


def get_optional_llm(
    x_user_email: Annotated[str | None, Header(alias="X-User-Email")] = None,
) -> Optional[BaseChatModel]:
    try:
        return get_llm(x_user_email=x_user_email)
    except Exception as e:
        logger.warning("LLM unavailable: %s", e)
        return None


def get_optional_llm_with_details(
    *,
    x_user_email: str | None,
    provider_override: str | None,
    model_override: str | None,
) -> tuple[Optional[BaseChatModel], Optional[str], Optional[str]]:
    default_provider_name = settings.default_provider
    default_model_id = settings.default_model

    preferred_provider: Optional[str] = None
    preferred_model: Optional[str] = None
    if x_user_email and x_user_email.strip():
        try:
            prefs = user_model_preferences.MODEL_PREFS_MANAGER.get_preferences(x_user_email.strip())
            preferred_provider = prefs.preferred_provider
            preferred_model = prefs.preferred_model
        except Exception as e:
            logger.warning("Failed to load model preferences: %s", e)

    has_overrides = bool(
        (provider_override and provider_override.strip())
        or (model_override and model_override.strip())
    )

    if provider_override and provider_override.strip():
        primary_provider = provider_override.strip()
        primary_model = (
            model_override.strip() if model_override and model_override.strip() else None
        )
    elif model_override and model_override.strip():
        primary_provider = preferred_provider or default_provider_name
        primary_model = model_override.strip()
    else:
        primary_provider = preferred_provider or default_provider_name
        primary_model = (
            preferred_model if preferred_provider else (preferred_model or default_model_id)
        )

    try:
        llm, resolved_model_id = _create_llm_with_resolved_model_id(primary_provider, primary_model)
        return llm, primary_provider, resolved_model_id
    except Exception as e:
        if has_overrides:
            logger.warning(
                "LLM unavailable for explicit selection (provider=%s, model=%s): %s",
                primary_provider,
                primary_model,
                e,
            )
            return None, primary_provider, primary_model

        if preferred_provider or preferred_model:
            try:
                llm, resolved_model_id = _create_llm_with_resolved_model_id(
                    default_provider_name,
                    default_model_id,
                )
                return llm, default_provider_name, resolved_model_id
            except Exception:
                pass
        if primary_provider != "ollama":
            try:
                ollama_provider = ModelProviderFactory.get_provider("ollama")
                runtime_ok, _runtime_error = ollama_provider.validate_connection()
                if runtime_ok:
                    llm, resolved_model_id = _create_llm_with_resolved_model_id(
                        "ollama",
                        settings.ollama_default_model,
                    )
                    return llm, "ollama", resolved_model_id
            except Exception:
                pass

        logger.warning("LLM unavailable: %s", e)
        return None, primary_provider, primary_model


def parse_rag_qa_request(
    payload: Annotated[Optional[RagQaRequest], Body()] = None,
    question: Annotated[Optional[str], Query()] = None,
    top_k: Annotated[int, Query(ge=1, le=50)] = 5,
    provider: Annotated[Optional[str], Query()] = None,
    model: Annotated[Optional[str], Query()] = None,
) -> RagQaRequest:
    if payload is not None:
        return payload

    if question is None or not question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Question must not be empty"
        )

    return RagQaRequest(
        question=question,
        top_k=top_k,
        provider=provider,
        model=model,
    )


def get_rag_qa_llm_details(
    rag_request: Annotated[RagQaRequest, Depends(parse_rag_qa_request)],
    x_user_email: Annotated[str | None, Header(alias="X-User-Email")] = None,
) -> tuple[Optional[BaseChatModel], Optional[str], Optional[str]]:
    return get_optional_llm_with_details(
        x_user_email=x_user_email,
        provider_override=rag_request.provider,
        model_override=rag_request.model,
    )


def get_valuation_provider() -> Optional[ValuationProvider]:
    if settings.valuation_mode != "simple":
        return None
    return SimpleValuationProvider()


def get_crm_connector() -> Optional[CRMConnector]:
    url = settings.crm_webhook_url
    if not url:
        return None
    return WebhookCRMConnector(url)


@lru_cache()
def get_knowledge_store() -> Optional["KnowledgeStore"]:
    """
    Get cached knowledge store instance for RAG uploads (CE-safe).
    Returns None if embeddings are not available.
    """
    if KnowledgeStore is None:
        return None
    try:
        store = KnowledgeStore(
            persist_directory=str(settings.chroma_dir),
            collection_name="knowledge",
        )
        return store
    except Exception:
        return None


def get_data_enrichment_service() -> Optional[DataEnrichmentService]:
    if not settings.data_enrichment_enabled:
        return None
    return BasicDataEnrichmentService()


def get_legal_check_service() -> Optional[LegalCheckService]:
    if settings.legal_check_mode != "basic":
        return None
    return BasicLegalCheckService()


# =============================================================================
# E-Signature Dependencies
# =============================================================================

_esignature_service: Optional[Any] = None
_template_service: Optional[Any] = None


def get_esignature_service() -> Optional[Any]:
    """
    Get e-signature service instance.

    Returns None if not configured.
    """
    from services.esignature_service import get_esignature_service as _get_esignature_service_impl

    return _get_esignature_service_impl()


def get_template_service() -> Optional[Any]:
    """
    Get template service instance.

    Returns None if not configured.
    """
    from services.template_service import get_template_service as _get_template_service_impl

    return _get_template_service_impl()


def get_agent(
    store: Annotated[Optional["ChromaPropertyStore"], Depends(get_vector_store)],
    llm: Annotated[BaseChatModel, Depends(get_llm)],
) -> Any:
    """
    Get initialized Hybrid Agent.
    """
    if not store:
        # If store is missing, we might want a simple agent or raise error
        # For now, let's assume we need the store for the full hybrid agent
        # But we can try to create it with a dummy retriever or fail
        # HybridPropertyAgent needs a retriever.
        raise RuntimeError("Vector Store unavailable, cannot create Hybrid Agent")

    retriever = store.get_retriever()
    return create_hybrid_agent(llm=llm, retriever=retriever)
