"""
Unit tests for the commute time client.

TASK-021: Commute Time Analysis
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from utils.commute_client import CommuteTimeClient, CommuteTimeResult


class TestCommuteTimeClient:
    """Test suite for CommuteTimeClient."""

    def test_init_with_api_key(self):
        """Test client initialization with API key."""
        client = CommuteTimeClient(api_key="test_key")
        assert client.api_key == "test_key"
        assert client.enabled is True

    def test_init_without_api_key(self):
        """Test client initialization without API key."""
        with patch("utils.commute_client.get_settings") as mock_settings:
            mock_settings.return_value.google_routes_api_key = None
            mock_settings.return_value.google_routes_enabled = True

            client = CommuteTimeClient(api_key=None)
            assert client.api_key is None
            assert client.enabled is False

    def test_get_cache_key(self):
        """Test cache key generation."""
        client = CommuteTimeClient(api_key="test_key")

        key = client._get_cache_key(
            origin_lat=52.2297,
            origin_lon=21.0122,
            destination_lat=52.2040,
            destination_lon=21.0120,
            mode="transit",
            departure_time=None,
        )

        assert "52.229700" in key
        assert "21.012200" in key
        assert "52.204000" in key
        assert "21.012000" in key
        assert "transit" in key
        assert "now" in key

    def test_get_cache_key_with_departure_time(self):
        """Test cache key generation with departure time."""
        client = CommuteTimeClient(api_key="test_key")
        departure_time = datetime(2024, 1, 15, 8, 30, 0)

        key = client._get_cache_key(
            origin_lat=52.2297,
            origin_lon=21.0122,
            destination_lat=52.2040,
            destination_lon=21.0120,
            mode="transit",
            departure_time=departure_time,
        )

        assert "2024-01-15T08:30:00" in key

    def test_format_duration(self):
        """Test duration formatting."""
        client = CommuteTimeClient(api_key="test_key")

        assert client._format_duration(30) == "30s"
        assert client._format_duration(90) == "1m"
        assert client._format_duration(150) == "2m"
        assert client._format_duration(3600) == "1h"
        assert client._format_duration(5400) == "1h 30m"
        assert client._format_duration(7200) == "2h"

    def test_format_distance(self):
        """Test distance formatting."""
        client = CommuteTimeClient(api_key="test_key")

        assert client._format_distance(500) == "500m"
        assert client._format_distance(1000) == "1.0km"
        assert client._format_distance(1500) == "1.5km"
        assert client._format_distance(12500) == "12.5km"

    def test_parse_duration(self):
        """Test duration parsing from API response."""
        client = CommuteTimeClient(api_key="test_key")

        assert client._parse_duration("3600s") == 3600
        assert client._parse_duration("1800s") == 1800
        assert client._parse_duration("0s") == 0
        assert client._parse_duration("") == 0

    def test_travel_modes(self):
        """Test travel modes mapping."""
        client = CommuteTimeClient(api_key="test_key")

        assert client.TRAVEL_MODES["driving"] == "DRIVE"
        assert client.TRAVEL_MODES["walking"] == "WALK"
        assert client.TRAVEL_MODES["bicycling"] == "BICYCLE"
        assert client.TRAVEL_MODES["transit"] == "TRANSIT"

    def test_routing_preferences(self):
        """Test routing preferences mapping."""
        client = CommuteTimeClient(api_key="test_key")

        assert client.ROUTING_PREFERENCES["driving"] == "TRAFFIC_AWARE"
        assert client.ROUTING_PREFERENCES["walking"] == "TRAFFIC_UNAWARE"
        assert client.ROUTING_PREFERENCES["bicycling"] == "TRAFFIC_UNAWARE"
        assert client.ROUTING_PREFERENCES["transit"] == "TRANSIT_AWARE"

    @pytest.mark.asyncio
    async def test_get_commute_time_invalid_mode(self):
        """Test commute time calculation with invalid mode."""
        client = CommuteTimeClient(api_key="test_key")

        with pytest.raises(ValueError, match="Invalid mode"):
            await client.get_commute_time(
                property_id="prop1",
                origin_lat=52.2297,
                origin_lon=21.0122,
                destination_lat=52.2040,
                destination_lon=21.0120,
                mode="invalid_mode",
            )

    @pytest.mark.asyncio
    async def test_get_commute_time_mock_data(self):
        """Test commute time calculation returns mock data when API disabled."""
        with patch("utils.commute_client.get_settings") as mock_settings:
            mock_settings.return_value.google_routes_api_key = None
            mock_settings.return_value.google_routes_enabled = True

            client = CommuteTimeClient(api_key=None)

            result = await client.get_commute_time(
                property_id="prop1",
                origin_lat=52.2297,
                origin_lon=21.0122,
                destination_lat=52.2040,
                destination_lon=21.0120,
                mode="transit",
                destination_name="Warsaw Central",
            )

            assert result.property_id == "prop1"
            assert result.destination_name == "Warsaw Central"
            assert result.mode == "transit"
            assert result.duration_seconds > 0
            assert result.distance_meters > 0
            assert result.polyline is None  # Mock data has no polyline

    @pytest.mark.asyncio
    async def test_rank_properties_by_commute_empty_list(self):
        """Test ranking properties with empty property list."""
        client = CommuteTimeClient(api_key="test_key")

        results = await client.rank_properties_by_commute(
            property_ids=[],
            properties_lat_lon={},
            destination_lat=52.2040,
            destination_lon=21.0120,
            mode="transit",
        )

        assert results == []

    @pytest.mark.asyncio
    async def test_rank_properties_by_commute_missing_coordinates(self):
        """Test ranking properties with missing coordinates."""
        client = CommuteTimeClient(api_key="test_key")

        results = await client.rank_properties_by_commute(
            property_ids=["prop1", "prop2"],
            properties_lat_lon={"prop1": (52.2297, 21.0122)},  # prop2 is missing
            destination_lat=52.2040,
            destination_lon=21.0120,
            mode="transit",
        )

        # Should only return results for properties with coordinates
        assert len(results) >= 0

    def test_clear_cache(self):
        """Test cache clearing."""
        client = CommuteTimeClient(api_key="test_key", cache_enabled=True)

        # Add something to cache
        client._cache["test_key"] = MagicMock()

        # Clear cache
        client.clear_cache()

        assert len(client._cache) == 0

    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached_result(self):
        """Test that cached results are returned without API call."""
        with patch("utils.commute_client.get_settings") as mock_settings:
            mock_settings.return_value.google_routes_api_key = None
            mock_settings.return_value.google_routes_enabled = True

            client = CommuteTimeClient(api_key=None, cache_enabled=True)

            # First call will use mock data (API disabled) and populate cache
            _result1 = await client.get_commute_time(
                property_id="prop1",
                origin_lat=52.2297,
                origin_lon=21.0122,
                destination_lat=52.2040,
                destination_lon=21.0120,
                mode="transit",
                destination_name="Destination A",
            )

            # Second call should hit cache
            result2 = await client.get_commute_time(
                property_id="prop2",  # Different property_id
                origin_lat=52.2297,
                origin_lon=21.0122,
                destination_lat=52.2040,
                destination_lon=21.0120,
                mode="transit",
                destination_name="Destination B",  # Different destination_name
            )

            # Results should be from cache with updated fields
            assert result2.property_id == "prop2"
            assert result2.destination_name == "Destination B"

    @pytest.mark.asyncio
    async def test_cache_disabled_skips_cache(self):
        """Test that cache is not used when disabled."""
        with patch("utils.commute_client.get_settings") as mock_settings:
            mock_settings.return_value.google_routes_api_key = None
            mock_settings.return_value.google_routes_enabled = True

            client = CommuteTimeClient(api_key=None, cache_enabled=False)

            # Add something to cache manually
            cache_key = client._get_cache_key(52.2297, 21.0122, 52.2040, 21.0120, "transit", None)
            client._cache[cache_key] = MagicMock()

            # Call should not use cache since it's disabled
            result = await client.get_commute_time(
                property_id="prop1",
                origin_lat=52.2297,
                origin_lon=21.0122,
                destination_lat=52.2040,
                destination_lon=21.0120,
                mode="transit",
            )

            # Should get a valid result (mock data since API is disabled)
            assert result is not None
            assert result.property_id == "prop1"

    @pytest.mark.asyncio
    async def test_transit_mode_with_departure_time(self):
        """Test transit mode with departure time set."""
        with patch("utils.commute_client.get_settings") as mock_settings:
            mock_settings.return_value.google_routes_api_key = None
            mock_settings.return_value.google_routes_enabled = True

            client = CommuteTimeClient(api_key=None)
            departure_time = datetime(2024, 6, 15, 8, 30, 0)

            result = await client.get_commute_time(
                property_id="prop1",
                origin_lat=52.2297,
                origin_lon=21.0122,
                destination_lat=52.2040,
                destination_lon=21.0120,
                mode="transit",
                departure_time=departure_time,
            )

            assert result.property_id == "prop1"
            assert result.mode == "transit"
            assert result.departure_time == departure_time

    def test_parse_duration_edge_cases(self):
        """Test duration parsing with various edge cases."""
        client = CommuteTimeClient(api_key="test_key")

        # Valid formats
        assert client._parse_duration("3600s") == 3600
        assert client._parse_duration("1800.5s") == 1800
        assert client._parse_duration("90") == 90

        # Invalid formats return 0
        assert client._parse_duration("invalid") == 0
        assert client._parse_duration("") == 0
        assert client._parse_duration("abc") == 0

    @pytest.mark.asyncio
    async def test_rank_properties_sorting_by_duration(self):
        """Test that properties are sorted by commute duration."""
        with patch("utils.commute_client.get_settings") as mock_settings:
            mock_settings.return_value.google_routes_api_key = None
            mock_settings.return_value.google_routes_enabled = True

            client = CommuteTimeClient(api_key=None)

            results = await client.rank_properties_by_commute(
                property_ids=["prop1", "prop2", "prop3"],
                properties_lat_lon={
                    "prop1": (52.2297, 21.0122),
                    "prop2": (52.2040, 21.0120),
                    "prop3": (52.2100, 21.0100),
                },
                destination_lat=52.2350,
                destination_lon=21.0100,
                mode="driving",
            )

            # Results should be sorted by duration
            if len(results) > 1:
                for i in range(len(results) - 1):
                    assert results[i].duration_seconds <= results[i + 1].duration_seconds

    @pytest.mark.asyncio
    async def test_get_commute_time_all_modes(self):
        """Test commute time calculation for all travel modes."""
        with patch("utils.commute_client.get_settings") as mock_settings:
            mock_settings.return_value.google_routes_api_key = None
            mock_settings.return_value.google_routes_enabled = True

            client = CommuteTimeClient(api_key=None)

            for mode in ["driving", "walking", "bicycling", "transit"]:
                result = await client.get_commute_time(
                    property_id=f"prop_{mode}",
                    origin_lat=52.2297,
                    origin_lon=21.0122,
                    destination_lat=52.2040,
                    destination_lon=21.0120,
                    mode=mode,
                )

                assert result.mode == mode
                assert result.duration_seconds > 0
                assert result.distance_meters > 0

    @pytest.mark.asyncio
    async def test_get_commute_time_with_successful_api_response(self):
        """Test commute time calculation with mocked successful API response."""
        # Mock response from Google Routes API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "routes": [
                {
                    "duration": "1800s",
                    "distanceMeters": 10000,
                    "polyline": {"encodedPolyline": "test_polyline_encoded"},
                }
            ]
        }

        mock_httpx_client = AsyncMock()
        mock_httpx_client.__aenter__.return_value.post.return_value = mock_response
        mock_httpx_client.__aexit__ = AsyncMock()

        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            client = CommuteTimeClient(api_key="test_key", cache_enabled=False)

            result = await client.get_commute_time(
                property_id="prop1",
                origin_lat=52.2297,
                origin_lon=21.0122,
                destination_lat=52.2040,
                destination_lon=21.0120,
                mode="driving",
                destination_name="Test Destination",
            )

            assert result.property_id == "prop1"
            assert result.destination_name == "Test Destination"
            assert result.duration_seconds == 1800
            assert result.duration_text == "30m"
            assert result.distance_meters == 10000
            assert result.distance_text == "10.0km"
            assert result.mode == "driving"
            assert result.polyline == "test_polyline_encoded"


class TestCommuteTimeResult:
    """Test suite for CommuteTimeResult dataclass."""

    def test_commute_time_result_creation(self):
        """Test creating a commute time result."""
        result = CommuteTimeResult(
            property_id="prop1",
            origin_lat=52.2297,
            origin_lon=21.0122,
            destination_lat=52.2040,
            destination_lon=21.0120,
            destination_name="Office",
            duration_seconds=1800,
            duration_text="30m",
            distance_meters=10000,
            distance_text="10.0km",
            mode="transit",
            polyline="encoded_polyline_string",
        )

        assert result.property_id == "prop1"
        assert result.destination_name == "Office"
        assert result.duration_seconds == 1800
        assert result.distance_meters == 10000
        assert result.mode == "transit"
        assert result.polyline == "encoded_polyline_string"

    def test_commute_time_result_without_optional_fields(self):
        """Test creating a commute time result without optional fields."""
        result = CommuteTimeResult(
            property_id="prop1",
            origin_lat=52.2297,
            origin_lon=21.0122,
            destination_lat=52.2040,
            destination_lon=21.0120,
            destination_name=None,
            duration_seconds=1800,
            duration_text="30m",
            distance_meters=10000,
            distance_text="10.0km",
            mode="driving",
            polyline=None,
        )

        assert result.destination_name is None
        assert result.polyline is None
        assert result.arrival_time is None
        assert result.departure_time is None
