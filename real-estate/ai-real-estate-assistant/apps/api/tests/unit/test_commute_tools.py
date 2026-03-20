"""
Unit tests for commute time property tools.

TASK-021: Commute Time Analysis
"""

from unittest.mock import MagicMock

import pytest
from langchain_core.documents import Document

from tools.property_tools import (
    CommuteRankingTool,
    CommuteTimeAnalysisTool,
)


class TestCommuteTimeAnalysisTool:
    """Test suite for CommuteTimeAnalysisTool."""

    @pytest.fixture
    def mock_vector_store(self):
        """Create a mock vector store."""
        store = MagicMock()

        def get_by_ids(ids):
            if not ids:
                return []
            # Return a property with coordinates
            return [
                Document(
                    page_content="Test Property",
                    metadata={
                        "id": ids[0] if ids else "test_prop",
                        "title": "Test Property",
                        "price": 500000,
                        "city": "Warsaw",
                        "lat": 52.2297,
                        "lon": 21.0122,
                    },
                )
            ]

        store.get_properties_by_ids.side_effect = get_by_ids
        return store

    def test_tool_initialization(self, mock_vector_store):
        """Test tool initialization."""
        tool = CommuteTimeAnalysisTool(vector_store=mock_vector_store)
        assert tool.name == "commute_time_analyzer"
        assert "commute" in tool.description.lower()
        assert "time" in tool.description.lower()

    def test_run_with_valid_inputs(self, mock_vector_store):
        """Test _run method with valid inputs."""
        tool = CommuteTimeAnalysisTool(vector_store=mock_vector_store)

        result = tool._run(
            property_id="test_prop",
            destination_lat=52.2040,
            destination_lon=21.0120,
            mode="transit",
            destination_name="Warsaw Central",
        )

        assert "Commute Analysis" in result
        assert "test_prop" in result
        assert "Warsaw Central" in result
        assert "Transit" in result  # Capitalized mode in output

    def test_run_with_missing_property(self, mock_vector_store):
        """Test _run method with missing property."""
        tool = CommuteTimeAnalysisTool(vector_store=mock_vector_store)

        # Mock to return empty list (property not found)
        mock_vector_store.get_properties_by_ids.return_value = []

        result = tool._run(
            property_id="missing_prop",
            destination_lat=52.2040,
            destination_lon=21.0120,
            mode="driving",
        )

        # Tool returns result with property_id even when not found in store
        # (uses mock data since API is disabled)
        assert "missing_prop" in result
        assert "Commute Analysis" in result

    def test_run_with_property_missing_coordinates(self, mock_vector_store):
        """Test _run with property that has no coordinates."""
        tool = CommuteTimeAnalysisTool(vector_store=mock_vector_store)

        # Mock to return property without coordinates
        mock_vector_store.get_properties_by_ids.return_value = [
            Document(
                page_content="Test",
                metadata={
                    "id": "no_coords_prop",
                    "title": "No Coords Property",
                },
            )
        ]

        result = tool._run(
            property_id="no_coords_prop",
            destination_lat=52.2040,
            destination_lon=21.0120,
            mode="transit",
        )

        # Tool still returns result (mock data uses destination as origin)
        assert result is not None
        assert len(result) > 0

    def test_run_all_travel_modes(self, mock_vector_store):
        """Test _run with all travel modes."""
        tool = CommuteTimeAnalysisTool(vector_store=mock_vector_store)

        for mode in ["driving", "walking", "bicycling", "transit"]:
            result = tool._run(
                property_id=f"prop_{mode}",
                destination_lat=52.2040,
                destination_lon=21.0120,
                mode=mode,
            )

            assert "Commute Analysis" in result

    def test_run_with_invalid_mode(self, mock_vector_store):
        """Test _run with invalid travel mode."""
        tool = CommuteTimeAnalysisTool(vector_store=mock_vector_store)

        # This should still work, but may use a default mode
        result = tool._run(
            property_id="test_prop",
            destination_lat=52.2040,
            destination_lon=21.0120,
            mode="invalid_mode",
        )

        # Tool should return some result even with invalid mode
        assert result is not None
        assert len(result) > 0


