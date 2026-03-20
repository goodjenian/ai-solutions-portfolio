from unittest.mock import patch

from vector_store.chroma_store import ChromaPropertyStore
from vector_store.hybrid_retriever import AdvancedPropertyRetriever, create_retriever


def test_factory_returns_advanced_when_geo_params_present(tmp_path):
    with patch.object(ChromaPropertyStore, "_create_embeddings", return_value=None):
        store = ChromaPropertyStore(persist_directory=str(tmp_path))
    retriever = create_retriever(
        vector_store=store,
        k=5,
        search_type="mmr",
        center_lat=52.23,
        center_lon=21.01,
        radius_km=10.0,
    )
    assert isinstance(retriever, AdvancedPropertyRetriever)
    assert retriever.center_lat == 52.23
    assert retriever.center_lon == 21.01
    assert retriever.radius_km == 10.0
