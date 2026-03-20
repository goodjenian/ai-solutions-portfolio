import os
from unittest.mock import patch

from config.settings import update_api_key


@patch("models.provider_factory.ModelProviderFactory.clear_cache")
def test_update_api_key_sets_env_and_clears_cache(mock_clear_cache, monkeypatch):
    cases = [
        ("openai", "OPENAI_API_KEY"),
        ("anthropic", "ANTHROPIC_API_KEY"),
        ("google", "GOOGLE_API_KEY"),
        ("grok", "XAI_API_KEY"),
        ("deepseek", "DEEPSEEK_API_KEY"),
    ]
    for provider, env_key in cases:
        monkeypatch.delenv(env_key, raising=False)
        update_api_key(provider, f"{provider}-key")
        assert os.environ[env_key] == f"{provider}-key"

    assert mock_clear_cache.call_count == len(cases)
