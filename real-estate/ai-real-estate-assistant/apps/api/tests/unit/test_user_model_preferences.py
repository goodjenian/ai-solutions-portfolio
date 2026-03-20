import json

import pytest

from models.user_model_preferences import UserModelPreferences, UserModelPreferencesManager


def test_user_model_preferences_manager_raises_on_empty_email(tmp_path):
    manager = UserModelPreferencesManager(storage_path=str(tmp_path))
    with pytest.raises(ValueError, match="Missing user email"):
        manager.get_preferences("  ")


def test_user_model_preferences_manager_handles_corrupt_file(tmp_path, caplog):
    corrupt_file = tmp_path / "model_preferences.json"
    corrupt_file.write_text("{invalid json content")

    manager = UserModelPreferencesManager(storage_path=str(tmp_path))
    prefs = manager.get_preferences("u1@example.com")
    assert prefs.user_email == "u1@example.com"


def test_user_model_preferences_manager_handles_non_dict_data(tmp_path):
    corrupt_file = tmp_path / "model_preferences.json"
    corrupt_file.write_text("not a dict")

    manager = UserModelPreferencesManager(storage_path=str(tmp_path))
    prefs = manager.get_preferences("u1@example.com")
    assert prefs.user_email == "u1@example.com"


def test_user_model_preferences_manager_skips_invalid_user_data(tmp_path):
    prefs_file = tmp_path / "model_preferences.json"
    prefs_file.write_text(
        json.dumps(
            {
                "u1@example.com": {"preferred_provider": "openai"},
                "u2@example.com": "not a dict",
                "u3@example.com": {"preferred_model": "gpt-4o"},
            }
        )
    )

    manager = UserModelPreferencesManager(storage_path=str(tmp_path))
    prefs1 = manager.get_preferences("u1@example.com")
    assert prefs1.preferred_provider == "openai"

    prefs3 = manager.get_preferences("u3@example.com")
    assert prefs3.preferred_model == "gpt-4o"


def test_user_model_preferences_manager_persists_and_loads(tmp_path):
    manager = UserModelPreferencesManager(storage_path=str(tmp_path))
    prefs = manager.get_preferences("u1@example.com")
    assert prefs.user_email == "u1@example.com"
    assert prefs.preferred_provider is None
    assert prefs.preferred_model is None

    updated = manager.update_preferences(
        "u1@example.com",
        preferred_provider=" openai ",
        preferred_model=" gpt-4o ",
    )
    assert updated.preferred_provider == "openai"
    assert updated.preferred_model == "gpt-4o"

    reloaded = UserModelPreferencesManager(storage_path=str(tmp_path))
    prefs2 = reloaded.get_preferences("u1@example.com")
    assert prefs2.preferred_provider == "openai"
    assert prefs2.preferred_model == "gpt-4o"


def test_user_model_preferences_from_dict_handles_invalid_updated_at():
    prefs = UserModelPreferences.from_dict(
        {
            "user_email": "u2@example.com",
            "preferred_provider": "ollama",
            "preferred_model": "llama3.3:8b",
            "updated_at": "not-a-date",
        }
    )
    assert prefs.user_email == "u2@example.com"
    assert prefs.preferred_provider == "ollama"
    assert prefs.preferred_model == "llama3.3:8b"


def test_user_model_preferences_manager_clears_fields_with_empty_strings(tmp_path):
    manager = UserModelPreferencesManager(storage_path=str(tmp_path))
    manager.update_preferences(
        "u3@example.com", preferred_provider="openai", preferred_model="gpt-4o"
    )
    manager.update_preferences("u3@example.com", preferred_provider="  ", preferred_model=" ")
    prefs = manager.get_preferences("u3@example.com")
    assert prefs.preferred_provider is None
    assert prefs.preferred_model is None
