import json
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from data.providers.json_provider import JSONDataProvider
from data.schemas import Property


class TestJSONDataProvider:
    @pytest.fixture
    def valid_json_data(self):
        return [
            {
                "id": "1",
                "title": "Modern Apartment",
                "city": "Warsaw",
                "price": 5000,
                "rooms": 3,
                "area_sqm": 75,
                "property_type": "apartment",
                "listing_type": "rent",
            },
            {
                "id": "2",
                "title": "Cozy Studio",
                "city": "Krakow",
                "price": 2500,
                "rooms": 1,
                "area_sqm": 30,
                "property_type": "studio",
                "listing_type": "rent",
            },
        ]

    def test_validate_source_local_file(self, tmp_path):
        f = tmp_path / "test.json"
        f.touch()
        provider = JSONDataProvider(f)
        assert provider.validate_source() is True

        provider_invalid = JSONDataProvider(tmp_path / "nonexistent.json")
        assert provider_invalid.validate_source() is False

    @patch("requests.head")
    def test_validate_source_url(self, mock_head):
        mock_head.return_value.status_code = 200
        provider = JSONDataProvider("http://example.com/data.json")
        assert provider.validate_source() is True

        mock_head.return_value.status_code = 404
        assert provider.validate_source() is False

    def test_load_data_local(self, tmp_path, valid_json_data):
        f = tmp_path / "data.json"
        with open(f, "w") as file:
            json.dump(valid_json_data, file)

        provider = JSONDataProvider(f)
        df = provider.load_data()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert df.iloc[0]["city"] == "Warsaw"

    @patch("requests.get")
    def test_load_data_url(self, mock_get, valid_json_data):
        mock_get.return_value.json.return_value = valid_json_data
        mock_get.return_value.raise_for_status = MagicMock()

        provider = JSONDataProvider("http://example.com/data.json")
        df = provider.load_data()

        assert len(df) == 2
        assert df.iloc[1]["city"] == "Krakow"

    @patch("requests.get")
    def test_load_data_github_url(self, mock_get, valid_json_data):
        """Test that GitHub blob URLs are converted to raw."""
        mock_get.return_value.json.return_value = valid_json_data
        mock_get.return_value.raise_for_status = MagicMock()

        url = "https://github.com/user/repo/blob/main/data.json"
        expected_url = "https://raw.githubusercontent.com/user/repo/main/data.json"

        provider = JSONDataProvider(url)
        df = provider.load_data()

        # Check if requests.get was called with converted URL
        mock_get.assert_called_with(expected_url, timeout=10)
        assert len(df) == 2

    def test_load_data_nested_properties(self, tmp_path, valid_json_data):
        # Test wrapping in "properties" key
        nested = {"properties": valid_json_data}
        f = tmp_path / "nested.json"
        with open(f, "w") as file:
            json.dump(nested, file)

        provider = JSONDataProvider(f)
        df = provider.load_data()
        assert len(df) == 2

    def test_get_properties(self, tmp_path, valid_json_data):
        f = tmp_path / "props.json"
        with open(f, "w") as file:
            json.dump(valid_json_data, file)

        provider = JSONDataProvider(f)
        props = provider.get_properties()

        assert len(props) == 2
        assert isinstance(props[0], Property)
        assert props[0].city == "Warsaw"
        assert props[0].price == 5000

    def test_get_properties_skips_invalid(self, tmp_path):
        data = [
            {"city": "Warsaw", "price": 1000},  # Valid (minimal)
            {"city": "Krakow", "price": "invalid_price"},  # Invalid type
            {"missing_city": True},  # Missing required field
        ]
        f = tmp_path / "mixed.json"
        with open(f, "w") as file:
            json.dump(data, file)

        provider = JSONDataProvider(f)
        props = provider.get_properties()

        # Should parse the valid one, skip others
        # Actually Property schema requires 'city', 'price' is optional but here it's provided.
        # "price": "invalid_price" -> Pydantic might fail float conversion.

        assert len(props) == 1
        assert props[0].city == "Warsaw"
