from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from langchain_core.documents import Document

from api.dependencies import get_vector_store
from api.main import app
from data.schemas import Property
from vector_store.chroma_store import ChromaPropertyStore

client = TestClient(app)


@pytest.fixture
def mock_store():
    store = MagicMock(spec=ChromaPropertyStore)
    return store


@pytest.fixture
def valid_headers():
    return {"X-API-Key": "dev-secret-key"}


def test_sorting_forwarded_to_hybrid_search(mock_store, valid_headers):
    prop = Property(id="p1", city="Krakow", price=500000, rooms=3, title="Nice flat")
    md = {k: v for k, v in prop.model_dump().items() if v is not None}
    doc = Document(page_content="desc", metadata=md)
    mock_store.hybrid_search.return_value = [(doc, 0.9)]

    app.dependency_overrides[get_vector_store] = lambda: mock_store

    payload = {
        "query": "apartment",
        "limit": 5,
        "sort_by": "price",
        "sort_order": "asc",
    }
    resp = client.post("/api/v1/search", json=payload, headers=valid_headers)
    assert resp.status_code == 200
    mock_store.hybrid_search.assert_called_once()
    _, kwargs = mock_store.hybrid_search.call_args
    assert kwargs["sort_by"] == "price"
    assert kwargs["sort_order"] == "asc"

    app.dependency_overrides = {}
