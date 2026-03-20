from models.providers.ollama import OllamaProvider


def test_ollama_provider_uses_ollama_base_url_env_var(monkeypatch):
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://example.local:11434")
    monkeypatch.delenv("OLLAMA_API_BASE", raising=False)
    provider = OllamaProvider()
    assert provider.config.get("base_url") == "http://example.local:11434"


def test_ollama_provider_uses_ollama_api_base_when_base_url_missing(monkeypatch):
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    monkeypatch.setenv("OLLAMA_API_BASE", "http://example.api.base:11434")
    provider = OllamaProvider()
    assert provider.config.get("base_url") == "http://example.api.base:11434"
