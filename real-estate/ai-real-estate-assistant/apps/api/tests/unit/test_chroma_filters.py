from vector_store.chroma_store import ChromaPropertyStore


def test_build_chroma_filter_basic(tmp_path, monkeypatch):
    store = ChromaPropertyStore(persist_directory=str(tmp_path))
    filters = {
        "city": "Krakow",
        "min_price": 300000,
        "max_price": 800000,
        "rooms": 2,
        "property_type": "apartment",
    }
    chroma = store._build_chroma_filter(filters)
    assert chroma is not None
    assert "$and" in chroma
    and_list = chroma["$and"]
    assert {"city": "Krakow"} in and_list
    assert {"price": {"$gte": 300000.0}} in and_list
    assert {"price": {"$lte": 800000.0}} in and_list
    assert {"rooms": {"$gte": 2.0}} in and_list
    assert {"property_type": "apartment"} in and_list
