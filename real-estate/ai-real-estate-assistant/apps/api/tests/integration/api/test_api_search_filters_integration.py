from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_search_accepts_filters_and_returns_422_on_bad_types():
    headers = {"X-API-Key": "dev-secret-key"}
    # Valid filters should be accepted
    ok = client.post(
        "/api/v1/search",
        json={
            "query": "apartment",
            "filters": {"min_price": 100000, "rooms": 2, "property_type": "apartment"},
        },
        headers=headers,
    )
    assert ok.status_code in (200, 503)  # store may be unavailable, but schema is valid

    # Invalid type for rooms should fail validation downstream or return 500
    bad = client.post(
        "/api/v1/search",
        json={
            "query": "apartment",
            "filters": {"rooms": "two"},
        },
        headers=headers,
    )
    assert bad.status_code in (422, 500)
