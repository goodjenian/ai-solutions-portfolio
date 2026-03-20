from unittest.mock import MagicMock

import pytest
from langchain_core.documents import Document

from vector_store.chroma_store import ChromaPropertyStore
from vector_store.hybrid_retriever import create_retriever
from vector_store.reranker import StrategicReranker


@pytest.fixture
def mock_vector_store():
    store = MagicMock(spec=ChromaPropertyStore)
    return store


@pytest.fixture
def mock_reranker():
    reranker = MagicMock(spec=StrategicReranker)
    return reranker


def test_hybrid_retriever_with_reranker(mock_vector_store, mock_reranker):
    # Setup mock store to return some documents
    docs = [
        Document(page_content="doc1", metadata={"id": "1", "price": 100000}),
        Document(page_content="doc2", metadata={"id": "2", "price": 200000}),
    ]

    # Mock search return (doc, score)
    mock_vector_store.search.return_value = [
        (docs[0], 0.9),
        (docs[1], 0.8),
    ]

    # Mock reranker to reverse order
    mock_reranker.rerank_with_strategy.return_value = [
        (docs[1], 0.95),
        (docs[0], 0.85),
    ]

    retriever = create_retriever(
        vector_store=mock_vector_store,
        k=2,
        search_type="similarity",
        reranker=mock_reranker,
        strategy="investor",
    )

    results = retriever.get_relevant_documents("query")

    # Verify reranker was called
    mock_reranker.rerank_with_strategy.assert_called_once()
    call_args = mock_reranker.rerank_with_strategy.call_args
    assert call_args.kwargs["query"] == "query"
    assert call_args.kwargs["strategy"] == "investor"
    assert len(call_args.kwargs["documents"]) == 2

    # Verify results are reranked (doc2 first)
    assert results[0].metadata["id"] == "2"
    assert results[1].metadata["id"] == "1"


def test_advanced_retriever_with_reranker_and_filters(mock_vector_store, mock_reranker):
    # Setup docs
    docs = [
        Document(page_content="doc1", metadata={"id": "1", "price": 100000}),  # Cheap
        Document(page_content="doc2", metadata={"id": "2", "price": 900000}),  # Expensive
        Document(page_content="doc3", metadata={"id": "3", "price": 150000}),  # Cheap
    ]

    # Mock search return
    mock_vector_store.search.return_value = [
        (docs[0], 0.9),
        (docs[1], 0.8),
        (docs[2], 0.7),
    ]

    # Mock reranker to just return what it gets (but we check if it received filtered list)
    def side_effect(query, documents, **kwargs):
        # Return same docs with same scores
        return [(d, 1.0) for d in documents]

    mock_reranker.rerank_with_strategy.side_effect = side_effect

    retriever = create_retriever(
        vector_store=mock_vector_store,
        k=5,
        search_type="similarity",
        max_price=200000,  # Should filter out doc2
        reranker=mock_reranker,
    )

    retriever.get_relevant_documents("query")

    # Verify reranker called with only 2 docs (doc1, doc3)
    mock_reranker.rerank_with_strategy.assert_called_once()
    call_args = mock_reranker.rerank_with_strategy.call_args
    passed_docs = call_args.kwargs["documents"]
    assert len(passed_docs) == 2
    ids = [d.metadata["id"] for d in passed_docs]
    assert "2" not in ids
    assert "1" in ids
    assert "3" in ids


def test_advanced_retriever_reranking_skipped_if_sort_by(mock_vector_store, mock_reranker):
    # Setup docs
    docs = [
        Document(page_content="doc1", metadata={"id": "1", "price": 100000}),
        Document(page_content="doc2", metadata={"id": "2", "price": 200000}),
    ]

    mock_vector_store.search.return_value = [
        (docs[0], 0.9),
        (docs[1], 0.8),
    ]

    retriever = create_retriever(
        vector_store=mock_vector_store,
        k=2,
        search_type="similarity",
        sort_by="price",  # Should disable reranking
        reranker=mock_reranker,
    )

    results = retriever.get_relevant_documents("query")

    # Verify reranker NOT called
    mock_reranker.rerank_with_strategy.assert_not_called()

    # Verify results sorted by price (ascending default)
    assert results[0].metadata["id"] == "1"  # 100k
    assert results[1].metadata["id"] == "2"  # 200k
