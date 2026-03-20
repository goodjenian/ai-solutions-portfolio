"""
Unit tests for DigestGenerator.
"""

import unittest
from unittest.mock import MagicMock

from langchain_core.documents import Document

from notifications.digest_generator import DigestGenerator
from utils.saved_searches import SavedSearch, UserPreferences


class TestDigestGenerator(unittest.TestCase):
    def setUp(self):
        self.mock_market_insights = MagicMock()
        self.mock_vector_store = MagicMock()
        self.generator = DigestGenerator(
            market_insights=self.mock_market_insights, vector_store=self.mock_vector_store
        )

    def test_generate_digest_basic(self):
        """Test basic digest generation with mock data."""
        # Setup mocks
        user_prefs = UserPreferences(preferred_cities=["London"])
        saved_searches = [SavedSearch(id="1", name="London Flats", city="London", min_rooms=2)]

        # Mock vector store results
        mock_doc = Document(
            page_content="Nice flat",
            metadata={
                "id": "prop1",
                "title": "Nice Flat",
                "city": "London",
                "price": 500000,
                "rooms": 2,
            },
        )
        self.mock_vector_store.search.return_value = [(mock_doc, 0.9)]

        # Mock market insights
        mock_trend = MagicMock()
        mock_trend.direction = "increasing"
        mock_trend.change_percent = 5.2
        mock_trend.average_price = 550000
        self.mock_market_insights.get_price_trend.return_value = mock_trend

        # Execute
        result = self.generator.generate_digest(user_prefs, saved_searches)

        # Verify
        self.assertEqual(result["new_properties"], 1)
        self.assertEqual(result["trending_cities"][0]["name"], "London")
        self.assertEqual(result["trending_cities"][0]["change"], "5.2%")

        # Check expert data presence
        self.assertIsNotNone(result.get("expert"))
        self.assertEqual(len(result["expert"]["market_table"]), 1)
        self.assertEqual(result["expert"]["market_table"][0]["City"], "London")

        # Verify vector store call
        self.mock_vector_store.search.assert_called_once()
        args, kwargs = self.mock_vector_store.search.call_args
        self.assertIn("query", kwargs)
        self.assertIn("filter", kwargs)

    def test_generate_digest_no_results(self):
        """Test digest generation with no matching properties."""
        user_prefs = UserPreferences()
        saved_searches = [SavedSearch(id="1", name="Empty Search")]

        self.mock_vector_store.search.return_value = []
        self.mock_market_insights.get_price_trend.side_effect = Exception("No data")

        result = self.generator.generate_digest(user_prefs, saved_searches)

        self.assertEqual(result["new_properties"], 0)
        self.assertEqual(len(result["top_picks"]), 0)
        # Expert data might be None or empty depending on logic,
        # but if get_price_trend fails, trending_cities should be empty
        self.assertEqual(len(result["trending_cities"]), 0)

    def test_build_filters(self):
        """Test filter construction from saved search."""
        search = SavedSearch(id="1", name="Test", city="Paris", min_price=1000, max_price=2000)

        filters = self.generator._build_filters(search)

        self.assertIn("$and", filters)
        conditions = filters["$and"]
        self.assertTrue(any(c.get("city") == {"$eq": "Paris"} for c in conditions))
        self.assertTrue(any(c.get("price") == {"$gte": 1000.0} for c in conditions))


if __name__ == "__main__":
    unittest.main()
