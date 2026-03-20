"""Unit tests for PRO filters."""

from datetime import datetime

import pytest

from agents.query_analyzer import get_query_analyzer
from analytics.market_insights import MarketInsights
from data.schemas import Property, PropertyCollection


@pytest.fixture
def sample_properties():
    return [
        Property(
            id="1",
            city="Warsaw",
            price=1000,
            rooms=2,
            has_parking=True,
            has_elevator=True,
            year_built=2020,
            energy_rating="A",
            latitude=52.2297,
            longitude=21.0122,
            scraped_at=datetime.now(),
        ),
        Property(
            id="2",
            city="Krakow",
            price=2000,
            rooms=3,
            has_parking=False,
            has_elevator=True,
            year_built=2010,
            energy_rating="B",
            latitude=50.0647,
            longitude=19.9450,
            scraped_at=datetime.now(),
        ),
        Property(
            id="3",
            city="Warsaw",
            price=1500,
            rooms=2,
            has_parking=True,
            has_elevator=False,
            year_built=1990,
            energy_rating="C",
            latitude=52.2297,
            longitude=21.0122,
            scraped_at=datetime.now(),
        ),
    ]


def test_property_collection_filters(sample_properties):
    collection = PropertyCollection(properties=sample_properties, total_count=3)

    # Filter by parking
    filtered = collection.filter_by_criteria(has_parking=True)
    assert len(filtered.properties) == 2
    assert all(p.has_parking for p in filtered.properties)

    # Filter by elevator
    filtered = collection.filter_by_criteria(has_elevator=True)
    assert len(filtered.properties) == 2
    assert all(p.has_elevator for p in filtered.properties)

    # Filter by year built
    filtered = collection.filter_by_criteria(year_built_min=2000)
    assert len(filtered.properties) == 2
    assert all(p.year_built >= 2000 for p in filtered.properties)

    # Filter by energy rating
    filtered = collection.filter_by_criteria(energy_ratings=["A"])
    assert len(filtered.properties) == 1
    assert filtered.properties[0].energy_rating == "A"


def test_market_insights_filters(sample_properties):
    collection = PropertyCollection(properties=sample_properties, total_count=3)
    insights = MarketInsights(collection)

    # Filter by parking
    df = insights.filter_properties(must_have_parking=True)
    assert len(df) == 2
    assert df["has_parking"].all()

    # Filter by elevator
    df = insights.filter_properties(must_have_elevator=True)
    assert len(df) == 2
    assert df["has_elevator"].all()

    # Filter by year built
    df = insights.filter_properties(year_built_min=2000)
    assert len(df) == 2
    assert (df["year_built"] >= 2000).all()

    # Filter by energy rating
    df = insights.filter_properties(energy_ratings=["A"])
    assert len(df) == 1
    assert df.iloc[0]["energy_rating"] == "A"


def test_query_analyzer_pro_filters():
    analyzer = get_query_analyzer()

    # Parking
    analysis = analyzer.analyze("apartment with parking")
    assert analysis.extracted_filters.get("must_have_parking") is True
    assert analysis.extracted_filters.get("has_parking") is True

    # Elevator
    analysis = analyzer.analyze("flat with elevator")
    assert analysis.extracted_filters.get("must_have_elevator") is True
    assert analysis.extracted_filters.get("has_elevator") is True

    # Year built
    analysis = analyzer.analyze("house built after 2010")
    assert analysis.extracted_filters.get("year_built_min") == 2010

    # Energy rating
    analysis = analyzer.analyze("property with energy class A")
    assert analysis.extracted_filters.get("energy_ratings") == ["A"]
