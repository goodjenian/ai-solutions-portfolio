import threading
from unittest.mock import MagicMock, patch

from langchain_core.documents import Document

from ai.app_services import create_property_retriever
from analytics.market_insights import MarketInsights
from data.schemas import ListingType, Property, PropertyCollection, PropertyType
from vector_store.chroma_store import ChromaPropertyStore


def test_property_retriever_forced_listing_type_filters_results(tmp_path, monkeypatch):
    with patch.object(ChromaPropertyStore, "_create_embeddings", return_value=None):
        store = ChromaPropertyStore(persist_directory=str(tmp_path))

    docs = [
        Document(page_content="rent 1", metadata={"listing_type": "rent"}),
        Document(page_content="rent 2", metadata={"listing_type": "rent"}),
        Document(page_content="sale 1", metadata={"listing_type": "sale"}),
    ]

    class FakeInnerRetriever:
        def get_relevant_documents(self, query: str):
            return docs

    captured = {}

    def fake_get_retriever(
        *,
        search_type: str,
        k: int,
        fetch_k: int,
        lambda_mult: float,
        filter=None,
        **kwargs,
    ):
        captured["search_type"] = search_type
        captured["k"] = k
        captured["fetch_k"] = fetch_k
        captured["lambda_mult"] = lambda_mult
        captured["filter"] = filter
        return FakeInnerRetriever()

    monkeypatch.setattr(store, "get_retriever", fake_get_retriever)

    retriever = create_property_retriever(
        vector_store=store,
        k_results=10,
        center_lat=None,
        center_lon=None,
        radius_km=None,
        listing_type_filter="Rent",
    )

    results = retriever.get_relevant_documents("apartments")
    assert len(results) == 2
    assert {doc.metadata.get("listing_type") for doc in results} == {"rent"}
    assert captured["filter"] == {"listing_type": "rent"}
    assert captured["k"] == 20
    assert captured["fetch_k"] == 20


def test_property_retriever_uses_fallback_while_indexing(tmp_path):
    started = threading.Event()
    allow_finish = threading.Event()

    fake_vector_store = MagicMock()
    fake_vector_store._collection = MagicMock()
    fake_vector_store._collection.count.return_value = 0
    fake_vector_store._collection.get.return_value = {"ids": []}

    def add_documents_side_effect(*args, **kwargs):
        started.set()
        allow_finish.wait(timeout=5)
        return None

    fake_vector_store.add_documents = MagicMock(side_effect=add_documents_side_effect)
    fake_vector_store._collection.add = MagicMock(side_effect=add_documents_side_effect)
    fake_vector_store.as_retriever = MagicMock()
    fake_vector_store.similarity_search_with_score = MagicMock(
        return_value=[(Document(page_content="vs", metadata={"id": "vs"}), 0.1)]
    )

    with (
        patch.object(ChromaPropertyStore, "_create_embeddings", return_value=MagicMock()),
        patch.object(
            ChromaPropertyStore, "_initialize_vector_store", return_value=fake_vector_store
        ),
    ):
        store = ChromaPropertyStore(persist_directory=str(tmp_path))

    props = [
        Property(
            id="p1",
            city="Krakow",
            price=900,
            rooms=2,
            bathrooms=1,
            area_sqm=50,
            property_type=PropertyType.APARTMENT,
            has_garden=True,
            has_balcony=True,
            description="balcony garden",
        ),
        Property(
            id="p2",
            city="Warsaw",
            price=1200,
            rooms=3,
            bathrooms=1,
            area_sqm=55,
            property_type=PropertyType.APARTMENT,
            description="garage",
        ),
    ]
    coll = PropertyCollection(properties=props, total_count=len(props))

    fut = store.add_property_collection_async(coll)
    assert started.wait(timeout=5)

    retriever = create_property_retriever(
        vector_store=store,
        k_results=5,
        center_lat=None,
        center_lon=None,
        radius_km=None,
        listing_type_filter=None,
    )
    results = retriever.get_relevant_documents("garden balcony")
    assert results and results[0].metadata.get("id") == "p1"
    assert fake_vector_store.as_retriever.call_count == 0
    assert fake_vector_store.similarity_search_with_score.call_count == 0

    allow_finish.set()
    assert fut.result(timeout=10) == 2


def test_property_retriever_geo_radius_filters_results(tmp_path, monkeypatch):
    with patch.object(ChromaPropertyStore, "_create_embeddings", return_value=None):
        store = ChromaPropertyStore(persist_directory=str(tmp_path))

    docs = [
        Document(page_content="near", metadata={"lat": 52.23, "lon": 21.01}),
        Document(page_content="far", metadata={"lat": 50.06, "lon": 19.94}),
    ]

    class FakeInnerRetriever:
        def get_relevant_documents(self, query: str):
            return docs

    def fake_get_retriever(**kwargs):
        return FakeInnerRetriever()

    monkeypatch.setattr(store, "get_retriever", fake_get_retriever)

    retriever = create_property_retriever(
        vector_store=store,
        k_results=10,
        center_lat=52.23,
        center_lon=21.01,
        radius_km=10.0,
        listing_type_filter=None,
    )

    results = retriever.get_relevant_documents("apartments")
    assert [d.page_content for d in results] == ["near"]


