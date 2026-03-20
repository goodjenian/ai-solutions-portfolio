from unittest.mock import patch

from langchain_core.documents import Document

from vector_store.chroma_store import ChromaPropertyStore
from vector_store.hybrid_retriever import AdvancedPropertyRetriever


def test_retriever_geo_radius_filters_docs(tmp_path):
    docs = [
        Document(
            page_content="Warsaw apt",
            metadata={"city": "Warsaw", "lat": 52.23, "lon": 21.01, "price": 5000},
        ),
        Document(
            page_content="Krakow apt",
            metadata={"city": "Krakow", "lat": 50.06, "lon": 19.94, "price": 4400},
        ),
    ]
    with patch.object(ChromaPropertyStore, "_create_embeddings", return_value=None):
        store = ChromaPropertyStore(persist_directory=str(tmp_path))
    retr = AdvancedPropertyRetriever(
        vector_store=store, center_lat=52.23, center_lon=21.01, radius_km=10.0
    )
    filtered = retr._filter_by_geo(docs)
    assert len(filtered) == 1
    assert filtered[0].metadata["city"] == "Warsaw"


def test_retriever_price_filter_skips_none_prices(tmp_path):
    docs = [
        Document(page_content="missing price", metadata={"price": None}),
        Document(page_content="ok price", metadata={"price": 5000}),
        Document(page_content="str price", metadata={"price": "4500"}),
        Document(page_content="bad price", metadata={"price": "n/a"}),
    ]
    with patch.object(ChromaPropertyStore, "_create_embeddings", return_value=None):
        store = ChromaPropertyStore(persist_directory=str(tmp_path))
    retr = AdvancedPropertyRetriever(vector_store=store, min_price=4600)
    filtered = retr._filter_by_price(docs)
    assert [d.page_content for d in filtered] == ["ok price"]


def test_retriever_sorting_handles_none_and_non_numeric(tmp_path):
    docs = [
        Document(page_content="a", metadata={"price_per_sqm": 20}),
        Document(page_content="b", metadata={"price_per_sqm": None}),
        Document(page_content="c", metadata={"price_per_sqm": "n/a"}),
        Document(page_content="d", metadata={"price_per_sqm": 10}),
    ]
    with patch.object(ChromaPropertyStore, "_create_embeddings", return_value=None):
        store = ChromaPropertyStore(persist_directory=str(tmp_path))
    retr = AdvancedPropertyRetriever(
        vector_store=store, sort_by="price_per_sqm", sort_ascending=True
    )
    sorted_docs = retr._sort_results(docs)
    assert [d.page_content for d in sorted_docs[:2]] == ["d", "a"]


def test_retriever_year_built_filter_skips_missing_or_non_numeric(tmp_path):
    docs = [
        Document(page_content="old", metadata={"year_built": 1990}),
        Document(page_content="new", metadata={"year_built": "2010"}),
        Document(page_content="missing", metadata={"year_built": None}),
        Document(page_content="bad", metadata={"year_built": "n/a"}),
    ]
    with patch.object(ChromaPropertyStore, "_create_embeddings", return_value=None):
        store = ChromaPropertyStore(persist_directory=str(tmp_path))
    retr = AdvancedPropertyRetriever(vector_store=store, year_built_min=2000, year_built_max=2020)
    filtered = retr._filter_by_year_built(docs)
    assert [d.page_content for d in filtered] == ["new"]


def test_retriever_energy_cert_filter_is_case_insensitive(tmp_path):
    docs = [
        Document(page_content="a", metadata={"energy_cert": "A"}),
        Document(page_content="b", metadata={"energy_cert": " b "}),
        Document(page_content="c", metadata={"energy_cert": "C"}),
        Document(page_content="missing", metadata={"energy_cert": None}),
    ]
    with patch.object(ChromaPropertyStore, "_create_embeddings", return_value=None):
        store = ChromaPropertyStore(persist_directory=str(tmp_path))
    retr = AdvancedPropertyRetriever(vector_store=store, energy_certs=["a", "B"])
    filtered = retr._filter_by_energy_certs(docs)
    assert [d.page_content for d in filtered] == ["a", "b"]


def test_advanced_retriever_filters_and_slices_to_k(tmp_path, monkeypatch):
    with patch.object(ChromaPropertyStore, "_create_embeddings", return_value=None):
        store = ChromaPropertyStore(persist_directory=str(tmp_path))

    docs = [
        Document(page_content="low", metadata={"price": 1000}),
        Document(page_content="mid", metadata={"price": 2000}),
        Document(page_content="high", metadata={"price": 3000}),
    ]

    class FakeInnerRetriever:
        def get_relevant_documents(self, query: str):
            return docs

    captured = {}

    def fake_get_retriever(**kwargs):
        captured.update(kwargs)
        return FakeInnerRetriever()

    monkeypatch.setattr(store, "get_retriever", fake_get_retriever)

    retr = AdvancedPropertyRetriever(
        vector_store=store,
        k=1,
        search_type="mmr",
        min_price=1500,
        sort_by="price",
        sort_ascending=True,
    )
    results = retr.get_relevant_documents("apartments")

    assert len(results) == 1
    assert results[0].page_content == "mid"
    assert captured["k"] == 20
    assert captured["fetch_k"] == 20
