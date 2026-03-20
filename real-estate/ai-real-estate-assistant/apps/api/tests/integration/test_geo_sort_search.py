from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document

from vector_store.chroma_store import ChromaPropertyStore


@pytest.fixture
def mock_store():
    store = MagicMock(spec=ChromaPropertyStore)
    # We want to test the actual logic of hybrid_search, so we shouldn't mock it.
    # But hybrid_search is a method of ChromaPropertyStore.
    # So we should probably instantiate a real ChromaPropertyStore but mock its internal 'search' method
    # and maybe 'embedding_function' and 'client'.

    # However, ChromaPropertyStore.__init__ does setup.
    # Let's mock the class partially or just patch 'search' on an instance.
    return store


class TestGeoSortSearch:
    @pytest.fixture
    def store_with_mocked_search(self):
        # Create a store instance with mocked internals
        # We patch the methods called in __init__ to avoid side effects
        with (
            patch.object(ChromaPropertyStore, "_create_embeddings", return_value=MagicMock()),
            patch.object(ChromaPropertyStore, "_initialize_vector_store", return_value=MagicMock()),
        ):
            store = ChromaPropertyStore()
            # Mock the search method to return predefined docs
            store.search = MagicMock()
            return store

    def test_geo_filtering_logic(self, store_with_mocked_search):
        """Test that hybrid_search correctly applies bounding box filter and post-filtering."""
        store = store_with_mocked_search

        # Center point: Paris (approx 48.8566, 2.3522)
        center_lat = 48.8566
        center_lon = 2.3522

        # Doc 1: Very close (0.5 km)
        doc1 = Document(
            page_content="Close property",
            metadata={"id": "1", "lat": 48.8566 + 0.004, "lon": 2.3522, "price": 500000},
        )

        # Doc 2: Inside bounding box but outside radius (e.g. corner of box)
        # 1 degree lat is ~111km. 5km radius is ~0.045 deg.
        # Let's put something 6km away.
        # 0.054 deg lat change approx 6km.
        doc2 = Document(
            page_content="Far property",
            metadata={"id": "2", "lat": 48.8566 + 0.054, "lon": 2.3522, "price": 400000},
        )

        store.search.return_value = [(doc1, 0.1), (doc2, 0.2)]

        # Call hybrid_search with 5km radius
        results = store.hybrid_search(
            query="apartment",
            lat=center_lat,
            lon=center_lon,
            radius_km=5.0,
            alpha=1.0,  # Pure vector score to simplify
        )

        # Check that search was called with some filter containing lat/lon ranges
        call_args = store.search.call_args
        assert call_args is not None
        filters = (
            call_args[1].get("filter") or call_args[0][2]
            if len(call_args[0]) > 2
            else call_args[1].get("filter")
        )

        # Verify bounding box filter structure
        assert "$and" in filters
        # We expect 4 conditions for lat/lon bounds
        assert len(filters["$and"]) >= 4

        # Verify results: Doc 2 should be filtered out by Haversine check
        ids = [doc.metadata["id"] for doc, _ in results]
        assert "1" in ids
        assert "2" not in ids

    def test_sorting_logic(self, store_with_mocked_search):
        """Test sorting by price and other fields."""
        store = store_with_mocked_search

        doc1 = Document(page_content="Cheap", metadata={"id": "1", "price": 100000, "area_sqm": 50})
        doc2 = Document(
            page_content="Expensive", metadata={"id": "2", "price": 500000, "area_sqm": 100}
        )
        doc3 = Document(page_content="Mid", metadata={"id": "3", "price": 250000, "area_sqm": 75})

        store.search.return_value = [(doc1, 0.1), (doc2, 0.2), (doc3, 0.15)]

        # Sort by Price ASC
        results_asc = store.hybrid_search(query="test", sort_by="price", sort_order="asc")
        ids_asc = [doc.metadata["id"] for doc, _ in results_asc]
        assert ids_asc == ["1", "3", "2"]

        # Sort by Price DESC
        results_desc = store.hybrid_search(query="test", sort_by="price", sort_order="desc")
        ids_desc = [doc.metadata["id"] for doc, _ in results_desc]
        assert ids_desc == ["2", "3", "1"]

        # Sort by Area DESC
        results_area = store.hybrid_search(query="test", sort_by="area_sqm", sort_order="desc")
        ids_area = [doc.metadata["id"] for doc, _ in results_area]
        assert ids_area == ["2", "3", "1"]

    def test_sorting_with_missing_values(self, store_with_mocked_search):
        """Test sorting when some docs miss the field."""
        store = store_with_mocked_search

        doc1 = Document(page_content="Has price", metadata={"id": "1", "price": 100000})
        doc2 = Document(page_content="No price", metadata={"id": "2"})  # No price

        store.search.return_value = [(doc1, 0.1), (doc2, 0.2)]

        # Sort by Price ASC - Missing should be last?
        # Logic says: if reverse (DESC), None is -inf (Last).
        # If ASC, None is inf (Last).

        results_asc = store.hybrid_search(query="test", sort_by="price", sort_order="asc")
        ids_asc = [doc.metadata["id"] for doc, _ in results_asc]
        assert ids_asc == ["1", "2"]

        results_desc = store.hybrid_search(query="test", sort_by="price", sort_order="desc")
        ids_desc = [doc.metadata["id"] for doc, _ in results_desc]
        assert ids_desc == ["1", "2"]  # Both put it last?

        # Wait, let's check my logic in implementation
        # if reverse (DESC): return float('-inf') -> NO, -inf is smallest, so it comes LAST in DESC sort (Big to Small).
        # Wait. DESC sort: 10, 5, 1, -inf. Yes, Last.

        # if not reverse (ASC): return float('inf') -> inf is biggest, so it comes LAST in ASC sort (Small to Big).
        # Wait. ASC sort: 1, 5, 10, inf. Yes, Last.

        # So in both cases, it should be last. Correct.

    def test_bbox_filter_is_applied_to_search_call(self, store_with_mocked_search):
        store = store_with_mocked_search

        doc1 = Document(
            page_content="In bbox", metadata={"id": "1", "lat": 50.5, "lon": 19.5, "price": 100000}
        )
        store.search.return_value = [(doc1, 0.1)]

        store.hybrid_search(
            query="apartment",
            min_lat=50.0,
            max_lat=51.0,
            min_lon=19.0,
            max_lon=20.0,
            alpha=1.0,
        )

        call_args = store.search.call_args
        assert call_args is not None
        filters = call_args[1].get("filter")
        assert filters is not None
        assert "$and" in filters
        assert {"lat": {"$gte": 50.0}} in filters["$and"]
        assert {"lat": {"$lte": 51.0}} in filters["$and"]
        assert {"lon": {"$gte": 19.0}} in filters["$and"]
        assert {"lon": {"$lte": 20.0}} in filters["$and"]