class TestCommuteRankingTool:
    """Test suite for CommuteRankingTool."""

    @pytest.fixture
    def mock_vector_store(self):
        """Create a mock vector store."""
        store = MagicMock()

        def get_by_ids(ids):
            if not ids:
                return []
            docs = []
            for pid in ids:
                if pid == "prop1":
                    docs.append(
                        Document(
                            page_content="Property 1",
                            metadata={
                                "id": "prop1",
                                "title": "Property 1",
                                "price": 450000,
                                "city": "Warsaw",
                                "lat": 52.2297,
                                "lon": 21.0122,
                            },
                        )
                    )
                elif pid == "prop2":
                    docs.append(
                        Document(
                            page_content="Property 2",
                            metadata={
                                "id": "prop2",
                                "title": "Property 2",
                                "price": 550000,
                                "city": "Warsaw",
                                "lat": 52.2040,
                                "lon": 21.0120,
                            },
                        )
                    )
                elif pid == "prop3":
                    docs.append(
                        Document(
                            page_content="Property 3",
                            metadata={
                                "id": "prop3",
                                "title": "Property 3",
                                "price": 650000,
                                "city": "Warsaw",
                                "lat": 52.2100,
                                "lon": 21.0100,
                            },
                        )
                    )
            return docs

        store.get_properties_by_ids.side_effect = get_by_ids
        return store

    def test_tool_initialization(self, mock_vector_store):
        """Test tool initialization."""
        tool = CommuteRankingTool(vector_store=mock_vector_store)
        assert tool.name == "commute_ranking"
        assert "commute" in tool.description.lower()
        assert "rank" in tool.description.lower()

    def test_run_with_valid_properties(self, mock_vector_store):
        """Test _run method with valid properties."""
        tool = CommuteRankingTool(vector_store=mock_vector_store)

        result = tool._run(
            property_ids="prop1,prop2,prop3",
            destination_lat=52.2350,
            destination_lon=21.0100,
            mode="driving",
            destination_name="Warsaw Central Station",
        )

        assert "Commute Ranking" in result
        assert "Warsaw Central Station" in result
        assert "Mode:" in result
        assert "Driving" in result  # Capitalized mode in output

    def test_run_with_empty_property_list(self, mock_vector_store):
        """Test _run with empty property list."""
        tool = CommuteRankingTool(vector_store=mock_vector_store)

        result = tool._run(
            property_ids="",
            destination_lat=52.2350,
            destination_lon=21.0100,
            mode="transit",
        )

        assert "Error" in result

    def test_run_with_single_property(self, mock_vector_store):
        """Test _run with a single property."""
        tool = CommuteRankingTool(vector_store=mock_vector_store)

        result = tool._run(
            property_ids="prop1",
            destination_lat=52.2350,
            destination_lon=21.0100,
            mode="walking",
        )

        assert "Commute Ranking" in result
        assert "Property 1" in result  # Title is shown, not ID
        assert "Walking" in result  # Capitalized mode

    def test_run_with_missing_properties(self, mock_vector_store):
        """Test _run when some properties are not found."""
        tool = CommuteRankingTool(vector_store=mock_vector_store)

        result = tool._run(
            property_ids="prop1,missing_prop,prop2",
            destination_lat=52.2350,
            destination_lon=21.0100,
            mode="bicycling",
        )

        # Should still return results for found properties
        assert "Commute Ranking" in result
        assert "Bicycling" in result  # Capitalized mode

    def test_run_all_travel_modes(self, mock_vector_store):
        """Test _run with all travel modes."""
        tool = CommuteRankingTool(vector_store=mock_vector_store)

        for mode in ["driving", "walking", "bicycling", "transit"]:
            result = tool._run(
                property_ids="prop1,prop2",
                destination_lat=52.2350,
                destination_lon=21.0100,
                mode=mode,
            )

            assert "Commute Ranking" in result

    def test_run_without_destination_name(self, mock_vector_store):
        """Test _run without providing destination name."""
        tool = CommuteRankingTool(vector_store=mock_vector_store)

        result = tool._run(
            property_ids="prop1,prop2",
            destination_lat=52.2350,
            destination_lon=21.0100,
            mode="transit",
        )

        assert "Commute Ranking" in result
        # Should use coordinates as destination identifier
        assert "52.2350" in result or "21.01" in result

    def test_run_with_invalid_destination(self, mock_vector_store):
        """Test _run with invalid destination coordinates."""
        tool = CommuteRankingTool(vector_store=mock_vector_store)

        result = tool._run(
            property_ids="prop1",
            destination_lat=999,  # Invalid latitude
            destination_lon=999,  # Invalid longitude
            mode="driving",
        )

        # Tool should still return some result
        assert result is not None
        assert len(result) > 0
