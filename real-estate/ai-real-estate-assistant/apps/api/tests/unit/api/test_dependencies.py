from types import SimpleNamespace
from typing import Any

import pytest

import api.dependencies as dep_mod
from api.dependencies import get_agent, get_llm, get_vector_store
from models.provider_factory import ModelProviderFactory


class _StubDocRetriever:
    def get_relevant_documents(self, query: str) -> list[Any]:
        return []


class _StubStore:
    def get_retriever(self):
        return _StubDocRetriever()


@pytest.fixture(autouse=True)
def _clear_factory_cache():
    ModelProviderFactory.clear_cache()
    yield
    ModelProviderFactory.clear_cache()


def test_get_vector_store_returns_none_on_exception(monkeypatch):
    class _Boom:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("boom")

    get_vector_store.cache_clear()
    monkeypatch.setattr(dep_mod, "ChromaPropertyStore", _Boom)
    store = get_vector_store()
    assert store is None


def test_get_vector_store_caches_success(monkeypatch):
    class _OK:
        def __init__(self, *args, **kwargs):
            self.created = True

    get_vector_store.cache_clear()
    monkeypatch.setattr(dep_mod, "ChromaPropertyStore", _OK)
    s1 = get_vector_store()
    s2 = get_vector_store()
    assert s1 is s2


def test_get_llm_chooses_first_model_when_default_missing(monkeypatch):
    dep_mod.settings.default_provider = "openai"
    dep_mod.settings.default_model = None

    class _ModelInfo(SimpleNamespace):
        pass

    class _Provider:
        def list_models(self):
            return [_ModelInfo(id="m1")]

        def create_model(self, model_id, temperature, max_tokens, **kwargs):
            return SimpleNamespace(id=model_id, kwargs=kwargs, t=temperature, max_tokens=max_tokens)

    import models.provider_factory as pf_mod

    monkeypatch.setattr(pf_mod.ModelProviderFactory, "get_provider", lambda name: _Provider())
    llm = get_llm()
    assert getattr(llm, "id", "") == "m1"
    assert "provider_name" not in getattr(llm, "kwargs", {})


def test_get_llm_raises_when_no_models(monkeypatch):
    dep_mod.settings.default_provider = "openai"
    dep_mod.settings.default_model = None

    class _Provider:
        def list_models(self):
            return []

        def create_model(self, *args, **kwargs):
            return SimpleNamespace()

    import models.provider_factory as pf_mod

    monkeypatch.setattr(pf_mod.ModelProviderFactory, "get_provider", lambda name: _Provider())
    with pytest.raises(RuntimeError):
        get_llm()


def test_get_agent_requires_store(monkeypatch):
    with pytest.raises(RuntimeError):
        # Pass None store via manual call (dependency layer tested directly)
        get_agent(None, SimpleNamespace())


def test_get_agent_success(monkeypatch):
    def _mk_agent(**kwargs):
        return SimpleNamespace(agent=True, **kwargs)

    monkeypatch.setattr(dep_mod, "create_hybrid_agent", _mk_agent)
    agent = get_agent(_StubStore(), SimpleNamespace())
    assert getattr(agent, "agent", False)


def test_get_valuation_provider_is_gated_by_mode():
    old_mode = dep_mod.settings.valuation_mode
    try:
        dep_mod.settings.valuation_mode = "simple"
        p = dep_mod.get_valuation_provider()
        assert p is not None
        assert p.estimate_value({"area": 2, "price_per_sqm": 3}) == 6.0

        dep_mod.settings.valuation_mode = "pro"
        assert dep_mod.get_valuation_provider() is None
    finally:
        dep_mod.settings.valuation_mode = old_mode


def test_get_legal_check_service_is_gated_by_mode():
    old_mode = dep_mod.settings.legal_check_mode
    try:
        dep_mod.settings.legal_check_mode = "basic"
        svc = dep_mod.get_legal_check_service()
        assert svc is not None
        assert svc.analyze_contract("x") == {"risks": [], "score": 0.0}

        dep_mod.settings.legal_check_mode = "pro"
        assert dep_mod.get_legal_check_service() is None
    finally:
        dep_mod.settings.legal_check_mode = old_mode


def test_get_data_enrichment_service_is_gated_by_flag():
    old_flag = dep_mod.settings.data_enrichment_enabled
    try:
        dep_mod.settings.data_enrichment_enabled = False
        assert dep_mod.get_data_enrichment_service() is None

        dep_mod.settings.data_enrichment_enabled = True
        svc = dep_mod.get_data_enrichment_service()
        assert svc is not None
        assert svc.enrich("Any") == {}
    finally:
        dep_mod.settings.data_enrichment_enabled = old_flag


def test_get_crm_connector_requires_webhook_url():
    old_url = dep_mod.settings.crm_webhook_url
    try:
        dep_mod.settings.crm_webhook_url = None
        assert dep_mod.get_crm_connector() is None

        dep_mod.settings.crm_webhook_url = "http://example.invalid"
        connector = dep_mod.get_crm_connector()
        assert connector is not None
        assert getattr(connector, "webhook_url", None) == "http://example.invalid"
    finally:
        dep_mod.settings.crm_webhook_url = old_url


def test_get_knowledge_store_returns_none_on_exception(monkeypatch):
    class _Boom:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("boom")

    dep_mod.get_knowledge_store.cache_clear()
    monkeypatch.setattr(dep_mod, "KnowledgeStore", _Boom)
    store = dep_mod.get_knowledge_store()
    assert store is None


def test_get_knowledge_store_caches_success(monkeypatch):
    class _OK:
        def __init__(self, *args, **kwargs):
            self.created = True

    dep_mod.get_knowledge_store.cache_clear()
    monkeypatch.setattr(dep_mod, "KnowledgeStore", _OK)
    s1 = dep_mod.get_knowledge_store()
    s2 = dep_mod.get_knowledge_store()
    assert s1 is s2
