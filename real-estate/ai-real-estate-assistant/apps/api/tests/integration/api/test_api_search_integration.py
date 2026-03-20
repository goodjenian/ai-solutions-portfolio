from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_search_endpoint_auth_enforcement():
    """Verify that search endpoint requires authentication (Integration)."""
    # No headers
    response = client.post("/api/v1/search", json={"query": "test"})
    assert response.status_code in [401, 403]

    # Invalid key
    response = client.post(
        "/api/v1/search", json={"query": "test"}, headers={"X-API-Key": "wrong-key"}
    )
    assert response.status_code == 403


def test_search_endpoint_validation_error(monkeypatch):
    """Verify input validation works."""
    # Authenticated but invalid body (missing query)
    # We need a valid key to bypass auth
    headers = {"X-API-Key": "dev-secret-key"}

    response = client.post(
        "/api/v1/search",
        json={"limit": 10},  # missing query
        headers=headers,
    )
    assert response.status_code == 422
