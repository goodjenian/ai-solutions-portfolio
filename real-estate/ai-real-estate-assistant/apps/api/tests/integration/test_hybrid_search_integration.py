from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document

from vector_store.chroma_store import ChromaPropertyStore


@pytest.fixture
def mock_vector_store_backend():
    """Mock the underlying LangChain Chroma object."""
    mock = MagicMock()
    return mock


@pytest.fixture
def store(mock_vector_store_backend):
    """Initialize ChromaPropertyStore with mocked backend."""
    # We mock _initialize_vector_store to return our mock
    # We also mock _create_embeddings to avoid loading models
    with (
        patch(
            "vector_store.chroma_store.ChromaPropertyStore._create_embeddings", return_value=None
        ),
        patch(
            "vector_store.chroma_store.ChromaPropertyStore._initialize_vector_store",
            return_value=mock_vector_store_backend,
        ),
    ):
        store = ChromaPropertyStore(persist_directory="dummy")
        # Manually set the vector_store in case __init__ didn't set it due to some logic
        store.vector_store = mock_vector_store_backend
        yield store


def test_hybrid_search_logic(store, mock_vector_store_backend):
    """
    Test the hybrid_search logic (filtering + BM25 rescoring)
    by mocking the vector store response.
    """
    # Setup mock documents
    doc1 = Document(
        page_content="Luxury apartment in city center",
        metadata={"id": "1", "city": "Paris", "price": 1000000},
    )
    doc2 = Document(
        page_content="Cozy studio in suburbs",
        metadata={"id": "2", "city": "Paris", "price": 200000},
    )
    doc3 = Document(
        page_content="Luxury house with garden",
        metadata={"id": "3", "city": "London", "price": 2000000},
    )

    # Mock vector search to return all docs with identical vector scores (distance 0.5)
    # This simulates "vector search found these, now rank them"
    mock_vector_store_backend.similarity_search_with_score.return_value = [
        (doc1, 0.5),
        (doc2, 0.5),
        (doc3, 0.5),
    ]

    # 1. Test Filter Propagation
    # When we call hybrid_search with filters, it should pass them to vector_store.search
    store.hybrid_search(query="apartment", filters={"city": "Paris"}, k=5, alpha=0.5)

    # Verify vector store was called with correct filters
    # hybrid_search calls self.search calls self.vector_store.search
    # _build_chroma_filter converts {"city": "Paris"} to {"city": {"$eq": "Paris"}} or similar
    # or just {"city": "Paris"} if simple.

    args, kwargs = mock_vector_store_backend.similarity_search_with_score.call_args
    # args[0] is query (actually it might be passed as kwarg or arg depending on LangChain version)
    # LangChain Chroma: similarity_search_with_score(query, k, filter, ...)
    # Let's check if it's positional or kwarg

    # If passed as kwargs to store.search, it passes to vector_store.similarity_search_with_score

    # The call in store.search is:
    # self.vector_store.similarity_search_with_score(query=query, k=k, filter=chroma_filter, **kwargs)

    assert kwargs["query"] == "apartment"
    expected_filter = {"city": {"$eq": "Paris"}}
    # Depending on how _build_chroma_filter works, simple dicts might be passed through if no special keys?
    # chroma_store.py line 557: if filter and not any(k.startswith("$") ...):
    #   if any(k in ["min_price"...]): _build_chroma_filter...
    #   else: chroma_filter = filter
    # "city" is not in the special list ["min_price", ...], so it might just pass {"city": "Paris"}

    # Let's be flexible
    actual_filter = kwargs.get("filter")
    if actual_filter == {"city": "Paris"}:
        pass
    else:
        assert actual_filter == expected_filter

    # 2. Test Keyword Rescoring (Alpha = 0.0, Pure Keyword)
    # Query: "garden"
    # Doc 3 has "garden".

    results = store.hybrid_search(
        query="garden",
        k=5,
        alpha=0.0,  # Pure keyword
    )

    # Doc 3 should be top 1 because of keyword match
    # Docs 1 and 2 don't have "garden"
    assert results[0][0].metadata["id"] == "3"

    # 3. Test Keyword Rescoring (Alpha = 1.0, Pure Vector)
    # All have vector score 0.5. Order should be preserved or stable.
    # BM25 should be ignored.

    results_vector = store.hybrid_search(query="garden", k=5, alpha=1.0)
    # Since vector scores are tied, order depends on input list.
    # We just ensure it ran without error and returned results.
    assert len(results_vector) == 3

    # 4. Test Hybrid (Alpha = 0.5)
    # Query: "luxury"
    # Doc 1 and Doc 3 have "Luxury". Doc 2 does not.
    # Doc 1 and 3 should be higher than 2.

    results_hybrid = store.hybrid_search(query="luxury", k=5, alpha=0.5)

    top_ids = [doc.metadata["id"] for doc, _ in results_hybrid[:2]]
    assert "1" in top_ids
    assert "3" in top_ids
    assert "2" not in top_ids
