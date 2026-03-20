"""
Integration tests for commute time analysis.

TASK-021: Commute Time Analysis
"""

from unittest.mock import MagicMock

import pytest
from langchain_core.documents import Document


class TestCommuteTimeTools:
    """Test suite for commute time tools integration."""

    @pytest.fixture
    def mock_vector_store(self):
        """Create a mock vector store with test properties."""
        store = MagicMock()

        def get_by_ids(ids):
            docs = []
            for pid in ids:
                if pid == "warsaw_property_1":
                    docs.append(
                        Document(
                            page_content="Modern apartment in Warsaw",
                            metadata={
                                "id": "warsaw_property_1",
                                "title": "Modern Apartment Warsaw Center",
                                "price": 450000,
                                "city": "Warsaw",
                                "lat": 52.2297,
                                "lon": 21.0122,
                            },
                        )
                    )
                elif pid == "warsaw_property_2":
                    docs.append(
                        Document(
                            page_content="Spacious house in suburbs",
                            metadata={
                                "id": "warsaw_property_2",
                                "title": "Spacious House with Garden",
                                "price": 650000,
                                "city": "Warsaw",
                                "lat": 52.2040,
                                "lon": 21.0120,
                            },
                        )
                    )
            return docs

        store.get_properties_by_ids.side_effect = get_by_ids
        return store

    def test_commute_time_tool_run_missing_coords(self, mock_vector_store):
        """Test commute time tool with property missing coordinates."""
        from tools.property_tools import CommuteTimeAnalysisTool

        tool = CommuteTimeAnalysisTool(vector_store=mock_vector_store)

        # Mock store returns property without coordinates
        mock_vector_store.get_properties_by_ids.return_value = [
            Document(
                page_content="Test",
                metadata={"id": "no_coords_prop", "title": "No Coords Property"},
            )
        ]

        result = tool._run(
            property_id="no_coords_prop",
            destination_lat=52.2040,
            destination_lon=21.0120,
            mode="transit",
        )

        # The tool returns "Property not found" when coords are missing
        assert "Error" in result or "not found" in result.lower()

    def test_commute_ranking_tool_run_success(self, mock_vector_store):
        """Test commute ranking tool with valid properties."""
        from tools.property_tools import CommuteRankingTool

        tool = CommuteRankingTool(vector_store=mock_vector_store)

        result = tool._run(
            property_ids="warsaw_property_1,warsaw_property_2",
            destination_lat=52.2350,
            destination_lon=21.0100,
            mode="driving",
            destination_name="Warsaw Central Station",
        )

        # Should return ranking output
        assert "Commute Ranking" in result
        assert "Warsaw Central Station" in result
        assert "Mode:" in result

    def test_commute_ranking_tool_empty_property_list(self, mock_vector_store):
        """Test commute ranking tool with empty property list."""
        from tools.property_tools import CommuteRankingTool

        tool = CommuteRankingTool(vector_store=mock_vector_store)

        result = tool._run(
            property_ids="",
            destination_lat=52.2350,
            destination_lon=21.0100,
            mode="transit",
        )

        assert "Error" in result
