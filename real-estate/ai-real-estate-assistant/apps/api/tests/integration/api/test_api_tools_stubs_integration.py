from fastapi.testclient import TestClient
from langchain_core.documents import Document

from api.dependencies import get_crm_connector, get_vector_store
from api.main import app
from config.settings import get_settings

client = TestClient(app)


class _Store:
    def get_properties_by_ids(self, property_ids):
        docs = []
        for pid in property_ids:
            docs.append(
                Document(
                    page_content="x",
                    metadata={"id": pid, "area_sqm": 50, "price_per_sqm": 10000},
                )
            )
        return docs


def test_valuation_is_gated_by_mode():
    settings = get_settings()
    key = settings.api_access_key

    old_mode = settings.valuation_mode
    app.dependency_overrides[get_vector_store] = lambda: _Store()
    try:
        settings.valuation_mode = "pro"
        r_disabled = client.post(
            "/api/v1/tools/valuation",
            json={"property_id": "p1"},
            headers={"X-API-Key": key},
        )
        assert r_disabled.status_code == 503
        assert r_disabled.json()["detail"] == "Valuation disabled"

        settings.valuation_mode = "simple"
        r_enabled = client.post(
            "/api/v1/tools/valuation",
            json={"property_id": "p1"},
            headers={"X-API-Key": key},
        )
        assert r_enabled.status_code == 200
        assert r_enabled.json()["estimated_value"] == 500000.0
    finally:
        settings.valuation_mode = old_mode
        app.dependency_overrides = {}


def test_legal_check_is_gated_by_mode():
    settings = get_settings()
    key = settings.api_access_key

    old_mode = settings.legal_check_mode
    try:
        settings.legal_check_mode = "pro"
        r_disabled = client.post(
            "/api/v1/tools/legal-check",
            json={"text": "contract"},
            headers={"X-API-Key": key},
        )
        assert r_disabled.status_code == 503
        assert r_disabled.json()["detail"] == "Legal check disabled"

        settings.legal_check_mode = "basic"
        r_enabled = client.post(
            "/api/v1/tools/legal-check",
            json={"text": "contract"},
            headers={"X-API-Key": key},
        )
        assert r_enabled.status_code == 200
        data = r_enabled.json()
        assert data["score"] == 0.0
        assert data["risks"] == []
    finally:
        settings.legal_check_mode = old_mode


def test_data_enrichment_is_gated_by_flag():
    settings = get_settings()
    key = settings.api_access_key

    old_flag = settings.data_enrichment_enabled
    try:
        settings.data_enrichment_enabled = False
        r_disabled = client.post(
            "/api/v1/tools/enrich-address",
            json={"address": "Some St 1"},
            headers={"X-API-Key": key},
        )
        assert r_disabled.status_code == 503
        assert r_disabled.json()["detail"] == "Data enrichment disabled"

        settings.data_enrichment_enabled = True
        r_enabled = client.post(
            "/api/v1/tools/enrich-address",
            json={"address": "Some St 1"},
            headers={"X-API-Key": key},
        )
        assert r_enabled.status_code == 200
        assert r_enabled.json()["data"] == {}
    finally:
        settings.data_enrichment_enabled = old_flag


def test_crm_sync_is_gated_by_webhook_url():
    settings = get_settings()
    key = settings.api_access_key

    old_url = settings.crm_webhook_url
    try:
        settings.crm_webhook_url = None
        r_disabled = client.post(
            "/api/v1/tools/crm-sync-contact",
            json={"name": "Jane"},
            headers={"X-API-Key": key},
        )
        assert r_disabled.status_code == 503
        assert r_disabled.json()["detail"] == "CRM connector not configured"

        settings.crm_webhook_url = "http://example.invalid"
        app.dependency_overrides[get_crm_connector] = lambda: type(
            "_Connector",
            (),
            {"sync_contact": staticmethod(lambda payload: "contact-xyz")},
        )()
        r_enabled = client.post(
            "/api/v1/tools/crm-sync-contact",
            json={"name": "Jane"},
            headers={"X-API-Key": key},
        )
        assert r_enabled.status_code == 200
        assert r_enabled.json()["id"] == "contact-xyz"
    finally:
        settings.crm_webhook_url = old_url
        app.dependency_overrides = {}
