import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


@pytest.fixture
def valid_headers():
    return {"X-API-Key": "dev-secret-key"}


def test_list_prompt_templates_requires_auth():
    r = client.get("/api/v1/prompt-templates")
    assert r.status_code == 401


def test_list_prompt_templates_happy_path(valid_headers):
    r = client.get("/api/v1/prompt-templates", headers=valid_headers)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert any(item["id"] == "listing_description_v1" for item in data)
    first = data[0]
    assert "variables" in first
    assert isinstance(first["variables"], list)


def test_apply_prompt_template_happy_path(valid_headers):
    r = client.post(
        "/api/v1/prompt-templates/apply",
        json={
            "template_id": "buyer_followup_email_v1",
            "variables": {
                "property_address": "Main St 10",
                "buyer_name": "Alex",
                "agent_name": "Maria",
            },
        },
        headers=valid_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["template_id"] == "buyer_followup_email_v1"
    assert "Main St 10" in data["rendered_text"]


def test_apply_prompt_template_missing_required_returns_400(valid_headers):
    r = client.post(
        "/api/v1/prompt-templates/apply",
        json={
            "template_id": "buyer_followup_email_v1",
            "variables": {
                "buyer_name": "Alex",
            },
        },
        headers=valid_headers,
    )
    assert r.status_code == 400
    assert "Missing required variables" in r.json()["detail"]


def test_apply_prompt_template_unknown_template_returns_404(valid_headers):
    r = client.post(
        "/api/v1/prompt-templates/apply",
        json={"template_id": "does_not_exist", "variables": {}},
        headers=valid_headers,
    )
    assert r.status_code == 404
