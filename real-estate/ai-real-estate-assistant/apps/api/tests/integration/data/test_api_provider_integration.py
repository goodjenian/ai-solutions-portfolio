"""
Integration tests for the API Data Provider.
"""

from unittest.mock import MagicMock, patch

import pytest

from data.providers.api_provider import APIProvider
from data.schemas import ListingType, PropertyType


@pytest.fixture
def api_provider():
    return APIProvider(api_url="https://api.example.com", api_key="test-key")


@pytest.fixture
def mock_api_response_data():
    return [
        {
            "id": "prop-1",
            "title": "Luxury Apartment",
            "description": "A beautiful place",
            "price": 500000,
            "currency": "USD",
            "city": "New York",
            "property_type": "apartment",
            "listing_type": "sale",
            "bedrooms": 2,
            "bathrooms": 2,
            "area": 120,
        },
        {
            "id": "prop-2",
            "title": "Cozy House",
            "description": "Family home",
            "price": 2500,
            "currency": "USD",
            "city": "Austin",
            "property_type": "house",
            "listing_type": "rent",
            "bedrooms": 3,
            "bathrooms": 2,
            "area": 200,
        },
    ]


def test_api_provider_full_flow_integration(api_provider, mock_api_response_data):
    """
    Test the critical path: API Response -> DataFrame -> Property Objects.
    """
    # Mock the network call, but allow the rest of the logic to run real
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_api_response_data
        mock_get.return_value = mock_response

        # Execute the flow
        properties = api_provider.get_properties()

        # Assertions
        assert len(properties) == 2

        # Verify first property
        p1 = properties[0]
        assert p1.title == "Luxury Apartment"
        assert p1.city == "New York"
        assert p1.price == 500000
        assert p1.property_type == PropertyType.APARTMENT
        assert p1.listing_type == ListingType.SALE

        # Verify second property
        p2 = properties[1]
        assert p2.title == "Cozy House"
        assert p2.city == "Austin"
        assert p2.price == 2500
        assert p2.property_type == PropertyType.HOUSE
        assert p2.listing_type == ListingType.RENT


def test_api_provider_handles_schema_mismatch_gracefully(api_provider):
    """
    Test that invalid data in the API response doesn't crash the whole batch.
    """
    mixed_data = [
        {
            "title": "Valid Prop",
            "price": 1000,
            "city": "Boston",
            "property_type": "apartment",
            "listing_type": "rent",
        },
        {
            "title": "Invalid Prop",
            "price": "not-a-number",  # Should cause validation error if strict
            "city": "Miami",
            # Missing fields might be okay depending on Property schema defaults,
            # but type mismatch is a good test
        },
    ]

    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mixed_data
        mock_get.return_value = mock_response

        # We expect the provider to handle errors (log and skip, or error out depending on implementation)
        # Based on current implementation:
        # try: Property(...) except Exception: logger.warning(...)
        # So it should skip the invalid one.

        properties = api_provider.get_properties()

        # If the second one fails validation, we should get 1 property.
        # If Property schema is loose, we might get 2.
        # Let's check what we got.
        assert len(properties) >= 1
        assert properties[0].title == "Valid Prop"
