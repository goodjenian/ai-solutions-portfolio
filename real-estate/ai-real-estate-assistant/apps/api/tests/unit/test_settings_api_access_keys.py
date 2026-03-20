from config.settings import AppSettings, _dedupe_preserve_order, _parse_csv_list


def test_parse_csv_list_trims_and_filters_empty():
    assert _parse_csv_list(None) == []
    assert _parse_csv_list("") == []
    assert _parse_csv_list(" , , ") == []
    assert _parse_csv_list(" a, b , ,c ") == ["a", "b", "c"]


def test_dedupe_preserve_order_keeps_first_occurrence():
    assert _dedupe_preserve_order([]) == []
    assert _dedupe_preserve_order(["a", "b", "a", "c", "b"]) == ["a", "b", "c"]


def test_app_settings_uses_api_access_key_when_rotated_keys_not_provided():
    s = AppSettings(environment="test", api_access_key="k1", api_access_keys=[])
    assert s.api_access_keys == ["k1"]
    assert s.api_access_key == "k1"


def test_app_settings_strips_primary_key_and_ignores_empty_values():
    s = AppSettings(environment="test", api_access_key="  k1  ", api_access_keys=[" ", "", "  "])
    assert s.api_access_keys == ["k1"]
    assert s.api_access_key == "k1"


def test_app_settings_uses_api_access_keys_and_sets_primary_to_first():
    s = AppSettings(environment="test", api_access_key=None, api_access_keys=["k2", "k1"])
    assert s.api_access_keys == ["k2", "k1"]
    assert s.api_access_key == "k2"


def test_app_settings_defaults_to_dev_secret_in_nonproduction_when_unset():
    # SECURITY: No default API key fallback. All environments require explicit key.
    # This prevents accidental deployment without proper authentication.
    s = AppSettings(environment="development", api_access_key=None, api_access_keys=[])
    assert s.api_access_keys == []
    assert s.api_access_key is None


def test_app_settings_does_not_default_to_dev_secret_in_production_when_unset():
    # SECURITY: Production requires explicit API keys and valid CORS origins.
    s = AppSettings(
        environment="production",
        api_access_key=None,
        api_access_keys=[],
        cors_allow_origins=["https://example.com"],
    )
    assert s.api_access_keys == []
    assert s.api_access_key is None


def test_app_settings_strips_and_dedupes_rotated_keys_preserving_first_occurrence():
    s = AppSettings(
        environment="test", api_access_key="k2", api_access_keys=[" k1 ", "k1", "k2", " k1 "]
    )
    assert s.api_access_keys == ["k1", "k2"]
    assert s.api_access_key == "k1"
