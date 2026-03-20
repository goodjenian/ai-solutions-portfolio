from unittest.mock import Mock

import ai.app_services as app_services


def test_build_forced_filters_none():
    assert app_services.build_forced_filters(None) is None
    assert app_services.build_forced_filters("Anything") is None


def test_build_forced_filters_rent_sale():
    assert app_services.build_forced_filters("Rent") == {"listing_type": "rent"}
    assert app_services.build_forced_filters("Sale") == {"listing_type": "sale"}


def test_create_llm_passes_callbacks_as_list(monkeypatch):
    captured = {}

    def fake_create_model(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(
        app_services.ModelProviderFactory, "create_model", staticmethod(fake_create_model)
    )

    cb1 = Mock()
    cb2 = Mock()
    llm = app_services.create_llm(
        provider_name="openai",
        model_id="gpt-4o-mini",
        temperature=0.1,
        max_tokens=123,
        streaming=True,
        callbacks=(cb1, cb2),
    )

    assert llm is not None
    assert captured["provider_name"] == "openai"
    assert captured["model_id"] == "gpt-4o-mini"
    assert captured["temperature"] == 0.1
    assert captured["max_tokens"] == 123
    assert captured["streaming"] is True
    assert captured["callbacks"] == [cb1, cb2]


def test_create_property_retriever_passes_forced_filters(monkeypatch):
    captured = {}

    def fake_create_retriever(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(app_services, "create_retriever", fake_create_retriever)

    retriever = app_services.create_property_retriever(
        vector_store=object(),
        k_results=7,
        center_lat=None,
        center_lon=None,
        radius_km=None,
        listing_type_filter="Rent",
        min_price=1000.0,
        max_price=2000.0,
        sort_by="price",
        sort_ascending=False,
    )

    assert retriever is not None
    assert captured["k"] == 7
    assert captured["search_type"] == "mmr"
    assert captured["forced_filters"] == {"listing_type": "rent"}
    assert captured["min_price"] == 1000.0
    assert captured["max_price"] == 2000.0
    assert captured["sort_by"] == "price"
    assert captured["sort_ascending"] is False


def test_create_conversation_chain_builds_memory(monkeypatch):
    captured = {}

    def fake_from_llm(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(
        app_services.ConversationalRetrievalChain, "from_llm", staticmethod(fake_from_llm)
    )

    chain = app_services.create_conversation_chain(
        llm=Mock(),
        retriever=Mock(),
        verbose=False,
    )

    assert chain is not None
    memory = captured["memory"]
    assert memory.memory_key == "chat_history"
    assert memory.output_key == "answer"
    assert captured["return_source_documents"] is True
    assert captured["verbose"] is False


def test_create_hybrid_agent_instance_passes_use_tools(monkeypatch):
    captured = {}

    def fake_create_hybrid_agent(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(app_services, "create_hybrid_agent", fake_create_hybrid_agent)

    agent = app_services.create_hybrid_agent_instance(
        llm=Mock(),
        retriever=Mock(),
        verbose=True,
    )

    assert agent is not None
    assert captured["use_tools"] is True
    assert captured["verbose"] is True
