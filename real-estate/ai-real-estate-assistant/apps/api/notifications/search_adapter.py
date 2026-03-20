"""Adapter to convert DB saved searches to Pydantic models for notification system.

This adapter allows the existing notification infrastructure (AlertManager, scheduler)
to work with the new database-backed SavedSearchDB model by converting to the
Pydantic SavedSearch model that the notification logic expects.
"""

from typing import Any

from db.models import SavedSearchDB
from utils.saved_searches import SavedSearch


def db_to_pydantic(db_search: SavedSearchDB) -> SavedSearch:
    """
    Convert database model to Pydantic SavedSearch for existing notification logic.

    Args:
        db_search: SavedSearchDB database model instance

    Returns:
        SavedSearch Pydantic model with filters extracted from the JSON column
    """
    filters = db_search.filters or {}

    return SavedSearch(
        id=db_search.id,
        name=db_search.name,
        description=db_search.description,
        # Search criteria from filters JSON
        city=filters.get("city"),
        min_price=filters.get("min_price"),
        max_price=filters.get("max_price"),
        min_rooms=filters.get("min_rooms"),
        max_rooms=filters.get("max_rooms"),
        property_types=filters.get("property_types", []),
        # Amenity preferences
        must_have_parking=filters.get("must_have_parking", False),
        must_have_elevator=filters.get("must_have_elevator", False),
        must_have_garden=filters.get("must_have_garden", False),
        must_have_pool=filters.get("must_have_pool", False),
        must_be_furnished=filters.get("must_be_furnished", False),
        # PRO filters
        year_built_min=filters.get("year_built_min"),
        year_built_max=filters.get("year_built_max"),
        energy_certs=filters.get("energy_certs", []),
        # Metadata
        created_at=db_search.created_at,
        last_used=db_search.last_used_at,
        use_count=db_search.use_count,
        # Notification settings
        notify_on_new=db_search.notify_on_new,
        notify_on_price_drop=db_search.notify_on_price_drop,
    )


def filters_to_dict(
    city: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    min_rooms: float | None = None,
    max_rooms: float | None = None,
    property_types: list[str] | None = None,
    must_have_parking: bool = False,
    must_have_elevator: bool = False,
    must_have_garden: bool = False,
    must_have_pool: bool = False,
    must_be_furnished: bool = False,
    year_built_min: int | None = None,
    year_built_max: int | None = None,
    energy_certs: list[str] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """
    Convert individual filter parameters to a filters dict for storage.

    Args:
        Various filter parameters

    Returns:
        Dictionary suitable for storage in SavedSearchDB.filters column
    """
    filters: dict[str, Any] = {}

    if city is not None:
        filters["city"] = city
    if min_price is not None:
        filters["min_price"] = min_price
    if max_price is not None:
        filters["max_price"] = max_price
    if min_rooms is not None:
        filters["min_rooms"] = min_rooms
    if max_rooms is not None:
        filters["max_rooms"] = max_rooms
    if property_types:
        filters["property_types"] = property_types

    if must_have_parking:
        filters["must_have_parking"] = True
    if must_have_elevator:
        filters["must_have_elevator"] = True
    if must_have_garden:
        filters["must_have_garden"] = True
    if must_have_pool:
        filters["must_have_pool"] = True
    if must_be_furnished:
        filters["must_be_furnished"] = True

    if year_built_min is not None:
        filters["year_built_min"] = year_built_min
    if year_built_max is not None:
        filters["year_built_max"] = year_built_max
    if energy_certs:
        filters["energy_certs"] = energy_certs

    # Include any extra filters
    filters.update(extra)

    return filters
