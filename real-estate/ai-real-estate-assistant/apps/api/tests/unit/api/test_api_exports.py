from io import BytesIO
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from langchain_core.documents import Document

from api.dependencies import get_vector_store
from api.main import app
from api.routers import exports as exports_router
from vector_store.chroma_store import ChromaPropertyStore

client = TestClient(app)


@pytest.fixture
def mock_store():
    return MagicMock(spec=ChromaPropertyStore)


@pytest.fixture
def valid_headers():
    return {"X-API-Key": "dev-secret-key"}


def test_export_properties_by_ids_csv_success(mock_store, valid_headers):
    mock_store.get_properties_by_ids.return_value = [
        Document(
            page_content="x",
            metadata={"id": "p1", "city": "Krakow", "price": 1000, "rooms": 2},
        )
    ]
    app.dependency_overrides[get_vector_store] = lambda: mock_store

    response = client.post(
        "/api/v1/export/properties",
        json={"format": "csv", "property_ids": ["p1"]},
        headers=valid_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "Krakow" in response.text
    assert "price" in response.text

    app.dependency_overrides = {}


def test_export_properties_by_search_json_success(mock_store, valid_headers):
    mock_store.hybrid_search.return_value = [
        (
            Document(page_content="x", metadata={"id": "p1", "city": "Warsaw", "price": 1200}),
            0.9,
        )
    ]
    app.dependency_overrides[get_vector_store] = lambda: mock_store

    response = client.post(
        "/api/v1/export/properties",
        json={"format": "json", "search": {"query": "test", "limit": 1}},
        headers=valid_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert '"properties"' in response.text
    assert "Warsaw" in response.text

    app.dependency_overrides = {}


def test_export_properties_invalid_columns_returns_400(mock_store, valid_headers):
    mock_store.get_properties_by_ids.return_value = [
        Document(page_content="x", metadata={"id": "p1", "city": "Krakow", "price": 1000})
    ]
    app.dependency_overrides[get_vector_store] = lambda: mock_store

    response = client.post(
        "/api/v1/export/properties",
        json={
            "format": "csv",
            "property_ids": ["p1"],
            "columns": ["not_a_column"],
        },
        headers=valid_headers,
    )

    assert response.status_code == 400
    assert "Unknown columns" in response.text
    app.dependency_overrides = {}


def test_export_properties_csv_delimiter_is_applied(mock_store, valid_headers):
    mock_store.get_properties_by_ids.return_value = [
        Document(page_content="x", metadata={"id": "p1", "city": "Krakow", "price": 1000})
    ]
    app.dependency_overrides[get_vector_store] = lambda: mock_store

    response = client.post(
        "/api/v1/export/properties",
        json={
            "format": "csv",
            "property_ids": ["p1"],
            "columns": ["id", "city", "price"],
            "csv_delimiter": ";",
        },
        headers=valid_headers,
    )

    assert response.status_code == 200
    header_line = response.text.splitlines()[0]
    assert header_line == "id;city;price"
    app.dependency_overrides = {}


def test_export_properties_requires_property_ids_or_search(mock_store, valid_headers):
    app.dependency_overrides[get_vector_store] = lambda: mock_store

    response = client.post(
        "/api/v1/export/properties",
        json={"format": "csv"},
        headers=valid_headers,
    )

    assert response.status_code == 422
    app.dependency_overrides = {}


def test_export_properties_store_unavailable(valid_headers):
    app.dependency_overrides[get_vector_store] = lambda: None

    response = client.post(
        "/api/v1/export/properties",
        json={"format": "csv", "property_ids": ["p1"]},
        headers=valid_headers,
    )

    assert response.status_code == 503
    app.dependency_overrides = {}


def test_export_properties_unauthorized():
    response = client.post(
        "/api/v1/export/properties", json={"format": "csv", "property_ids": ["p1"]}
    )
    assert response.status_code == 401


def test_documents_to_export_rows_fills_missing_id():
    docs = [Document(page_content="x", metadata={"city": "Krakow"})]
    rows = exports_router._documents_to_export_rows(docs)
    assert rows == [{"city": "Krakow", "id": "unknown"}]


def test_export_properties_by_ids_markdown_success(mock_store, valid_headers, monkeypatch):
    def fake_export_to_markdown(self, include_summary, max_properties):
        return "markdown-export"

    monkeypatch.setattr(
        exports_router.PropertyExporter, "export_to_markdown", fake_export_to_markdown
    )
    mock_store.get_properties_by_ids.return_value = [
        Document(page_content="x", metadata={"id": "p1"})
    ]
    app.dependency_overrides[get_vector_store] = lambda: mock_store

    response = client.post(
        "/api/v1/export/properties",
        json={"format": "md", "property_ids": ["p1"]},
        headers=valid_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    assert response.text == "markdown-export"
    assert response.headers.get("content-disposition", "").endswith('.md"')

    app.dependency_overrides = {}


def test_export_properties_by_ids_excel_success(mock_store, valid_headers, monkeypatch):
    def fake_export_to_excel(self, include_summary, include_statistics, columns=None):
        buf = BytesIO(b"fake-xlsx")
        buf.seek(0)
        return buf

    monkeypatch.setattr(exports_router.PropertyExporter, "export_to_excel", fake_export_to_excel)
    mock_store.get_properties_by_ids.return_value = [
        Document(page_content="x", metadata={"id": "p1"})
    ]
    app.dependency_overrides[get_vector_store] = lambda: mock_store

    response = client.post(
        "/api/v1/export/properties",
        json={"format": "xlsx", "property_ids": ["p1"]},
        headers=valid_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert response.content == b"fake-xlsx"
    assert response.headers.get("content-disposition", "").endswith('.xlsx"')

    app.dependency_overrides = {}


def test_export_properties_by_ids_pdf_success(mock_store, valid_headers, monkeypatch):
    def fake_export_to_pdf(self):
        buf = BytesIO(b"fake-pdf")
        buf.seek(0)
        return buf

    monkeypatch.setattr(exports_router.PropertyExporter, "export_to_pdf", fake_export_to_pdf)
    mock_store.get_properties_by_ids.return_value = [
        Document(page_content="x", metadata={"id": "p1"})
    ]
    app.dependency_overrides[get_vector_store] = lambda: mock_store

    response = client.post(
        "/api/v1/export/properties",
        json={"format": "pdf", "property_ids": ["p1"]},
        headers=valid_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.content == b"fake-pdf"
    assert response.headers.get("content-disposition", "").endswith('.pdf"')

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_export_properties_unsupported_format_raises(mock_store):
    class FakeFormat:
        value = "bogus"

    request = SimpleNamespace(
        property_ids=["p1"],
        search=None,
        format=FakeFormat(),
        columns=None,
        include_header=True,
        pretty=True,
        include_metadata=True,
        include_summary=True,
        include_statistics=True,
        max_properties=None,
    )
    mock_store.get_properties_by_ids.return_value = []

    with pytest.raises(HTTPException) as exc:
        await exports_router.export_properties(request=request, store=mock_store)

    assert exc.value.status_code == 400
