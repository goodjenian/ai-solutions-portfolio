from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from api.main import app
from config.settings import get_settings

client = TestClient(app)


@patch("api.routers.settings.ModelProviderFactory")
def test_settings_test_runtime_integration_returns_payload(mock_factory):
    settings = get_settings()
    key = settings.api_access_key

    mock_factory.list_providers.return_value = ["ollama"]

    provider = MagicMock()
    provider.is_local = True
    provider.validate_connection.return_value = (True, None)
    provider.list_available_models.return_value = ["llama3.3:8b"]
    mock_factory.get_provider.return_value = provider

    r = client.get("/api/v1/settings/test-runtime?provider=ollama", headers={"X-API-Key": key})
    assert r.status_code == 200
    assert r.json() == {
        "provider": "ollama",
        "is_local": True,
        "runtime_available": True,
        "available_models": ["llama3.3:8b"],
        "runtime_error": None,
    }


@patch("api.routers.settings.ModelProviderFactory")
def test_settings_test_runtime_integration_rejects_non_local_provider(mock_factory):
    settings = get_settings()
    key = settings.api_access_key

    mock_factory.list_providers.return_value = ["openai"]

    provider = MagicMock()
    provider.is_local = False
    mock_factory.get_provider.return_value = provider

    r = client.get("/api/v1/settings/test-runtime?provider=openai", headers={"X-API-Key": key})
    assert r.status_code == 400
    assert "not a local runtime provider" in r.json()["detail"]
