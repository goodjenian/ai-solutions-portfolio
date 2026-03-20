from utils.saved_searches import SavedSearch, SavedSearchManager, UserPreferences


def test_saved_search_manager_searches_preferences_and_favorites(tmp_path):
    manager = SavedSearchManager(storage_path=str(tmp_path))

    search = SavedSearch(id="s1", name="Test", city="Warsaw", max_price=1000)
    manager.save_search(search)
    assert manager.get_search("s1") is not None
    assert len(manager.get_all_searches()) == 1

    manager.increment_search_usage("s1")
    updated = manager.get_search("s1")
    assert updated is not None
    assert updated.use_count == 1
    assert updated.last_used is not None

    assert manager.delete_search("missing") is False
    assert manager.delete_search("s1") is True
    assert manager.get_search("s1") is None

    prefs = UserPreferences(
        default_sort="rooms", results_per_page=25, show_map=False, preferred_provider="openai"
    )
    manager.update_preferences(prefs)
    got = manager.get_preferences()
    assert got.default_sort == "rooms"
    assert got.results_per_page == 25
    assert got.show_map is False
    assert got.preferred_provider == "openai"

    fav1 = manager.add_favorite("p1", notes="note", tags=["a"])
    assert fav1.property_id == "p1"
    assert manager.is_favorite("p1") is True

    fav2 = manager.add_favorite("p1", notes="updated", tags=["b", "c"])
    assert fav2.property_id == "p1"
    assert fav2.notes == "updated"
    assert fav2.tags == ["b", "c"]
    assert len(manager.get_favorites()) == 1

    assert manager.remove_favorite("missing") is False
    assert manager.remove_favorite("p1") is True
    assert manager.is_favorite("p1") is False


def test_saved_search_manager_loads_from_disk(tmp_path):
    manager = SavedSearchManager(storage_path=str(tmp_path))
    manager.save_search(SavedSearch(id="s1", name="Test", city="Krakow"))
    manager.update_preferences(UserPreferences(default_sort="price_desc", results_per_page=5))
    manager.add_favorite("p2", notes="hello", tags=["x"])

    reloaded = SavedSearchManager(storage_path=str(tmp_path))
    assert reloaded.get_search("s1") is not None
    assert reloaded.get_preferences().default_sort == "price_desc"
    assert reloaded.is_favorite("p2") is True
    favs = reloaded.get_favorites()
    assert favs and favs[0].property_id == "p2"
