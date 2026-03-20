"""
Tests for property export functionality with Points of Interest.
"""

import json

import pytest

from data.schemas import PointOfInterest, Property, PropertyCollection, PropertyType
from utils import PropertyExporter


@pytest.fixture
def property_with_pois():
    """Create a property with POIs."""
    poi1 = PointOfInterest(
        name="Central Park",
        category="park",
        latitude=52.2,
        longitude=21.0,
        distance_meters=250.0,
        tags={"leisure": "park"},
    )
    poi2 = PointOfInterest(
        name="Main Station",
        category="transport",
        latitude=52.3,
        longitude=21.1,
        distance_meters=500.0,
    )

    prop = Property(
        id="poi_prop",
        city="Warsaw",
        rooms=2,
        price=1000,
        property_type=PropertyType.APARTMENT,
        title="Apartment near Park",
        points_of_interest=[poi1, poi2],
    )
    return PropertyCollection(properties=[prop], total_count=1)


def test_export_dataframe_with_poi_summary(property_with_pois):
    """Test DataFrame conversion includes POI summary."""
    exporter = PropertyExporter(property_with_pois)
    df = exporter.df

    assert "poi_count" in df.columns
    assert "closest_poi_distance" in df.columns
    assert "poi_categories" in df.columns

    assert df.iloc[0]["poi_count"] == 2
    assert df.iloc[0]["closest_poi_distance"] == 250.0
    assert "park" in df.iloc[0]["poi_categories"]
    assert "transport" in df.iloc[0]["poi_categories"]


def test_export_markdown_includes_pois(property_with_pois):
    """Test Markdown export includes POI section."""
    exporter = PropertyExporter(property_with_pois)
    md = exporter.export_to_markdown()

    assert "- **Points of Interest**:" in md
    assert "Central Park (park): 250m" in md
    assert "Main Station (transport): 500m" in md


def test_export_json_includes_pois(property_with_pois):
    """Test JSON export includes POI data."""
    exporter = PropertyExporter(property_with_pois)
    json_data = exporter.export_to_json()
    parsed = json.loads(json_data)

    prop = parsed["properties"][0]
    assert "points_of_interest" in prop
    assert len(prop["points_of_interest"]) == 2
    assert prop["points_of_interest"][0]["name"] == "Central Park"
