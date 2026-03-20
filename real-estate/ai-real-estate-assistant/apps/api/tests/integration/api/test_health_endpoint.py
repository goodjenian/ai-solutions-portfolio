def test_health_endpoint_returns_healthy():
    TestClient = __import__("fastapi.testclient", fromlist=["TestClient"]).TestClient
    app = __import__("api.main", fromlist=["app"]).app

    with TestClient(app) as client:
        resp = client.get("/health?include_dependencies=false")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("status") == "healthy"
        assert "version" in data
