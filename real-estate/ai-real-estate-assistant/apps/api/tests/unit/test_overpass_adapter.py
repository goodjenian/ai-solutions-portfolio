"""
Tests for the Overpass API adapter.

This module tests the Overpass adapter for fetching property data
from OpenStreetMap.
"""

from unittest.mock import Mock, patch

import pytest
import requests

from data.adapters.base import PortalFilter
from data.adapters.overpass_adapter import OverpassAdapter


class TestOverpassAdapter:
    """Tests for OverpassAdapter class."""

    @pytest.fixture
    def adapter(self):
        """Create an OverpassAdapter instance."""
        return OverpassAdapter()

    @pytest.fixture
    def sample_filters(self):
        """Create sample PortalFilter for testing."""
        return PortalFilter(
            city="Warsaw",
            listing_type="rent",
            limit=10,
        )

    @pytest.fixture
    def sample_overpass_response(self):
        """Sample Overpass API response."""
        return {
            "elements": [
                {
                    "type": "way",
                    "id": 12345,
                    "center": {"lat": 52.2297, "lon": 21.0122},
                    "tags": {
                        "building": "apartments",
                        "name": "Test Building",
                        "addr:city": "Warsaw",
                        "addr:street": "Marszałkowska",
                        "addr:housenumber": "100",
                    },
                },
                {
                    "type": "way",
                    "id": 12346,
                    "center": {"lat": 52.2298, "lon": 21.0123},
                    "tags": {
                        "building": "house",
                        "addr:city": "Warsaw",
                        "addr:street": "Nowy Świat",
                        "addr:housenumber": "50",
                    },
                },
            ]
        }

    def test_adapter_name(self, adapter):
        """Verify adapter has correct name."""
        assert adapter.name == "overpass"
        assert adapter.display_name == "OpenStreetMap (Overpass)"

    def test_adapter_no_api_key_required(self, adapter):
        """Verify adapter does not require API key."""
        assert adapter.requires_api_key is False

    def test_fetch_requires_city(self, adapter):
        """Verify fetch requires city filter."""
        filters = PortalFilter(city=None)
        result = adapter.fetch(filters)

        assert result.success is False
        assert "City filter is required" in str(result.errors)

    def test_fetch_success(self, adapter, sample_filters, sample_overpass_response):
        """Verify successful fetch returns properties."""
        with patch.object(adapter, "_api_url", "https://test-api.com"):
            with patch("requests.get") as mock_get:
                mock_response = Mock()
                mock_response.json.return_value = sample_overpass_response
                mock_response.raise_for_status = Mock()
                mock_get.return_value = mock_response

                result = adapter.fetch(sample_filters)

        assert result.success is True
        assert result.count == 2
        assert len(result.properties) == 2
        assert result.source == "overpass"
        assert result.source_type == "portal"

    def test_fetch_handles_api_error(self, adapter, sample_filters):
        """Verify fetch handles API errors gracefully."""
        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.ConnectionError("Network error")

            result = adapter.fetch(sample_filters)

        assert result.success is False
        assert len(result.errors) > 0

    def test_fetch_handles_timeout(self, adapter, sample_filters):
        """Verify fetch handles timeout errors."""
        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.Timeout("Request timed out")

            result = adapter.fetch(sample_filters)

        assert result.success is False
        assert len(result.errors) > 0

    def test_build_overpass_query(self, adapter, sample_filters):
        """Verify Overpass QL query is built correctly."""
        query = adapter._build_overpass_query(sample_filters)

        assert "[out:json]" in query
        assert "Warsaw" in query
        assert "building" in query

    def test_parse_osm_response(self, adapter, sample_filters, sample_overpass_response):
        """Verify OSM response parsing extracts properties."""
        properties = adapter._parse_osm_response(sample_overpass_response, sample_filters)

        assert len(properties) == 2

        # Check first property
        prop = properties[0]
        assert prop["city"] == "Warsaw"
        assert prop["source_platform"] == "overpass"
        assert "latitude" in prop
        assert "longitude" in prop

    def test_normalize_property_type_apartment(self, adapter):
        """Verify apartment building type normalization."""
        result = adapter._normalize_property_type("apartments", None)
        assert result == "apartment"

        result = adapter._normalize_property_type("residential", None)
        assert result == "apartment"

    def test_normalize_property_type_house(self, adapter):
        """Verify house building type normalization."""
        result = adapter._normalize_property_type("house", None)
        assert result == "house"

        result = adapter._normalize_property_type("detached", None)
        assert result == "house"

    def test_extract_address(self, adapter):
        """Verify address extraction from OSM tags."""
        tags = {
            "addr:city": "Warsaw",
            "addr:street": "Marszałkowska",
            "addr:housenumber": "100",
            "addr:postcode": "00-001",
        }

        addr = adapter._extract_address(tags)

        assert addr["city"] == "Warsaw"
        assert addr["street"] == "Marszałkowska"
        assert addr["housenumber"] == "100"
        assert addr["postcode"] == "00-001"
        assert "Marszałkowska 100" in addr["full"]

    def test_estimate_price_warsaw(self, adapter):
        """Verify price estimation for Warsaw."""
        tags = {"addr:city": "Warsaw", "building": "apartments"}
        filters = PortalFilter(city="Warsaw")

        price = adapter._estimate_price(tags, filters)

        # Warsaw base is 2500, with random variation
        assert 2000 <= price <= 3000

    def test_estimate_price_house_premium(self, adapter):
        """Verify house price has premium over apartment."""
        tags = {"addr:city": "Warsaw", "building": "house"}
        filters = PortalFilter(city="Warsaw")

        price = adapter._estimate_price(tags, filters)

        # House should have 1.5x premium
        assert 3000 <= price <= 4500

    def test_estimate_rooms_apartment(self, adapter):
        """Verify room estimation for apartments."""
        rooms = adapter._estimate_rooms("apartments")
        assert rooms == 2.0

    def test_estimate_rooms_house(self, adapter):
        """Verify room estimation for houses."""
        rooms = adapter._estimate_rooms("house")
        assert rooms == 4.0

    def test_build_osm_url_way(self, adapter):
        """Verify OSM URL generation for way element."""
        url = adapter._build_osm_url("12345", "way")
        assert url == "https://www.openstreetmap.org/way/12345"

    def test_build_osm_url_relation(self, adapter):
        """Verify OSM URL generation for relation element."""
        url = adapter._build_osm_url("67890", "relation")
        assert url == "https://www.openstreetmap.org/relation/67890"

    def test_get_status(self, adapter):
        """Verify adapter status returns correct info."""
        status = adapter.get_status()

        assert status["name"] == "overpass"
        assert status["configured"] is True
        assert status["has_api_key"] is False
        assert "rate_limit" in status


class TestOverpassAdapterRateLimit:
    """Tests for rate limiting behavior."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with rate limit config."""
        return OverpassAdapter()

    def test_rate_limit_configuration(self, adapter):
        """Verify rate limit is configured."""
        assert adapter.rate_limit_requests == 10
        assert adapter.rate_limit_window == 60

    def test_handles_429_response(self):
        """Verify HTTP 429 (rate limit) is handled."""
        adapter = OverpassAdapter()
        filters = PortalFilter(city="Warsaw")

        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.raise_for_status.side_effect = requests.HTTPError(response=mock_response)
            mock_get.return_value = mock_response

            result = adapter.fetch(filters)

        assert result.success is False
        assert len(result.errors) > 0
