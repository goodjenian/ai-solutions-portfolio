"""
Unit tests for APIProvider and MockRealEstateAPIProvider.
"""

from unittest.mock import Mock, patch

import pandas as pd
import pytest
import requests

from data.providers.api_provider import APIProvider, MockRealEstateAPIProvider
from data.schemas import Property


class TestAPIProvider:
    @pytest.fixture
    def api_provider(self):
        return APIProvider(api_url="https://api.example.com", api_key="test-key")

    def test_init(self, api_provider):
        assert api_provider.source == "https://api.example.com"
        assert api_provider.api_key == "test-key"
        assert api_provider.headers == {"Authorization": "Bearer test-key"}

    @patch("requests.get")
    def test_validate_source_success(self, mock_get, api_provider):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        assert api_provider.validate_source() is True
        mock_get.assert_called_once_with(
            "https://api.example.com", headers={"Authorization": "Bearer test-key"}, timeout=10
        )

    @patch("requests.get")
    def test_validate_source_failure(self, mock_get, api_provider):
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")
        assert api_provider.validate_source() is False

    @patch("requests.get")
    def test_load_data_success(self, mock_get, api_provider):
        mock_response = Mock()
        mock_response.json.return_value = [
            {"title": "Test Prop", "city": "Test City", "price": 1000}
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        df = api_provider.load_data()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert df.iloc[0]["title"] == "Test Prop"

    @patch("requests.get")
    def test_load_data_failure(self, mock_get, api_provider):
        mock_get.side_effect = Exception("API Error")
        df = api_provider.load_data()
        assert df.empty

    @patch("requests.get")
    def test_get_properties(self, mock_get, api_provider):
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "title": "Luxury Apt",
                "city": "New York",
                "price": 5000,
                "property_type": "apartment",
                "listing_type": "rent",
            }
        ]
        mock_get.return_value = mock_response

        properties = api_provider.get_properties()
        assert len(properties) == 1
        assert isinstance(properties[0], Property)
        assert properties[0].title == "Luxury Apt"
        assert properties[0].city == "New York"
        assert properties[0].price == 5000.0


class TestMockRealEstateAPIProvider:
    @pytest.fixture
    def mock_provider(self):
        return MockRealEstateAPIProvider()

    def test_validate_source(self, mock_provider):
        assert mock_provider.validate_source() is True

    def test_load_data(self, mock_provider):
        df = mock_provider.load_data()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "Modern Apartment in Warsaw" in df["title"].values

    def test_get_properties(self, mock_provider):
        properties = mock_provider.get_properties()
        assert len(properties) == 2
        assert isinstance(properties[0], Property)
        assert properties[0].city == "Warsaw"
        assert properties[1].city == "Krakow"
