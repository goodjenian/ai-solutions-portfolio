from unittest.mock import patch

import pandas as pd
import pytest

from data.providers.csv_provider import CSVDataProvider
from data.schemas import Property, PropertyType


class TestCSVDataProvider:
    @pytest.fixture
    def mock_loader_class(self):
        with patch("data.providers.csv_provider.DataLoaderCsv") as MockClass:
            yield MockClass

    @pytest.fixture
    def mock_loader_instance(self, mock_loader_class):
        return mock_loader_class.return_value

    def test_init(self, mock_loader_class):
        """Test initialization of CSVDataProvider."""
        source = "test.csv"
        provider = CSVDataProvider(source)

        assert provider.source == source
        mock_loader_class.assert_called_once_with(source)

    def test_validate_source_valid(self, mock_loader_instance):
        """Test validate_source returns True when source is valid."""
        # Setup mock to have a valid csv_path (not None)
        mock_loader_instance.csv_path = "valid/path/test.csv"

        provider = CSVDataProvider("test.csv")
        assert provider.validate_source() is True

    def test_validate_source_invalid(self, mock_loader_instance):
        """Test validate_source returns False when source is invalid."""
        # Setup mock to have None as csv_path (simulating invalid source)
        mock_loader_instance.csv_path = None

        provider = CSVDataProvider("invalid.csv")
        assert provider.validate_source() is False

    def test_load_data(self, mock_loader_instance):
        """Test load_data delegates to loader and caches result."""
        # Setup mocks
        mock_df_raw = pd.DataFrame({"a": [1]})
        mock_df_formatted = pd.DataFrame({"a": [1], "formatted": [True]})

        mock_loader_instance.load_df.return_value = mock_df_raw
        mock_loader_instance.format_df.return_value = mock_df_formatted

        provider = CSVDataProvider("test.csv")

        # First call should hit the loader
        result1 = provider.load_data()
        assert result1.equals(mock_df_formatted)
        mock_loader_instance.load_df.assert_called_once()
        mock_loader_instance.format_df.assert_called_once_with(mock_df_raw)

        # Second call should return cached data
        result2 = provider.load_data()
        assert result2.equals(mock_df_formatted)
        # Call counts should remain the same
        assert mock_loader_instance.load_df.call_count == 1

    def test_get_properties(self, mock_loader_instance):
        """Test conversion of DataFrame rows to Property objects."""
        # Setup mock data that matches Property schema
        data = {
            "city": ["Warsaw", "Krakow"],
            "price": [3000.0, 2500.0],
            "rooms": [2.0, 1.0],
            "area_sqm": [50.0, 30.0],
            "property_type": ["apartment", "studio"],
            "listing_type": ["rent", "rent"],
            "image_urls": ["http://img1.com,http://img2.com", "http://img3.com"],
        }
        mock_df = pd.DataFrame(data)

        # We need load_data to return this mock_df
        # Since load_data calls format_df, we mock format_df to return our ready-to-go DF
        mock_loader_instance.format_df.return_value = mock_df

        provider = CSVDataProvider("test.csv")
        properties = provider.get_properties()

        assert len(properties) == 2
        assert isinstance(properties[0], Property)
        assert properties[0].city == "Warsaw"
        assert properties[0].price == 3000.0
        assert properties[0].image_urls == ["http://img1.com", "http://img2.com"]

        assert properties[1].city == "Krakow"
        assert properties[1].property_type == PropertyType.STUDIO
        assert properties[1].image_urls == ["http://img3.com"]

    def test_get_properties_skips_invalid(self, mock_loader_instance):
        """Test that get_properties skips rows that fail validation."""
        # Second row is missing required 'city' field
        data = {
            "city": ["Warsaw", None],
            "price": [3000.0, 2500.0],
            "rooms": [2.0, 1.0],
            "area_sqm": [50.0, 30.0],
        }
        mock_df = pd.DataFrame(data)
        mock_loader_instance.format_df.return_value = mock_df

        provider = CSVDataProvider("test.csv")
        properties = provider.get_properties()

        assert len(properties) == 1
        assert properties[0].city == "Warsaw"
