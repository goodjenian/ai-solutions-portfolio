"""
Tests for Lead Tracking Service.

Task #58: Comprehensive Test Suite Update
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from services.lead_tracking import (
    SESSION_TIMEOUT_MINUTES,
    VISITOR_COOKIE_MAX_AGE_DAYS,
    VISITOR_COOKIE_NAME,
    LeadTrackingService,
)


class TestLeadTrackingServiceConstants:
    """Tests for module constants."""

    def test_visitor_cookie_name(self):
        """Verify visitor cookie name."""
        assert VISITOR_COOKIE_NAME == "visitor_id"

    def test_visitor_cookie_max_age(self):
        """Verify cookie max age is 365 days."""
        assert VISITOR_COOKIE_MAX_AGE_DAYS == 365

    def test_session_timeout(self):
        """Verify session timeout is 30 minutes."""
        assert SESSION_TIMEOUT_MINUTES == 30


class TestLeadTrackingService:
    """Tests for LeadTrackingService."""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = MagicMock(spec=AsyncSession)
        session.flush = AsyncMock()
        return session

    @pytest.fixture
    def mock_lead_repo(self):
        """Create mock lead repository."""
        repo = MagicMock()
        repo.get_or_create_by_visitor_id = AsyncMock()
        repo.link_to_user = AsyncMock()
        repo.get_by_visitor_id = AsyncMock()
        repo.get_by_user_id = AsyncMock()
        repo.get_by_email = AsyncMock()
        repo.set_consent = AsyncMock()
        repo.update_last_activity = AsyncMock()
        repo.create = AsyncMock()
        return repo

    @pytest.fixture
    def mock_interaction_repo(self):
        """Create mock interaction repository."""
        repo = MagicMock()
        repo.create = AsyncMock()
        repo.get_by_lead = AsyncMock()
        repo.get_session_interactions = AsyncMock()
        repo.count_interactions = AsyncMock()
        return repo

    @pytest.fixture
    def lead_tracking_service(self, mock_session, mock_lead_repo, mock_interaction_repo):
        """Create LeadTrackingService with mocked dependencies."""
        with (
            patch(
                "services.lead_tracking.LeadRepository",
                return_value=mock_lead_repo,
            ),
            patch(
                "services.lead_tracking.LeadInteractionRepository",
                return_value=mock_interaction_repo,
            ),
        ):
            service = LeadTrackingService(mock_session)
            service.lead_repo = mock_lead_repo
            service.interaction_repo = mock_interaction_repo
            return service

    @pytest.fixture
    def mock_lead(self):
        """Create a mock lead."""
        lead = MagicMock()
        lead.id = "lead-123"
        lead.visitor_id = "visitor-abc"
        lead.user_id = None
        lead.email = None
        lead.consent_given = False
        lead.current_score = 50
        lead.source = "organic"
        lead.created_at = datetime.now(timezone.utc)
        lead.updated_at = datetime.now(timezone.utc)
        return lead

    @pytest.fixture
    def mock_interaction(self):
        """Create a mock interaction."""
        interaction = MagicMock()
        interaction.id = "interaction-123"
        interaction.lead_id = "lead-123"
        interaction.interaction_type = "view"
        interaction.property_id = "prop-456"
        interaction.search_query = None
        interaction.created_at = datetime.now(timezone.utc)
        return interaction

    def test_generate_visitor_id(self, lead_tracking_service):
        """Verify visitor ID generation."""
        visitor_id = lead_tracking_service.generate_visitor_id()

        assert isinstance(visitor_id, str)
        # secrets.token_urlsafe(16) produces 22 characters
        assert len(visitor_id) == 22

    @pytest.mark.asyncio
    async def test_track_interaction_creates_lead(
        self,
        lead_tracking_service,
        mock_lead,
        mock_interaction,
    ):
        """Verify tracking creates lead if needed."""
        lead_tracking_service.lead_repo.get_or_create_by_visitor_id = AsyncMock(
            return_value=mock_lead
        )
        lead_tracking_service.interaction_repo.create = AsyncMock(return_value=mock_interaction)

        result = await lead_tracking_service.track_interaction(
            visitor_id="visitor-abc",
            interaction_type="view",
            property_id="prop-456",
        )

        assert result == mock_interaction
        lead_tracking_service.lead_repo.get_or_create_by_visitor_id.assert_called_once_with(
            "visitor-abc"
        )
        lead_tracking_service.interaction_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_track_interaction_links_user(
        self,
        lead_tracking_service,
        mock_lead,
        mock_interaction,
    ):
        """Verify tracking links user if provided."""
        mock_lead.user_id = None
        lead_tracking_service.lead_repo.get_or_create_by_visitor_id = AsyncMock(
            return_value=mock_lead
        )
        lead_tracking_service.interaction_repo.create = AsyncMock(return_value=mock_interaction)

        await lead_tracking_service.track_interaction(
            visitor_id="visitor-abc",
            interaction_type="view",
            user_id="user-123",
        )

        lead_tracking_service.lead_repo.link_to_user.assert_called_once_with(mock_lead, "user-123")

    @pytest.mark.asyncio
    async def test_track_interaction_updates_last_activity(
        self,
        lead_tracking_service,
        mock_lead,
        mock_interaction,
    ):
        """Verify tracking updates last activity timestamp."""
        lead_tracking_service.lead_repo.get_or_create_by_visitor_id = AsyncMock(
            return_value=mock_lead
        )
        lead_tracking_service.interaction_repo.create = AsyncMock(return_value=mock_interaction)

        await lead_tracking_service.track_interaction(
            visitor_id="visitor-abc",
            interaction_type="search",
            search_query="apartments in Warsaw",
        )

        lead_tracking_service.lead_repo.update_last_activity.assert_called_once_with(mock_lead)

    @pytest.mark.asyncio
    async def test_get_or_create_visitor_existing(
        self,
        lead_tracking_service,
        mock_lead,
    ):
        """Verify getting existing visitor."""
        lead_tracking_service.lead_repo.get_by_visitor_id = AsyncMock(return_value=mock_lead)

        lead, is_new = await lead_tracking_service.get_or_create_visitor(visitor_id="visitor-abc")

        assert lead == mock_lead
        assert is_new is False

    @pytest.mark.asyncio
    async def test_get_or_create_visitor_new(
        self,
        lead_tracking_service,
        mock_lead,
    ):
        """Verify creating new visitor."""
        lead_tracking_service.lead_repo.get_by_visitor_id = AsyncMock(return_value=None)
        lead_tracking_service.lead_repo.create = AsyncMock(return_value=mock_lead)

        lead, is_new = await lead_tracking_service.get_or_create_visitor(
            visitor_id="new-visitor",
            source="direct",
        )

        assert is_new is True
        lead_tracking_service.lead_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_or_create_visitor_by_user_id(
        self,
        lead_tracking_service,
        mock_lead,
    ):
        """Verify finding visitor by user ID."""
        lead_tracking_service.lead_repo.get_by_visitor_id = AsyncMock(return_value=None)
        lead_tracking_service.lead_repo.get_by_user_id = AsyncMock(return_value=mock_lead)

        lead, is_new = await lead_tracking_service.get_or_create_visitor(
            visitor_id="visitor-abc",
            user_id="user-123",
        )

        assert lead == mock_lead
        assert is_new is False
        lead_tracking_service.lead_repo.get_by_user_id.assert_called_once_with("user-123")

    @pytest.mark.asyncio
    async def test_get_or_create_visitor_by_email(
        self,
        lead_tracking_service,
        mock_lead,
    ):
        """Verify finding visitor by email."""
        lead_tracking_service.lead_repo.get_by_visitor_id = AsyncMock(return_value=None)
        lead_tracking_service.lead_repo.get_by_user_id = AsyncMock(return_value=None)
        lead_tracking_service.lead_repo.get_by_email = AsyncMock(return_value=mock_lead)

        lead, is_new = await lead_tracking_service.get_or_create_visitor(
            visitor_id="visitor-abc",
            email="test@example.com",
        )

        assert lead == mock_lead
        assert is_new is False
        lead_tracking_service.lead_repo.get_by_email.assert_called_once_with("test@example.com")

    @pytest.mark.asyncio
    async def test_get_or_create_visitor_updates_consent(
        self,
        lead_tracking_service,
        mock_lead,
    ):
        """Verify consent is updated for existing visitor."""
        mock_lead.consent_given = False
        lead_tracking_service.lead_repo.get_by_visitor_id = AsyncMock(return_value=mock_lead)

        await lead_tracking_service.get_or_create_visitor(
            visitor_id="visitor-abc",
            consent_given=True,
        )

        lead_tracking_service.lead_repo.set_consent.assert_called_once_with(mock_lead, True)

    @pytest.mark.asyncio
    async def test_link_visitor_to_user(
        self,
        lead_tracking_service,
        mock_lead,
    ):
        """Verify linking visitor to user."""
        mock_lead.user_id = None
        lead_tracking_service.lead_repo.get_by_visitor_id = AsyncMock(return_value=mock_lead)

        await lead_tracking_service.link_visitor_to_user(
            visitor_id="visitor-abc",
            user_id="user-123",
        )

        lead_tracking_service.lead_repo.link_to_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_link_visitor_already_linked(
        self,
        lead_tracking_service,
        mock_lead,
    ):
        """Verify linking still calls link_to_user (implementation always links)."""
        mock_lead.user_id = "existing-user"
        lead_tracking_service.lead_repo.get_by_visitor_id = AsyncMock(return_value=mock_lead)

        await lead_tracking_service.link_visitor_to_user(
            visitor_id="visitor-abc",
            user_id="user-123",
        )

        # Implementation always calls link_to_user
        lead_tracking_service.lead_repo.link_to_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_lead_interactions(
        self,
        lead_tracking_service,
        mock_lead,
        mock_interaction,
    ):
        """Verify getting lead interactions by visitor_id."""
        lead_tracking_service.lead_repo.get_by_visitor_id = AsyncMock(return_value=mock_lead)
        lead_tracking_service.interaction_repo.get_by_lead = AsyncMock(
            return_value=[mock_interaction]
        )

        interactions = await lead_tracking_service.get_lead_interactions(
            visitor_id="visitor-abc",
            limit=10,
        )

        assert len(interactions) == 1
        assert interactions[0] == mock_interaction
        lead_tracking_service.lead_repo.get_by_visitor_id.assert_called_once_with("visitor-abc")

    @pytest.mark.asyncio
    async def test_get_lead_interactions_not_found(
        self,
        lead_tracking_service,
    ):
        """Verify empty list when lead not found."""
        lead_tracking_service.lead_repo.get_by_visitor_id = AsyncMock(return_value=None)

        interactions = await lead_tracking_service.get_lead_interactions(
            visitor_id="nonexistent",
            limit=10,
        )

        assert interactions == []

    @pytest.mark.asyncio
    async def test_get_lead_by_visitor(
        self,
        lead_tracking_service,
        mock_lead,
    ):
        """Verify getting lead by visitor ID."""
        lead_tracking_service.lead_repo.get_by_visitor_id = AsyncMock(return_value=mock_lead)

        lead = await lead_tracking_service.get_lead_by_visitor("visitor-abc")

        assert lead == mock_lead
        lead_tracking_service.lead_repo.get_by_visitor_id.assert_called_once_with("visitor-abc")


class TestLeadTrackingServiceEdgeCases:
    """Tests for edge cases in LeadTrackingService."""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = MagicMock(spec=AsyncSession)
        session.flush = AsyncMock()
        return session

    @pytest.fixture
    def lead_tracking_service(self, mock_session):
        """Create LeadTrackingService with mocked dependencies."""
        with (
            patch("services.lead_tracking.LeadRepository"),
            patch("services.lead_tracking.LeadInteractionRepository"),
        ):
            service = LeadTrackingService(mock_session)
            service.lead_repo = MagicMock()
            service.interaction_repo = MagicMock()
            service.lead_repo.get_or_create_by_visitor_id = AsyncMock()
            service.lead_repo.link_to_user = AsyncMock()
            service.lead_repo.update_last_activity = AsyncMock()
            service.interaction_repo.create = AsyncMock()
            return service

    @pytest.mark.asyncio
    async def test_track_interaction_with_full_metadata(
        self,
        lead_tracking_service,
    ):
        """Verify tracking with all metadata fields."""
        mock_lead = MagicMock()
        mock_lead.id = "lead-123"
        mock_lead.user_id = None

        mock_interaction = MagicMock()
        mock_interaction.id = "interaction-123"

        lead_tracking_service.lead_repo.get_or_create_by_visitor_id = AsyncMock(
            return_value=mock_lead
        )
        lead_tracking_service.interaction_repo.create = AsyncMock(return_value=mock_interaction)

        result = await lead_tracking_service.track_interaction(
            visitor_id="visitor-abc",
            interaction_type="view",
            property_id="prop-456",
            search_query="apartments Warsaw",
            metadata={"price_min": 500000, "price_max": 1000000},
            session_id="session-xyz",
            page_url="https://example.com/properties/123",
            referrer="https://google.com",
            user_agent="Mozilla/5.0",
            ip_address="192.168.1.1",
            time_spent_seconds=60,
            user_id="user-123",
        )

        assert result == mock_interaction
        call_kwargs = lead_tracking_service.interaction_repo.create.call_args[1]
        assert call_kwargs["interaction_type"] == "view"
        assert call_kwargs["property_id"] == "prop-456"

    @pytest.mark.asyncio
    async def test_get_or_create_visitor_generates_visitor_id(
        self,
        lead_tracking_service,
    ):
        """Verify visitor ID is generated if not provided."""
        mock_lead = MagicMock()
        lead_tracking_service.lead_repo.get_by_visitor_id = AsyncMock(return_value=None)
        lead_tracking_service.lead_repo.create = AsyncMock(return_value=mock_lead)

        lead, is_new = await lead_tracking_service.get_or_create_visitor()

        assert is_new is True
        # Verify create was called with a generated visitor_id
        create_call = lead_tracking_service.lead_repo.create.call_args
        assert create_call is not None
        assert "visitor_id" in create_call[1]
        # secrets.token_urlsafe(16) produces 22 characters
        assert len(create_call[1]["visitor_id"]) == 22
