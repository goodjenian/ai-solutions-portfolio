from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_search_accepts_sorting_parameters():
    headers = {"X-API-Key": "dev-secret-key"}
    resp = client.post(
        "/api/v1/search",
        json={
            "query": "apartment",
            "sort_by": "price",
            "sort_order": "asc",
        },
        headers=headers,
    )
    assert resp.status_code in (200, 503)
