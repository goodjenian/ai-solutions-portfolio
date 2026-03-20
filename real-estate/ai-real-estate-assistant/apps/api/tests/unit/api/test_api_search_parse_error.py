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


def test_search_handles_parse_errors(mock_store, valid_headers):
    bad_doc = Document(page_content="bad", metadata={"id": "bad"})
    good_prop = Property(id="ok1", city="City", price=1000, rooms=2, title="Okay Title")
    md = good_prop.model_dump()
    md["property_type"] = good_prop.property_type.value
    md["listing_type"] = good_prop.listing_type.value
    md = {k: v for k, v in md.items() if v is not None}
    good_doc = Document(page_content="good", metadata=md)
    mock_store.hybrid_search.return_value = [(bad_doc, 0.5), (good_doc, 0.9)]

    app.dependency_overrides[get_vector_store] = lambda: mock_store
    resp = client.post(
        "/api/v1/search",
        json={"query": "test", "limit": 5},
        headers=valid_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1
    assert data["results"][0]["property"]["id"] == "ok1"
    app.dependency_overrides = {}