def test_property_retriever_price_range_filters_results(tmp_path, monkeypatch):
    with patch.object(ChromaPropertyStore, "_create_embeddings", return_value=None):
        store = ChromaPropertyStore(persist_directory=str(tmp_path))

    docs = [
        Document(page_content="low", metadata={"price": 1000}),
        Document(page_content="mid", metadata={"price": 1500}),
        Document(page_content="high", metadata={"price": 2500}),
    ]

    class FakeInnerRetriever:
        def get_relevant_documents(self, query: str):
            return docs

    def fake_get_retriever(**kwargs):
        return FakeInnerRetriever()

    monkeypatch.setattr(store, "get_retriever", fake_get_retriever)

    retriever = create_property_retriever(
        vector_store=store,
        k_results=10,
        center_lat=None,
        center_lon=None,
        radius_km=None,
        listing_type_filter=None,
        min_price=1200.0,
        max_price=2000.0,
    )

    results = retriever.get_relevant_documents("apartments")
    assert [d.page_content for d in results] == ["mid"]


def test_property_retriever_year_built_and_energy_filters_results(tmp_path, monkeypatch):
    with patch.object(ChromaPropertyStore, "_create_embeddings", return_value=None):
        store = ChromaPropertyStore(persist_directory=str(tmp_path))

    docs = [
        Document(page_content="good", metadata={"year_built": 2010, "energy_cert": "B"}),
        Document(page_content="bad_year", metadata={"year_built": 1990, "energy_cert": "B"}),
        Document(page_content="bad_cert", metadata={"year_built": 2010, "energy_cert": "D"}),
        Document(page_content="missing_year", metadata={"year_built": None, "energy_cert": "B"}),
    ]

    class FakeInnerRetriever:
        def get_relevant_documents(self, query: str):
            return docs

    def fake_get_retriever(**kwargs):
        return FakeInnerRetriever()

    monkeypatch.setattr(store, "get_retriever", fake_get_retriever)

    retriever = create_property_retriever(
        vector_store=store,
        k_results=10,
        center_lat=None,
        center_lon=None,
        radius_km=None,
        listing_type_filter=None,
        year_built_min=2000,
        year_built_max=2020,
        energy_certs=["b"],
    )

    results = retriever.get_relevant_documents("apartments")
    assert [d.page_content for d in results] == ["good"]


def test_property_retriever_sorting_applies_after_retrieval(tmp_path, monkeypatch):
    with patch.object(ChromaPropertyStore, "_create_embeddings", return_value=None):
        store = ChromaPropertyStore(persist_directory=str(tmp_path))

    docs = [
        Document(page_content="a", metadata={"price_per_sqm": 20}),
        Document(page_content="b", metadata={"price_per_sqm": 5}),
        Document(page_content="c", metadata={"price_per_sqm": 10}),
    ]

    class FakeInnerRetriever:
        def get_relevant_documents(self, query: str):
            return docs

    def fake_get_retriever(**kwargs):
        return FakeInnerRetriever()

    monkeypatch.setattr(store, "get_retriever", fake_get_retriever)

    retriever = create_property_retriever(
        vector_store=store,
        k_results=10,
        center_lat=None,
        center_lon=None,
        radius_km=None,
        listing_type_filter=None,
        sort_by="price_per_sqm",
        sort_ascending=True,
    )

    results = retriever.get_relevant_documents("apartments")
    assert [d.page_content for d in results] == ["b", "c", "a"]


def test_market_insights_filter_properties_end_to_end():
    properties = [
        Property(
            id="p1",
            city="Warsaw",
            price=1000,
            area_sqm=50,
            rooms=2,
            property_type=PropertyType.APARTMENT,
            listing_type=ListingType.RENT,
            latitude=52.23,
            longitude=21.01,
            has_parking=True,
        ),
        Property(
            id="p2",
            city="Warsaw",
            price=5000,
            area_sqm=50,
            rooms=4,
            property_type=PropertyType.HOUSE,
            listing_type=ListingType.SALE,
            latitude=52.24,
            longitude=21.02,
            has_parking=False,
            has_balcony=True,
            is_furnished=True,
        ),
        Property(
            id="p3",
            city="Krakow",
            price=1200,
            area_sqm=60,
            rooms=2,
            property_type=PropertyType.APARTMENT,
            listing_type=ListingType.RENT,
            latitude=50.06,
            longitude=19.94,
        ),
    ]
    coll = PropertyCollection(properties=properties, total_count=len(properties))
    insights = MarketInsights(coll)

    df = insights.filter_properties(
        center_lat=52.23,
        center_lon=21.01,
        radius_km=10.0,
        listing_type="sale",
        min_price_per_sqm=90.0,
        must_have_balcony=True,
        must_be_furnished=True,
    )
    assert df["id"].tolist() == ["p2"]


def test_market_insights_filter_properties_handles_missing_coords_with_require_coords():
    properties = [
        Property(
            id="p1",
            city="Warsaw",
            price=1000,
            area_sqm=50,
            rooms=2,
            property_type=PropertyType.APARTMENT,
            listing_type=ListingType.RENT,
            latitude=52.23,
            longitude=21.01,
        ),
        Property(
            id="p2",
            city="Warsaw",
            price=1200,
            area_sqm=60,
            rooms=2,
            property_type=PropertyType.APARTMENT,
            listing_type=ListingType.RENT,
        ),
    ]
    coll = PropertyCollection(properties=properties, total_count=len(properties))
    insights = MarketInsights(coll)

    required_df = insights.filter_properties(require_coords=True)
    assert required_df["id"].tolist() == ["p1"]

    optional_df = insights.filter_properties(require_coords=False)
    assert set(optional_df["id"].tolist()) == {"p1", "p2"}
