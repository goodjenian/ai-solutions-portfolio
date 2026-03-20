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


def test_search_properties_success(mock_store, valid_headers):
    # Mock search results
    mock_prop = Property(id="prop1", city="Test City", price=1000, rooms=2, title="Test Property")
    # Simulate metadata stored in Chroma
    # Enums are usually stored as values
    metadata = mock_prop.model_dump()
    metadata["property_type"] = mock_prop.property_type.value
    metadata["listing_type"] = mock_prop.listing_type.value
    # Remove None values as Chroma might not store them or they might be missing
    metadata = {k: v for k, v in metadata.items() if v is not None}

    mock_doc = Document(page_content="test content", metadata=metadata)
    mock_store.hybrid_search.return_value = [(mock_doc, 0.95)]

    # Override dependency
    app.dependency_overrides[get_vector_store] = lambda: mock_store

    response = client.post(
        "/api/v1/search", json={"query": "test query", "limit": 5}, headers=valid_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["results"][0]["score"] == 0.95
    assert data["results"][0]["property"]["id"] == "prop1"
    assert data["results"][0]["property"]["city"] == "Test City"

    # Clean up
    app.dependency_overrides = {}


def test_search_properties_empty(mock_store, valid_headers):
    mock_store.search.return_value = []
    app.dependency_overrides[get_vector_store] = lambda: mock_store

    response = client.post(
        "/api/v1/search", json={"query": "nothing matches"}, headers=valid_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0
    assert data["results"] == []

    app.dependency_overrides = {}


def test_search_store_unavailable(valid_headers):
    # Simulate store not available (None)
    app.dependency_overrides[get_vector_store] = lambda: None

    response = client.post("/api/v1/search", json={"query": "test"}, headers=valid_headers)

    assert response.status_code == 503
    assert "not available" in response.json()["detail"]

    app.dependency_overrides = {}


def test_search_internal_error(mock_store, valid_headers):
    mock_store.hybrid_search.side_effect = Exception("DB Error")
    app.dependency_overrides[get_vector_store] = lambda: mock_store

    response = client.post("/api/v1/search", json={"query": "crash"}, headers=valid_headers)

    assert response.status_code == 500
    assert "Search operation failed" in response.json()["detail"]

    app.dependency_overrides = {}


def test_search_bbox_is_forwarded(mock_store, valid_headers):
    mock_prop = Property(id="prop1", city="Test City", price=1000, rooms=2, title="Test Property")
    metadata = mock_prop.model_dump()
    metadata["property_type"] = mock_prop.property_type.value
    metadata["listing_type"] = mock_prop.listing_type.value
    metadata = {k: v for k, v in metadata.items() if v is not None}
    mock_doc = Document(page_content="test content", metadata=metadata)
    mock_store.hybrid_search.return_value = [(mock_doc, 0.95)]

    app.dependency_overrides[get_vector_store] = lambda: mock_store

    response = client.post(
        "/api/v1/search",
        json={
            "query": "test query",
            "limit": 5,
            "min_lat": 50.0,
            "max_lat": 51.0,
            "min_lon": 19.0,
            "max_lon": 20.0,
        },
        headers=valid_headers,
    )

    assert response.status_code == 200
    mock_store.hybrid_search.assert_called_once()
    _, kwargs = mock_store.hybrid_search.call_args
    assert kwargs["min_lat"] == 50.0
    assert kwargs["max_lat"] == 51.0
    assert kwargs["min_lon"] == 19.0
    assert kwargs["max_lon"] == 20.0

    app.dependency_overrides = {}


def test_search_unauthorized():
    response = client.post("/api/v1/search", json={"query": "test"})
    assert response.status_code == 401
