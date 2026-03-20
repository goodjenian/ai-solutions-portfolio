from fastapi.testclient import TestClient

from api.main import app
from config.settings import get_settings

client = TestClient(app)


def test_prompt_templates_list_and_apply_integration():
    settings = get_settings()
    key = settings.api_access_key

    r = client.get("/api/v1/prompt-templates", headers={"X-API-Key": key})
    assert r.status_code == 200
    templates = r.json()
    assert any(t["id"] == "buyer_followup_email_v1" for t in templates)

    r2 = client.post(
        "/api/v1/prompt-templates/apply",
        json={
            "template_id": "buyer_followup_email_v1",
            "variables": {
                "property_address": "Main St 10",
                "buyer_name": "Alex",
                "agent_name": "Maria",
            },
        },
        headers={"X-API-Key": key},
    )
    assert r2.status_code == 200
    data = r2.json()
    assert data["template_id"] == "buyer_followup_email_v1"
    assert "Subject:" in data["rendered_text"]
