"""
Integration tests for DigestGenerator and AlertManager workflow.
"""

from unittest.mock import MagicMock

import pytest
from langchain_core.documents import Document

from notifications.alert_manager import AlertManager
from notifications.digest_generator import DigestGenerator
from utils.saved_searches import SavedSearch, UserPreferences


class TestDigestWorkflow:
    @pytest.fixture
    def mock_components(self):
        market_insights = MagicMock()
        vector_store = MagicMock()
        email_service = MagicMock()

        return {
            "market_insights": market_insights,
            "vector_store": vector_store,
            "email_service": email_service,
        }

    def test_alert_manager_process_digest(self, mock_components, tmp_path):
        """Test AlertManager.process_digest using DigestGenerator."""
        # Setup
        market_insights = mock_components["market_insights"]
        vector_store = mock_components["vector_store"]
        email_service = mock_components["email_service"]

        # Setup Generator
        generator = DigestGenerator(market_insights, vector_store)

        # Setup AlertManager
        alert_manager = AlertManager(email_service, storage_path=str(tmp_path))

        # Mock Data
        user_email = "test@example.com"
        user_prefs = UserPreferences(preferred_cities=["New York"])
        saved_searches = [SavedSearch(id="1", name="NY Search", city="New York")]

        # Mock Vector Store Results
        mock_doc = Document(
            page_content="Test Prop",
            metadata={
                "id": "p1",
                "title": "Luxury Apt",
                "city": "New York",
                "price": 1000000,
                "rooms": 3,
            },
        )
        vector_store.search.return_value = [(mock_doc, 0.95)]

        # Mock Market Insights
        mock_trend = MagicMock()
        mock_trend.direction = "increasing"
        mock_trend.percentage_change = 2.5
        mock_trend.current_average_price = 1200000
        market_insights.get_price_trend.return_value = mock_trend

        # Mock Email Service
        email_service.send_email.return_value = True

        # Execute
        result = alert_manager.process_digest(
            user_email=user_email,
            user_prefs=user_prefs,
            saved_searches=saved_searches,
            digest_generator=generator,
            digest_type="daily",
            send_email=True,
        )

        # Verify
        assert result is True

        # Verify Email Content
        email_service.send_email.assert_called_once()
        call_args = email_service.send_email.call_args[1]
        assert call_args["to_email"] == user_email
        assert "Daily Real Estate Digest" in call_args["subject"]
        assert "Luxury Apt" in call_args["body"]  # From Top Picks
        assert "New York" in call_args["body"]
