from vector_store.knowledge_store import KnowledgeStore, _create_embeddings


def test_ingest_and_search_basic():
    ks = KnowledgeStore()
    added = ks.ingest_text("Warsaw is the capital of Poland.", source="facts.md")
    assert added > 0
    res = ks.similarity_search_with_score("capital of Poland", k=5)
    assert len(res) >= 1
    doc, score = res[0]
    assert isinstance(score, float)
    assert doc.metadata["source"] == "facts.md"


def test_ingest_multiple_chunks_and_citations_metadata():
    ks = KnowledgeStore()
    text = "Line1\n\n" + ("Data " * 500) + "\n\nLine2"
    added = ks.ingest_text(text, source="long.md")
    assert added >= 2
    res = ks.similarity_search_with_score("Data", k=3)
    assert len(res) > 0
    for doc, _ in res:
        assert doc.metadata["source"] == "long.md"
        assert "chunk_index" in doc.metadata


def test_empty_query_returns_empty_results():
    ks = KnowledgeStore()
    ks.ingest_text("Hello world", source="a.md")
    res = ks.similarity_search_with_score("", k=5)
    assert res == []


def test_embeddings_factory_invocation():
    # Should not raise even if providers unavailable
    _ = _create_embeddings()


def test_get_stats_counts_docs():
    ks = KnowledgeStore()
    ks.ingest_text("a " * 500, source="s.md")
    stats = ks.get_stats()
    assert stats["documents"] >= 1


def test_ingest_text_segments_preserves_segment_metadata_and_sequential_chunk_index():
    ks = KnowledgeStore()
    added = ks.ingest_text_segments(
        segments=[
            ("alpha", {"page_number": 1}),
            ("beta", {"page_number": 2}),
        ],
        source="doc.pdf",
    )
    assert added >= 2
    res = ks.similarity_search_with_score("beta", k=5)
    assert len(res) >= 1
    doc, _score = res[0]
    assert doc.metadata["source"] == "doc.pdf"
    assert doc.metadata["page_number"] == 2
    assert isinstance(doc.metadata["chunk_index"], int)
