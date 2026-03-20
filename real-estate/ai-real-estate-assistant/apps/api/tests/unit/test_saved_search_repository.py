"""Unit tests for SavedSearch repository and adapter.

Tests for:
- SavedSearchRepository CRUD operations
- search_adapter.db_to_pydantic conversion
- SavedSearchCreate/Update schema validation
"""

from datetime import UTC, datetime

import pytest

from db.schemas import SavedSearchCreate, SavedSearchUpdate
from notifications.search_adapter import db_to_pydantic, filters_to_dict


class TestSavedSearchSchemas:
    """Tests for saved search Pydantic schemas."""

    def test_create_schema_minimal(self):
        """Test creating saved search with minimal fields."""
        schema = SavedSearchCreate(name="Test Search", filters={})
        assert schema.name == "Test Search"
        assert schema.filters == {}
        assert schema.alert_frequency == "daily"
        assert schema.notify_on_new is True
        assert schema.notify_on_price_drop is True

    def test_create_schema_with_filters(self):
        """Test creating saved search with filters."""
        schema = SavedSearchCreate(
            name="Madrid Apartments",
            filters={"city": "Madrid", "max_price": 500000},
            alert_frequency="weekly",
            notify_on_new=True,
            notify_on_price_drop=False,
        )
        assert schema.name == "Madrid Apartments"
        assert schema.filters["city"] == "Madrid"
        assert schema.alert_frequency == "weekly"
        assert schema.notify_on_price_drop is False

    def test_create_schema_invalid_frequency(self):
        """Test that invalid frequency raises validation error."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SavedSearchCreate(
                name="Test",
                filters={},
                alert_frequency="invalid",  # type: ignore
            )

    def test_update_schema_partial(self):
        """Test partial update schema."""
        schema = SavedSearchUpdate(is_active=False)
        assert schema.is_active is False
        assert schema.name is None
        assert schema.filters is None

    def test_update_schema_all_fields(self):
        """Test update schema with all fields."""
        schema = SavedSearchUpdate(
            name="Updated Name",
            description="Updated description",
            filters={"city": "Barcelona"},
            alert_frequency="instant",
            is_active=True,
            notify_on_new=False,
            notify_on_price_drop=True,
        )
        assert schema.name == "Updated Name"
        assert schema.alert_frequency == "instant"


class TestSearchAdapter:
    """Tests for search_adapter functions."""

    def test_db_to_pydantic_conversion(self):
        """Test converting mock DB model to Pydantic SavedSearch."""

        # Create a mock DB model
        class MockSavedSearchDB:
            id = "test-123"
            user_id = "user-456"
            name = "Test Search"
            description = "Test description"
            filters = {
                "city": "Madrid",
                "min_price": 100000,
                "max_price": 500000,
                "property_types": ["apartment", "house"],
                "must_have_parking": True,
                "must_have_elevator": False,
            }
            alert_frequency = "daily"
            is_active = True
            notify_on_new = True
            notify_on_price_drop = True
            created_at = datetime.now(UTC)
            updated_at = datetime.now(UTC)
            last_used_at = None
            use_count = 5

        db_search = MockSavedSearchDB()
        pydantic_search = db_to_pydantic(db_search)

        assert pydantic_search.id == "test-123"
        assert pydantic_search.name == "Test Search"
        assert pydantic_search.city == "Madrid"
        assert pydantic_search.min_price == 100000
        assert pydantic_search.max_price == 500000
        assert pydantic_search.property_types == ["apartment", "house"]
        assert pydantic_search.must_have_parking is True
        assert pydantic_search.must_have_elevator is False
        assert pydantic_search.use_count == 5

    def test_db_to_pydantic_empty_filters(self):
        """Test conversion with empty filters."""

        class MockSavedSearchDB:
            id = "test-empty"
            user_id = "user-789"
            name = "Empty Search"
            description = None
            filters = {}
            alert_frequency = "none"
            is_active = True
            notify_on_new = False
            notify_on_price_drop = False
            created_at = datetime.now(UTC)
            updated_at = datetime.now(UTC)
            last_used_at = None
            use_count = 0

        db_search = MockSavedSearchDB()
        pydantic_search = db_to_pydantic(db_search)

        assert pydantic_search.id == "test-empty"
        assert pydantic_search.city is None
        assert pydantic_search.min_price is None
        assert pydantic_search.property_types == []
        assert pydantic_search.must_have_parking is False

    def test_filters_to_dict_basic(self):
        """Test converting filter params to dict."""
        filters = filters_to_dict(
            city="Madrid",
            min_price=100000,
            max_price=500000,
        )
        assert filters["city"] == "Madrid"
        assert filters["min_price"] == 100000
        assert filters["max_price"] == 500000

    def test_filters_to_dict_amenities(self):
        """Test filter conversion with amenity flags."""
        filters = filters_to_dict(
            city="Barcelona",
            must_have_parking=True,
            must_have_elevator=True,
            must_have_garden=False,  # False values not included
        )
        assert filters["city"] == "Barcelona"
        assert filters["must_have_parking"] is True
        assert filters["must_have_elevator"] is True
        assert "must_have_garden" not in filters  # False values not included

    def test_filters_to_dict_property_types(self):
        """Test filter conversion with property types list."""
        filters = filters_to_dict(
            property_types=["apartment", "studio"],
            min_rooms=2,
        )
        assert filters["property_types"] == ["apartment", "studio"]
        assert filters["min_rooms"] == 2

    def test_filters_to_dict_none_values(self):
        """Test that None values are not included."""
        filters = filters_to_dict(
            city="Madrid",
            min_price=None,
            max_price=None,
        )
        assert filters["city"] == "Madrid"
        assert "min_price" not in filters
        assert "max_price" not in filters


class TestSavedSearchMatching:
    """Tests for saved search filter matching logic."""

    def test_matches_city(self):
        """Test property matching by city."""
        from utils.saved_searches import SavedSearch

        search = SavedSearch(
            id="test-1",
            name="Madrid Search",
            city="Madrid",
        )

        # Should match
        assert search.matches({"city": "Madrid", "price": 300000}) is True
        # Case insensitive
        assert search.matches({"city": "MADRID", "price": 300000}) is True
        # Should not match
        assert search.matches({"city": "Barcelona", "price": 300000}) is False

    def test_matches_price_range(self):
        """Test property matching by price range."""
        from utils.saved_searches import SavedSearch

        search = SavedSearch(
            id="test-2",
            name="Budget Search",
            min_price=100000,
            max_price=300000,
        )

        assert search.matches({"city": "Madrid", "price": 200000}) is True
        assert search.matches({"city": "Madrid", "price": 50000}) is False
        assert search.matches({"city": "Madrid", "price": 400000}) is False

    def test_matches_amenities(self):
        """Test property matching by amenities."""
        from utils.saved_searches import SavedSearch

        search = SavedSearch(
            id="test-3",
            name="Parking Required",
            must_have_parking=True,
        )

        assert search.matches({"city": "Madrid", "has_parking": True}) is True
        assert search.matches({"city": "Madrid", "has_parking": False}) is False

    def test_matches_all_criteria(self):
        """Test property matching all criteria."""
        from utils.saved_searches import SavedSearch

        search = SavedSearch(
            id="test-4",
            name="Complete Search",
            city="Madrid",
            min_price=200000,
            max_price=400000,
            min_rooms=2,
            must_have_elevator=True,
        )

        property_match = {
            "city": "Madrid",
            "price": 300000,
            "rooms": 3,
            "has_elevator": True,
        }
        assert search.matches(property_match) is True

        # Missing elevator
        property_no_elevator = {
            "city": "Madrid",
            "price": 300000,
            "rooms": 3,
            "has_elevator": False,
        }
        assert search.matches(property_no_elevator) is False
