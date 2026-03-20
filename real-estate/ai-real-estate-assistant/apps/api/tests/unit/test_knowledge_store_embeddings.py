import builtins

from vector_store.knowledge_store import KnowledgeStore, _create_embeddings


def test_create_embeddings_returns_none_when_unavailable(monkeypatch):
    monkeypatch.setattr(
        "vector_store.knowledge_store.app_settings.openai_api_key", "", raising=False
    )

    original_import = builtins.__import__

    def _fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name in {"langchain_community.embeddings.fastembed", "langchain_openai"}:
            raise ModuleNotFoundError(name)
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", _fake_import)

    emb = _create_embeddings()
    assert emb is None


def test_knowledge_store_ingest_and_stats(tmp_path):
    store = KnowledgeStore(persist_directory=str(tmp_path), collection_name="knowledge-test")
    n = store.ingest_text("hello world", source="test.txt")
    assert n >= 1
    results = store.similarity_search_with_score("hello", k=3)
    assert results and results[0][1] > 0
    stats = store.get_stats()
    assert stats["collection"] == "knowledge-test"
    assert stats["documents"] >= 1
