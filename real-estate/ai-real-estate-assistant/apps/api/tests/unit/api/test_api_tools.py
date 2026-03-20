import os

# Set test environment before importing app
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("API_ACCESS_KEY", "dev-secret-key")

import pytest
from fastapi.testclient import TestClient
from langchain_core.documents import Document

from api.dependencies import (
    get_crm_connector,
    get_data_enrichment_service,
    get_legal_check_service,
    get_valuation_provider,
    get_vector_store,
)
from api.main import app
from api.routers import tools as tools_router
from tools.property_tools import NeighborhoodQualityResult

client = TestClient(app)


@pytest.fixture
def valid_headers():
    return {"X-API-Key": "dev-secret-key"}


def test_list_tools(valid_headers):
    response = client.get("/api/v1/tools", headers=valid_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    names = [tool["name"] for tool in data]
    assert "mortgage_calculator" in names


def test_mortgage_calculator_success(valid_headers):
    payload = {
        "property_price": 500000,
        "down_payment_percent": 20,
        "interest_rate": 5.0,
        "loan_years": 30,
    }
    response = client.post("/api/v1/tools/mortgage-calculator", json=payload, headers=valid_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["monthly_payment"] > 0
    assert data["loan_amount"] == 400000
    assert data["down_payment"] == 100000


def test_mortgage_calculator_invalid_input(valid_headers):
    payload = {
        "property_price": -100,  # Invalid
        "down_payment_percent": 20,
        "interest_rate": 5.0,
        "loan_years": 30,
    }
    response = client.post("/api/v1/tools/mortgage-calculator", json=payload, headers=valid_headers)
    assert response.status_code == 422
    # Pydantic validation error returns a detail list
    detail = response.json()["detail"]
    assert any("property_price" in str(err).lower() for err in detail)


def test_tools_unauthorized():
    response = client.get("/api/v1/tools")
    assert response.status_code == 401


class _FakeVectorStore:
    def __init__(self) -> None:
        self._docs_by_id: dict[str, Document] = {}

    def add_doc(self, doc: Document) -> None:
        doc_id = doc.metadata.get("id")
        if doc_id is None:
            raise ValueError("Document metadata must include id")
        self._docs_by_id[str(doc_id)] = doc

    def get_properties_by_ids(self, property_ids: list[str]) -> list[Document]:
        docs: list[Document] = []
        for pid in property_ids:
            if str(pid) in self._docs_by_id:
                docs.append(self._docs_by_id[str(pid)])
        return docs

    def search(self, query: str, k: int = 20):
        docs = list(self._docs_by_id.values())[:k]
        return [(d, 0.5) for d in docs]


def test_compare_properties_success(valid_headers):
    store = _FakeVectorStore()
    store.add_doc(Document(page_content="a", metadata={"id": "p1", "price": 100000, "city": "X"}))
    store.add_doc(Document(page_content="b", metadata={"id": "p2", "price": 150000, "city": "X"}))
    app.dependency_overrides[get_vector_store] = lambda: store

    response = client.post(
        "/api/v1/tools/compare-properties",
        json={"property_ids": ["p1", "p2"]},
        headers=valid_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["count"] == 2
    assert data["summary"]["min_price"] == 100000
    assert data["summary"]["max_price"] == 150000
    assert data["summary"]["price_difference"] == 50000

    app.dependency_overrides = {}


def test_tco_calculator_success(valid_headers, monkeypatch):
    """Test TCO calculator endpoint success."""

    def _mock_calculate(**kwargs):
        return {
            "monthly_payment": 2000.0,
            "total_interest": 300000.0,
            "down_payment": 100000.0,
            "loan_amount": 400000.0,
            "monthly_mortgage": 2000.0,
            "monthly_property_tax": 500.0,
            "monthly_insurance": 100.0,
            "monthly_hoa": 200.0,
            "monthly_utilities": 150.0,
            "monthly_internet": 50.0,
            "monthly_parking": 100.0,
            "monthly_maintenance": 300.0,
            "monthly_tco": 3400.0,
            "annual_mortgage": 24000.0,
            "annual_property_tax": 6000.0,
            "annual_insurance": 1200.0,
            "annual_hoa": 2400.0,
            "annual_utilities": 1800.0,
            "annual_internet": 600.0,
            "annual_parking": 1200.0,
            "annual_maintenance": 3600.0,
            "annual_tco": 40800.0,
            "total_ownership_cost": 1224000.0,
            "total_all_costs": 1324000.0,
            "breakdown": {},
        }

    monkeypatch.setattr(tools_router.TCOCalculatorTool, "calculate", staticmethod(_mock_calculate))

    payload = {
        "property_price": 500000,
        "down_payment_percent": 20,
        "interest_rate": 5.0,
        "loan_years": 30,
        "monthly_hoa": 200,
        "annual_property_tax": 6000,
        "annual_insurance": 1200,
        "monthly_utilities": 150,
        "monthly_internet": 50,
        "monthly_parking": 100,
        "maintenance_percent": 1.0,
    }

    response = client.post(
        "/api/v1/tools/tco-calculator",
        json=payload,
        headers=valid_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["monthly_tco"] == 3400.0
    assert data["annual_tco"] == 40800.0


def test_tco_calculator_invalid_input(valid_headers):
    """Test TCO calculator with invalid input."""
    payload = {
        "property_price": -500000,  # Invalid
        "down_payment_percent": 20,
        "interest_rate": 5.0,
        "loan_years": 30,
        "monthly_hoa": 200,
        "annual_property_tax": 6000,
        "annual_insurance": 1200,
        "monthly_utilities": 150,
        "monthly_internet": 50,
        "monthly_parking": 100,
        "maintenance_percent": 1.0,
    }

    response = client.post(
        "/api/v1/tools/tco-calculator",
        json=payload,
        headers=valid_headers,
    )

    assert response.status_code == 422


def test_tco_calculator_internal_error(valid_headers, monkeypatch):
    """Test TCO calculator internal error handling."""

    def _boom(**kwargs):
        raise RuntimeError("Calculation failed")

    monkeypatch.setattr(tools_router.TCOCalculatorTool, "calculate", staticmethod(_boom))

    payload = {
        "property_price": 500000,
        "down_payment_percent": 20,
        "interest_rate": 5.0,
        "loan_years": 30,
        "monthly_hoa": 200,
        "annual_property_tax": 6000,
        "annual_insurance": 1200,
        "monthly_utilities": 150,
        "monthly_internet": 50,
        "monthly_parking": 100,
        "maintenance_percent": 1.0,
    }

    response = client.post(
        "/api/v1/tools/tco-calculator",
        json=payload,
        headers=valid_headers,
    )

    assert response.status_code == 500
    assert "Calculation failed" in response.json()["detail"]


def test_investment_analysis_success(valid_headers, monkeypatch):
    """Test investment analysis endpoint success."""

    def _mock_calculate(**kwargs):
        return {
            "monthly_cash_flow": 500.0,
            "annual_cash_flow": 6000.0,
            "cash_on_cash_roi": 8.0,
            "cap_rate": 6.0,
            "gross_yield": 7.2,
            "net_yield": 1.2,
            "total_investment": 110000.0,
            "monthly_income": 3000.0,
            "monthly_expenses": 2500.0,
            "annual_income": 36000.0,
            "annual_expenses": 30000.0,
            "monthly_mortgage": 2000.0,
            "investment_score": 65.0,
            "score_breakdown": {},
        }

    monkeypatch.setattr(
        tools_router.InvestmentCalculatorTool, "calculate", staticmethod(_mock_calculate)
    )

    payload = {
        "property_price": 500000,
        "monthly_rent": 3000,
        "down_payment_percent": 20,
        "closing_costs": 10000,
        "renovation_costs": 5000,
        "interest_rate": 5.0,
        "loan_years": 30,
        "property_tax_monthly": 500,
        "insurance_monthly": 100,
        "hoa_monthly": 200,
        "maintenance_percent": 1.0,
        "vacancy_rate": 5.0,
        "management_percent": 8.0,
    }

    response = client.post(
        "/api/v1/tools/investment-analysis",
        json=payload,
        headers=valid_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["monthly_cash_flow"] == 500.0
    assert data["cap_rate"] == 6.0


def test_investment_analysis_invalid_input(valid_headers):
    """Test investment analysis with invalid input."""
    payload = {
        "property_price": 500000,
        "monthly_rent": -3000,  # Invalid
        "down_payment_percent": 20,
        "closing_costs": 10000,
        "renovation_costs": 5000,
        "interest_rate": 5.0,
        "loan_years": 30,
        "property_tax_monthly": 500,
        "insurance_monthly": 100,
        "hoa_monthly": 200,
        "maintenance_percent": 1.0,
        "vacancy_rate": 5.0,
        "management_percent": 8.0,
    }

    response = client.post(
        "/api/v1/tools/investment-analysis",
        json=payload,
        headers=valid_headers,
    )

    assert response.status_code == 422


def test_investment_analysis_internal_error(valid_headers, monkeypatch):
    """Test investment analysis internal error handling."""

    def _boom(**kwargs):
        raise RuntimeError("Analysis failed")

    monkeypatch.setattr(tools_router.InvestmentCalculatorTool, "calculate", staticmethod(_boom))

    payload = {
        "property_price": 500000,
        "monthly_rent": 3000,
        "down_payment_percent": 20,
        "closing_costs": 10000,
        "renovation_costs": 5000,
        "interest_rate": 5.0,
        "loan_years": 30,
        "property_tax_monthly": 500,
        "insurance_monthly": 100,
        "hoa_monthly": 200,
        "maintenance_percent": 1.0,
        "vacancy_rate": 5.0,
        "management_percent": 8.0,
    }

    response = client.post(
        "/api/v1/tools/investment-analysis",
        json=payload,
        headers=valid_headers,
    )

    assert response.status_code == 500
    assert "Calculation failed" in response.json()["detail"]


def test_neighborhood_quality_success(valid_headers, monkeypatch):
    """Test neighborhood quality endpoint success."""

    def _mock_calculate(**kwargs):
        return NeighborhoodQualityResult(
            property_id="prop1",
            overall_score=85.0,
            safety_score=90.0,
            schools_score=80.0,
            amenities_score=75.0,
            walkability_score=85.0,
            green_space_score=75.0,
            air_quality_score=80.0,
            noise_level_score=70.0,
            public_transport_score=75.0,
            score_breakdown={},
            factor_details=None,
            city_comparison=None,
            nearby_pois=None,
            data_sources=["mock"],
            data_freshness=None,
            latitude=52.2297,
            longitude=21.0122,
            city="Warsaw",
            neighborhood="Mokotow",
        )

    monkeypatch.setattr(
        tools_router.NeighborhoodQualityIndexTool, "calculate", staticmethod(_mock_calculate)
    )

    payload = {
        "property_id": "prop1",
        "latitude": 52.2297,
        "longitude": 21.0122,
        "city": "Warsaw",
        "neighborhood": "Mokotow",
    }

    response = client.post(
        "/api/v1/tools/neighborhood-quality",
        json=payload,
        headers=valid_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["overall_score"] == 85
    assert data["safety_score"] == 90


def test_neighborhood_quality_error(valid_headers, monkeypatch):
    """Test neighborhood quality error handling."""

    def _boom(**kwargs):
        raise ValueError("Invalid coordinates")

    monkeypatch.setattr(tools_router.NeighborhoodQualityIndexTool, "calculate", staticmethod(_boom))

    payload = {
        "property_id": "prop1",
        "latitude": 52.2297,
        "longitude": 21.0122,
        "city": "Warsaw",
        "neighborhood": "Mokotow",
    }

    response = client.post(
        "/api/v1/tools/neighborhood-quality",
        json=payload,
        headers=valid_headers,
    )

    assert response.status_code == 400
    assert "Invalid coordinates" in response.json()["detail"]


def test_compare_properties_store_unavailable(valid_headers):
    app.dependency_overrides[get_vector_store] = lambda: None

    response = client.post(
        "/api/v1/tools/compare-properties",
        json={"property_ids": ["p1"]},
        headers=valid_headers,
    )

    assert response.status_code == 503
    app.dependency_overrides = {}


def test_compare_properties_requires_at_least_one_id(valid_headers):
    app.dependency_overrides[get_vector_store] = lambda: _FakeVectorStore()

    response = client.post(
        "/api/v1/tools/compare-properties",
        json={"property_ids": ["", "   "]},
        headers=valid_headers,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "At least one property_id is required"

    app.dependency_overrides = {}


def test_compare_properties_returns_404_when_no_docs(valid_headers):
    app.dependency_overrides[get_vector_store] = lambda: _FakeVectorStore()

    response = client.post(
        "/api/v1/tools/compare-properties",
        json={"property_ids": ["missing"]},
        headers=valid_headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "No properties found for provided IDs"

    app.dependency_overrides = {}


def test_compare_properties_coerces_invalid_metadata_to_null(valid_headers):
    store = _FakeVectorStore()
    store.add_doc(
        Document(
            page_content="a",
            metadata={
                "id": "p1",
                "price": {},
                "price_per_sqm": "not-a-number",
                "rooms": {"x": 1},
                "bathrooms": None,
                "area_sqm": [],
                "year_built": {},
            },
        )
    )
    app.dependency_overrides[get_vector_store] = lambda: store

    response = client.post(
        "/api/v1/tools/compare-properties",
        json={"property_ids": ["p1"]},
        headers=valid_headers,
    )
    assert response.status_code == 200
    item = response.json()["properties"][0]
    assert item["price"] is None
    assert item["price_per_sqm"] is None
    assert item["rooms"] is None
    assert item["area_sqm"] is None
    assert item["year_built"] is None

    app.dependency_overrides = {}


def test_price_analysis_success(valid_headers):
    store = _FakeVectorStore()
    store.add_doc(
        Document(
            page_content="a",
            metadata={
                "id": "p1",
                "price": 100000,
                "price_per_sqm": 2000,
                "property_type": "Apartment",
            },
        )
    )
    store.add_doc(
        Document(
            page_content="b",
            metadata={
                "id": "p2",
                "price": 200000,
                "price_per_sqm": 2500,
                "property_type": "House",
            },
        )
    )
    store.add_doc(
        Document(
            page_content="c",
            metadata={
                "id": "p3",
                "price": 150000,
                "price_per_sqm": 2200,
                "property_type": "Apartment",
            },
        )
    )
    app.dependency_overrides[get_vector_store] = lambda: store

    response = client.post(
        "/api/v1/tools/price-analysis",
        json={"query": "apartments"},
        headers=valid_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 3
    assert data["average_price"] == 150000
    assert data["median_price"] == 150000
    assert data["min_price"] == 100000
    assert data["max_price"] == 200000
    assert data["distribution_by_type"]["Apartment"] == 2
    assert data["distribution_by_type"]["House"] == 1

    app.dependency_overrides = {}


def test_location_analysis_success(valid_headers):
    store = _FakeVectorStore()
    store.add_doc(
        Document(page_content="a", metadata={"id": "p1", "city": "X", "lat": 1.0, "lon": 2.0})
    )
    app.dependency_overrides[get_vector_store] = lambda: store

    response = client.post(
        "/api/v1/tools/location-analysis",
        json={"property_id": "p1"},
        headers=valid_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["property_id"] == "p1"
    assert data["city"] == "X"
    assert data["lat"] == 1.0
    assert data["lon"] == 2.0

    app.dependency_overrides = {}


def test_valuation_success(valid_headers):
    store = _FakeVectorStore()
    store.add_doc(
        Document(
            page_content="a",
            metadata={"id": "p1", "area_sqm": 50, "price_per_sqm": 10000},
        )
    )
    app.dependency_overrides[get_vector_store] = lambda: store
    app.dependency_overrides[get_valuation_provider] = lambda: type(
        "_Provider",
        (),
        {
            "estimate_value": staticmethod(
                lambda data: float(data["area"]) * float(data["price_per_sqm"])
            )
        },
    )()

    response = client.post(
        "/api/v1/tools/valuation",
        json={"property_id": "p1"},
        headers=valid_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["property_id"] == "p1"
    assert data["estimated_value"] == 500000.0

    app.dependency_overrides = {}


def test_mortgage_calculator_internal_error_returns_500(valid_headers, monkeypatch):
    def _boom(**_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(tools_router.MortgageCalculatorTool, "calculate", staticmethod(_boom))

    response = client.post(
        "/api/v1/tools/mortgage-calculator",
        json={
            "property_price": 500000,
            "down_payment_percent": 20,
            "interest_rate": 5.0,
            "loan_years": 30,
        },
        headers=valid_headers,
    )
    assert response.status_code == 500
    assert "Calculation failed" in response.json()["detail"]


def test_price_analysis_requires_query(valid_headers):
    app.dependency_overrides[get_vector_store] = lambda: _FakeVectorStore()

    response = client.post(
        "/api/v1/tools/price-analysis",
        json={"query": "   "},
        headers=valid_headers,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "query is required"

    app.dependency_overrides = {}


def test_price_analysis_returns_404_when_no_results(valid_headers):
    class _Store(_FakeVectorStore):
        def search(self, query: str, k: int = 20):
            return []

    app.dependency_overrides[get_vector_store] = lambda: _Store()

    response = client.post(
        "/api/v1/tools/price-analysis",
        json={"query": "x"},
        headers=valid_headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "No properties found for analysis"

    app.dependency_overrides = {}


def test_price_analysis_assigns_unknown_type_when_missing(valid_headers):
    store = _FakeVectorStore()
    store.add_doc(Document(page_content="a", metadata={"id": "p1", "price": 10}))
    app.dependency_overrides[get_vector_store] = lambda: store

    response = client.post(
        "/api/v1/tools/price-analysis",
        json={"query": "x"},
        headers=valid_headers,
    )
    assert response.status_code == 200
    assert response.json()["distribution_by_type"]["Unknown"] == 1

    app.dependency_overrides = {}


def test_location_analysis_store_unavailable(valid_headers):
    app.dependency_overrides[get_vector_store] = lambda: None

    response = client.post(
        "/api/v1/tools/location-analysis",
        json={"property_id": "p1"},
        headers=valid_headers,
    )
    assert response.status_code == 503
    assert response.json()["detail"] == "Vector store unavailable"

    app.dependency_overrides = {}


def test_location_analysis_requires_property_id(valid_headers):
    app.dependency_overrides[get_vector_store] = lambda: _FakeVectorStore()

    response = client.post(
        "/api/v1/tools/location-analysis",
        json={"property_id": "   "},
        headers=valid_headers,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "property_id is required"

    app.dependency_overrides = {}


def test_location_analysis_returns_404_when_missing(valid_headers):
    app.dependency_overrides[get_vector_store] = lambda: _FakeVectorStore()

    response = client.post(
        "/api/v1/tools/location-analysis",
        json={"property_id": "missing"},
        headers=valid_headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Property not found"

    app.dependency_overrides = {}


def test_valuation_disabled_returns_503(valid_headers):
    app.dependency_overrides[get_vector_store] = lambda: _FakeVectorStore()
    app.dependency_overrides[get_valuation_provider] = lambda: None

    response = client.post(
        "/api/v1/tools/valuation",
        json={"property_id": "p1"},
        headers=valid_headers,
    )
    assert response.status_code == 503
    assert response.json()["detail"] == "Valuation disabled"

    app.dependency_overrides = {}


def test_valuation_requires_property_id(valid_headers):
    app.dependency_overrides[get_vector_store] = lambda: _FakeVectorStore()
    app.dependency_overrides[get_valuation_provider] = lambda: type(
        "_Provider",
        (),
        {"estimate_value": staticmethod(lambda _data: 1.0)},
    )()

    response = client.post(
        "/api/v1/tools/valuation",
        json={"property_id": "   "},
        headers=valid_headers,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "property_id is required"

    app.dependency_overrides = {}


def test_valuation_returns_404_when_property_missing(valid_headers):
    app.dependency_overrides[get_vector_store] = lambda: _FakeVectorStore()
    app.dependency_overrides[get_valuation_provider] = lambda: type(
        "_Provider",
        (),
        {"estimate_value": staticmethod(lambda _data: 1.0)},
    )()

    response = client.post(
        "/api/v1/tools/valuation",
        json={"property_id": "missing"},
        headers=valid_headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Property not found"

    app.dependency_overrides = {}


def test_legal_check_success(valid_headers):
    app.dependency_overrides[get_legal_check_service] = lambda: type(
        "_Service",
        (),
        {"analyze_contract": staticmethod(lambda text: {"risks": [{"type": "x"}], "score": 0.25})},
    )()

    response = client.post(
        "/api/v1/tools/legal-check",
        json={"text": "contract"},
        headers=valid_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["score"] == 0.25
    assert isinstance(data["risks"], list)
    assert len(data["risks"]) == 1

    app.dependency_overrides = {}


def test_legal_check_disabled_returns_503(valid_headers):
    app.dependency_overrides[get_legal_check_service] = lambda: None

    response = client.post(
        "/api/v1/tools/legal-check",
        json={"text": "contract"},
        headers=valid_headers,
    )
    assert response.status_code == 503
    assert response.json()["detail"] == "Legal check disabled"

    app.dependency_overrides = {}


def test_legal_check_requires_text(valid_headers):
    app.dependency_overrides[get_legal_check_service] = lambda: type(
        "_Service",
        (),
        {"analyze_contract": staticmethod(lambda _text: {"risks": [], "score": 0.0})},
    )()

    response = client.post(
        "/api/v1/tools/legal-check",
        json={"text": "   "},
        headers=valid_headers,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "text is required"

    app.dependency_overrides = {}


def test_enrich_address_disabled_returns_503(valid_headers):
    app.dependency_overrides[get_data_enrichment_service] = lambda: None

    response = client.post(
        "/api/v1/tools/enrich-address",
        json={"address": "Some St 1"},
        headers=valid_headers,
    )
    assert response.status_code == 503
    assert response.json()["detail"] == "Data enrichment disabled"

    app.dependency_overrides = {}


def test_enrich_address_success(valid_headers):
    app.dependency_overrides[get_data_enrichment_service] = lambda: type(
        "_Service",
        (),
        {"enrich": staticmethod(lambda address: {"normalized": address.upper()})},
    )()

    response = client.post(
        "/api/v1/tools/enrich-address",
        json={"address": "Some St 1"},
        headers=valid_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["address"] == "Some St 1"
    assert data["data"]["normalized"] == "SOME ST 1"

    app.dependency_overrides = {}


def test_enrich_address_requires_address(valid_headers):
    app.dependency_overrides[get_data_enrichment_service] = lambda: type(
        "_Service",
        (),
        {"enrich": staticmethod(lambda _address: {})},
    )()

    response = client.post(
        "/api/v1/tools/enrich-address",
        json={"address": "   "},
        headers=valid_headers,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "address is required"

    app.dependency_overrides = {}


def test_crm_sync_contact_disabled_returns_503(valid_headers):
    app.dependency_overrides[get_crm_connector] = lambda: None

    response = client.post(
        "/api/v1/tools/crm-sync-contact",
        json={"name": "Jane", "phone": "123", "email": "jane@example.com"},
        headers=valid_headers,
    )
    assert response.status_code == 503
    assert response.json()["detail"] == "CRM connector not configured"

    app.dependency_overrides = {}


def test_crm_sync_contact_success(valid_headers):
    app.dependency_overrides[get_crm_connector] = lambda: type(
        "_Connector",
        (),
        {"sync_contact": staticmethod(lambda payload: "contact-123")},
    )()

    response = client.post(
        "/api/v1/tools/crm-sync-contact",
        json={"name": "Jane", "phone": "123", "email": "jane@example.com"},
        headers=valid_headers,
    )
    assert response.status_code == 200
    assert response.json()["id"] == "contact-123"

    app.dependency_overrides = {}


def test_crm_sync_contact_failed_returns_502(valid_headers):
    app.dependency_overrides[get_crm_connector] = lambda: type(
        "_Connector",
        (),
        {"sync_contact": staticmethod(lambda payload: "")},
    )()

    response = client.post(
        "/api/v1/tools/crm-sync-contact",
        json={"name": "Jane"},
        headers=valid_headers,
    )
    assert response.status_code == 502
    assert response.json()["detail"] == "CRM sync failed"

    app.dependency_overrides = {}


# TASK-021: Commute Time Analysis API Tests


def test_commute_time_success(valid_headers):
    """Test commute time calculation endpoint."""
    store = _FakeVectorStore()
    store.add_doc(
        Document(
            page_content="Test Property",
            metadata={
                "id": "prop1",
                "city": "Warsaw",
                "lat": 52.2297,
                "lon": 21.0122,
            },
        )
    )
    app.dependency_overrides[get_vector_store] = lambda: store

    response = client.post(
        "/api/v1/tools/commute-time",
        json={
            "property_id": "prop1",
            "destination_lat": 52.2040,
            "destination_lon": 21.0120,
            "mode": "transit",
            "destination_name": "Warsaw Central",
        },
        headers=valid_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    result = data["result"]
    assert result["property_id"] == "prop1"
    assert "destination_name" in result
    assert "duration_seconds" in result
    assert "distance_meters" in result
    assert "mode" in result

    app.dependency_overrides = {}


def test_commute_time_requires_property_id(valid_headers):
    """Test commute time endpoint requires property_id."""
    app.dependency_overrides[get_vector_store] = lambda: _FakeVectorStore()

    response = client.post(
        "/api/v1/tools/commute-time",
        json={
            "property_id": "   ",
            "destination_lat": 52.2040,
            "destination_lon": 21.0120,
            "mode": "transit",
        },
        headers=valid_headers,
    )

    assert response.status_code == 400

    app.dependency_overrides = {}


def test_commute_time_property_not_found(valid_headers):
    """Test commute time endpoint when property not found."""
    app.dependency_overrides[get_vector_store] = lambda: _FakeVectorStore()

    response = client.post(
        "/api/v1/tools/commute-time",
        json={
            "property_id": "missing_prop",
            "destination_lat": 52.2040,
            "destination_lon": 21.0120,
            "mode": "transit",
        },
        headers=valid_headers,
    )

    assert response.status_code == 404

    app.dependency_overrides = {}


def test_commute_ranking_success(valid_headers):
    """Test commute ranking endpoint."""
    store = _FakeVectorStore()
    store.add_doc(
        Document(
            page_content="Property 1",
            metadata={
                "id": "prop1",
                "title": "Property 1",
                "city": "Warsaw",
                "lat": 52.2297,
                "lon": 21.0122,
            },
        )
    )
    store.add_doc(
        Document(
            page_content="Property 2",
            metadata={
                "id": "prop2",
                "title": "Property 2",
                "city": "Warsaw",
                "lat": 52.2040,
                "lon": 21.0120,
            },
        )
    )
    app.dependency_overrides[get_vector_store] = lambda: store

    response = client.post(
        "/api/v1/tools/commute-ranking",
        json={
            "property_ids": "prop1,prop2",
            "destination_lat": 52.2350,
            "destination_lon": 21.0100,
            "mode": "driving",
            "destination_name": "Warsaw Central Station",
        },
        headers=valid_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "rankings" in data
    assert "destination_name" in data
    assert "mode" in data
    assert len(data["rankings"]) == 2

    app.dependency_overrides = {}


def test_commute_ranking_empty_property_list(valid_headers):
    """Test commute ranking with empty property list."""
    app.dependency_overrides[get_vector_store] = lambda: _FakeVectorStore()

    response = client.post(
        "/api/v1/tools/commute-ranking",
        json={
            "property_ids": "",
            "destination_lat": 52.2350,
            "destination_lon": 21.0100,
            "mode": "transit",
        },
        headers=valid_headers,
    )

    # Pydantic validation returns 422 for empty property_ids
    assert response.status_code == 422

    app.dependency_overrides = {}


def test_commute_ranking_all_properties_not_found(valid_headers):
    """Test commute ranking when no properties are found."""
    app.dependency_overrides[get_vector_store] = lambda: _FakeVectorStore()

    response = client.post(
        "/api/v1/tools/commute-ranking",
        json={
            "property_ids": "missing1,missing2",
            "destination_lat": 52.2350,
            "destination_lon": 21.0100,
            "mode": "transit",
        },
        headers=valid_headers,
    )

    assert response.status_code == 404

    app.dependency_overrides = {}


def test_commute_ranking_store_unavailable(valid_headers):
    """Test commute ranking when vector store is unavailable."""
    app.dependency_overrides[get_vector_store] = lambda: None

    response = client.post(
        "/api/v1/tools/commute-ranking",
        json={
            "property_ids": "prop1",
            "destination_lat": 52.2350,
            "destination_lon": 21.0100,
            "mode": "transit",
        },
        headers=valid_headers,
    )

    assert response.status_code == 503

    app.dependency_overrides = {}


def test_commute_time_property_no_coordinates(valid_headers):
    """Test commute time when property has no coordinates."""
    store = _FakeVectorStore()
    store.add_doc(
        Document(
            page_content="Test Property",
            metadata={
                "id": "prop1",
                "city": "Warsaw",
                # Missing lat/lon
            },
        )
    )
    app.dependency_overrides[get_vector_store] = lambda: store

    response = client.post(
        "/api/v1/tools/commute-time",
        json={
            "property_id": "prop1",
            "destination_lat": 52.2040,
            "destination_lon": 21.0120,
            "mode": "transit",
        },
        headers=valid_headers,
    )

    assert response.status_code == 400

    app.dependency_overrides = {}


def test_commute_time_with_departure_time(valid_headers):
    """Test commute time with departure time."""
    store = _FakeVectorStore()
    store.add_doc(
        Document(
            page_content="Test Property",
            metadata={
                "id": "prop1",
                "city": "Warsaw",
                "lat": 52.2297,
                "lon": 21.0122,
            },
        )
    )
    app.dependency_overrides[get_vector_store] = lambda: store

    response = client.post(
        "/api/v1/tools/commute-time",
        json={
            "property_id": "prop1",
            "destination_lat": 52.2040,
            "destination_lon": 21.0120,
            "mode": "transit",
            "departure_time": "2024-01-15T08:30:00",
        },
        headers=valid_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "result" in data

    app.dependency_overrides = {}


def test_commute_time_invalid_departure_time(valid_headers):
    """Test commute time with invalid departure time format."""
    store = _FakeVectorStore()
    store.add_doc(
        Document(
            page_content="Test Property",
            metadata={
                "id": "prop1",
                "city": "Warsaw",
                "lat": 52.2297,
                "lon": 21.0122,
            },
        )
    )
    app.dependency_overrides[get_vector_store] = lambda: store

    response = client.post(
        "/api/v1/tools/commute-time",
        json={
            "property_id": "prop1",
            "destination_lat": 52.2040,
            "destination_lon": 21.0120,
            "mode": "transit",
            "departure_time": "invalid-time",
        },
        headers=valid_headers,
    )

    assert response.status_code == 400

    app.dependency_overrides = {}


def test_commute_ranking_no_valid_coordinates(valid_headers):
    """Test commute ranking when no properties have valid coordinates."""
    store = _FakeVectorStore()
    store.add_doc(
        Document(
            page_content="Test Property",
            metadata={
                "id": "prop1",
                "city": "Warsaw",
                # Missing lat/lon
            },
        )
    )
    app.dependency_overrides[get_vector_store] = lambda: store

    response = client.post(
        "/api/v1/tools/commute-ranking",
        json={
            "property_ids": "prop1",
            "destination_lat": 52.2350,
            "destination_lon": 21.0100,
            "mode": "transit",
        },
        headers=valid_headers,
    )

    assert response.status_code == 400

    app.dependency_overrides = {}
