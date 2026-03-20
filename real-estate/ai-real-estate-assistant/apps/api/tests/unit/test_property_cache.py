import json

import utils.property_cache as property_cache
from data.schemas import PropertyCollection


def test_property_cache_save_load_previous_and_clear(tmp_path, monkeypatch):
    cache_dir = tmp_path / "cache"
    monkeypatch.setattr(property_cache, "CACHE_DIR", cache_dir)
    monkeypatch.setattr(property_cache, "CACHE_FILE", cache_dir / "properties.json")
    monkeypatch.setattr(property_cache, "PREV_CACHE_FILE", cache_dir / "properties_prev.json")

    c1 = PropertyCollection(properties=[], total_count=0, source="test")
    property_cache.save_collection(c1)
    loaded = property_cache.load_collection()
    assert loaded is not None
    assert loaded.total_count == 0
    assert loaded.source == "test"

    c2 = PropertyCollection(properties=[], total_count=0, source="test2")
    property_cache.save_collection(c2)

    prev = property_cache.load_previous_collection()
    assert prev is not None
    assert prev.source == "test"

    property_cache.clear_cache()
    assert property_cache.load_collection() is None
    assert property_cache.load_previous_collection() is None


def test_property_cache_load_returns_none_on_invalid_json(tmp_path, monkeypatch):
    cache_dir = tmp_path / "cache"
    monkeypatch.setattr(property_cache, "CACHE_DIR", cache_dir)
    monkeypatch.setattr(property_cache, "CACHE_FILE", cache_dir / "properties.json")
    monkeypatch.setattr(property_cache, "PREV_CACHE_FILE", cache_dir / "properties_prev.json")

    cache_dir.mkdir(parents=True, exist_ok=True)
    property_cache.CACHE_FILE.write_text(json.dumps({"invalid": "shape"}), encoding="utf-8")
    assert property_cache.load_collection() is None


def test_property_cache_handles_write_and_unlink_errors(tmp_path, monkeypatch):
    import pathlib

    cache_dir = tmp_path / "cache"
    monkeypatch.setattr(property_cache, "CACHE_DIR", cache_dir)
    monkeypatch.setattr(property_cache, "CACHE_FILE", cache_dir / "properties.json")
    monkeypatch.setattr(property_cache, "PREV_CACHE_FILE", cache_dir / "properties_prev.json")

    c1 = PropertyCollection(properties=[], total_count=0)
    property_cache.save_collection(c1)

    original_write_text = pathlib.Path.write_text

    def _write_text(self, data, *args, **kwargs):
        if self.name == "properties_prev.json":
            raise OSError("nope")
        return original_write_text(self, data, *args, **kwargs)

    monkeypatch.setattr(pathlib.Path, "write_text", _write_text, raising=True)
    property_cache.save_collection(PropertyCollection(properties=[], total_count=0))

    original_write_text(property_cache.PREV_CACHE_FILE, "{", encoding="utf-8")
    assert property_cache.load_previous_collection() is None

    original_unlink = pathlib.Path.unlink

    def _unlink(self, *args, **kwargs):
        raise OSError("nope")

    monkeypatch.setattr(pathlib.Path, "unlink", _unlink, raising=True)
    property_cache.clear_cache()

    monkeypatch.setattr(pathlib.Path, "unlink", original_unlink, raising=True)
