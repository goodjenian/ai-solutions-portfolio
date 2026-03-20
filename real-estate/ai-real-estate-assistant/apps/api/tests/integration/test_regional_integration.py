from datetime import datetime

import pytest

from analytics.market_insights import MarketInsights
from data.schemas import Property, PropertyCollection


@pytest.fixture
def multi_region_data():
    """Create a dataset with properties from multiple regions for integration testing."""
    base_date = datetime.now()
    properties = [
        # USA Properties
        Property(
            id="usa1",
            title="NYC Condo",
            description="Luxury",
            price=1000000,
            currency="USD",
            city="New York",
            country="USA",
            region="NY",
            listing_type="sale",
            property_type="apartment",
            bedrooms=2,
            bathrooms=2,
            area=100,
            date_posted=base_date,
        ),
        Property(
            id="usa2",
            title="LA House",
            description="Spacious",
            price=2000000,
            currency="USD",
            city="Los Angeles",
            country="USA",
            region="CA",
            listing_type="sale",
            property_type="house",
            bedrooms=3,
            bathrooms=3,
            area=200,
            date_posted=base_date,
        ),
        # Turkey Properties
        Property(
            id="tr1",
            title="Istanbul Apt",
            description="Bosphorus view",
            price=500000,
            currency="USD",
            city="Istanbul",
            country="Turkey",
            region="Marmara",
            listing_type="sale",
            property_type="apartment",
            bedrooms=2,
            bathrooms=1,
            area=90,
            date_posted=base_date,
        ),
        Property(
            id="tr2",
            title="Antalya Villa",
            description="Seaside",
            price=750000,
            currency="USD",
            city="Antalya",
            country="Turkey",
            region="Mediterranean",
            listing_type="sale",
            property_type="house",
            bedrooms=4,
            bathrooms=3,
            area=250,
            date_posted=base_date,
        ),
        # Russia Properties
        Property(
            id="ru1",
            title="Moscow Flat",
            description="City center",
            price=400000,
            currency="USD",
            city="Moscow",
            country="Russia",
            region="Central",
            listing_type="sale",
            property_type="apartment",
            bedrooms=1,
            bathrooms=1,
            area=50,
            date_posted=base_date,
        ),
    ]
    return PropertyCollection(properties=properties, total_count=len(properties))


def test_regional_market_insights_integration(multi_region_data):
    """Integration test for MarketInsights with multi-region data."""
    insights = MarketInsights(multi_region_data)

    # 1. Test Country Statistics
    usa_stats = insights.get_country_statistics("USA")
    assert usa_stats.total_properties == 2
    assert usa_stats.average_price == 1500000
    assert "New York" in usa_stats.cities
    assert "Los Angeles" in usa_stats.cities

    tr_stats = insights.get_country_statistics("Turkey")
    assert tr_stats.total_properties == 2
    assert tr_stats.average_price == 625000

    # 2. Test Region Statistics
    marmara_stats = insights.get_region_statistics("Marmara")
    assert marmara_stats.total_properties == 1
    assert "Istanbul" in marmara_stats.cities
    assert marmara_stats.cities["Istanbul"] == 1

    # 3. Test Cross-Country Indices
    indices_df = insights.get_country_indices(["USA", "Turkey", "Russia"])
    assert not indices_df.empty
    # Should have entries for each country
    countries_in_indices = indices_df["country"].unique()
    assert "USA" in countries_in_indices
    assert "Turkey" in countries_in_indices
    assert "Russia" in countries_in_indices

    # 4. Test Price Trends with filters
    usa_trend = insights.get_price_trend(country="USA")
    assert usa_trend.sample_size == 2

    tr_trend = insights.get_price_trend(country="Turkey")
    assert tr_trend.sample_size == 2

    # Verify no cross-contamination
    assert usa_trend.average_price != tr_trend.average_price
