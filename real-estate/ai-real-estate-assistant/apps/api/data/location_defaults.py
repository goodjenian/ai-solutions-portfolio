"""
Location-based default cost estimates for TCO Calculator.

This module provides realistic default values for property-related costs
across different countries and regions in the EU and USA.

Data sources:
- Property tax rates: Government websites, OECD tax data
- Insurance rates: Industry averages
- Utilities: Local provider averages
- All values are estimates and should be overridden with actual data when available.
"""

from typing import Any

# Location defaults structure:
# {
#     "COUNTRY_CODE": {
#         "region_slug": {
#             "property_tax_rate": float,      # Annual % of property value
#             "avg_insurance_rate": float,     # Annual % of property value
#             "avg_utilities_per_sqm": float,  # Monthly cost per sqm (EUR/USD)
#             "avg_internet": float,           # Monthly cost
#             "avg_parking": float,            # Monthly cost if applicable
#             "currency": str,                 # Default currency
#         }
#     }
# }

LOCATION_DEFAULTS: dict[str, dict[str, dict[str, Any]]] = {
    # ===========================================
    # EUROPEAN UNION
    # ===========================================
    "DE": {  # Germany
        "berlin": {
            "property_tax_rate": 0.011,  # Grundsteuer ~1.1%
            "avg_insurance_rate": 0.002,  # Wohngebäudeversicherung
            "avg_utilities_per_sqm": 2.50,  # €/sqm/month (heating, water, etc.)
            "avg_internet": 35.0,  # €/month
            "avg_parking": 50.0,  # €/month (rented parking spot)
            "currency": "EUR",
        },
        "munich": {
            "property_tax_rate": 0.013,
            "avg_insurance_rate": 0.002,
            "avg_utilities_per_sqm": 3.00,
            "avg_internet": 35.0,
            "avg_parking": 80.0,
            "currency": "EUR",
        },
        "hamburg": {
            "property_tax_rate": 0.012,
            "avg_insurance_rate": 0.002,
            "avg_utilities_per_sqm": 2.80,
            "avg_internet": 35.0,
            "avg_parking": 60.0,
            "currency": "EUR",
        },
        "frankfurt": {
            "property_tax_rate": 0.013,
            "avg_insurance_rate": 0.002,
            "avg_utilities_per_sqm": 2.70,
            "avg_internet": 35.0,
            "avg_parking": 70.0,
            "currency": "EUR",
        },
        "cologne": {
            "property_tax_rate": 0.011,
            "avg_insurance_rate": 0.002,
            "avg_utilities_per_sqm": 2.60,
            "avg_internet": 35.0,
            "avg_parking": 55.0,
            "currency": "EUR",
        },
        "stuttgart": {
            "property_tax_rate": 0.012,
            "avg_insurance_rate": 0.002,
            "avg_utilities_per_sqm": 2.75,
            "avg_internet": 35.0,
            "avg_parking": 65.0,
            "currency": "EUR",
        },
        "dusseldorf": {
            "property_tax_rate": 0.011,
            "avg_insurance_rate": 0.002,
            "avg_utilities_per_sqm": 2.65,
            "avg_internet": 35.0,
            "avg_parking": 60.0,
            "currency": "EUR",
        },
    },
    "ES": {  # Spain
        "madrid": {
            "property_tax_rate": 0.004,  # IBI ~0.4%
            "avg_insurance_rate": 0.002,
            "avg_utilities_per_sqm": 2.00,
            "avg_internet": 30.0,
            "avg_parking": 40.0,
            "currency": "EUR",
        },
        "barcelona": {
            "property_tax_rate": 0.004,
            "avg_insurance_rate": 0.002,
            "avg_utilities_per_sqm": 2.10,
            "avg_internet": 30.0,
            "avg_parking": 45.0,
            "currency": "EUR",
        },
        "valencia": {
            "property_tax_rate": 0.004,
            "avg_insurance_rate": 0.002,
            "avg_utilities_per_sqm": 1.80,
            "avg_internet": 28.0,
            "avg_parking": 35.0,
            "currency": "EUR",
        },
        "seville": {
            "property_tax_rate": 0.004,
            "avg_insurance_rate": 0.002,
            "avg_utilities_per_sqm": 1.75,
            "avg_internet": 28.0,
            "avg_parking": 30.0,
            "currency": "EUR",
        },
    },
    "GB": {  # United Kingdom
        "london": {
            "property_tax_rate": 0.005,  # Council tax varies, approximate
            "avg_insurance_rate": 0.002,
            "avg_utilities_per_sqm": 3.50,  # GBP/sqm/month
            "avg_internet": 35.0,
            "avg_parking": 150.0,  # Very high in London
            "currency": "GBP",
            "council_tax_annual": 1500.0,  # Band D average
        },
        "manchester": {
            "property_tax_rate": 0.005,
            "avg_insurance_rate": 0.002,
            "avg_utilities_per_sqm": 2.80,
            "avg_internet": 30.0,
            "avg_parking": 80.0,
            "currency": "GBP",
            "council_tax_annual": 1200.0,
        },
        "birmingham": {
            "property_tax_rate": 0.005,
            "avg_insurance_rate": 0.002,
            "avg_utilities_per_sqm": 2.70,
            "avg_internet": 30.0,
            "avg_parking": 70.0,
            "currency": "GBP",
            "council_tax_annual": 1150.0,
        },
        "edinburgh": {
            "property_tax_rate": 0.005,
            "avg_insurance_rate": 0.002,
            "avg_utilities_per_sqm": 2.90,
            "avg_internet": 30.0,
            "avg_parking": 90.0,
            "currency": "GBP",
            "council_tax_annual": 1250.0,
        },
    },
    "FR": {  # France
        "paris": {
            "property_tax_rate": 0.008,  # Taxe foncière
            "avg_insurance_rate": 0.002,
            "avg_utilities_per_sqm": 3.00,
            "avg_internet": 35.0,
            "avg_parking": 100.0,
            "currency": "EUR",
            "taxe_habitation_rate": 0.01,  # Secondary residences only now
        },
        "lyon": {
            "property_tax_rate": 0.007,
            "avg_insurance_rate": 0.002,
            "avg_utilities_per_sqm": 2.50,
            "avg_internet": 32.0,
            "avg_parking": 60.0,
            "currency": "EUR",
        },
        "marseille": {
            "property_tax_rate": 0.007,
            "avg_insurance_rate": 0.002,
            "avg_utilities_per_sqm": 2.40,
            "avg_internet": 32.0,
            "avg_parking": 50.0,
            "currency": "EUR",
        },
        "nice": {
            "property_tax_rate": 0.007,
            "avg_insurance_rate": 0.002,
            "avg_utilities_per_sqm": 2.60,
            "avg_internet": 32.0,
            "avg_parking": 70.0,
            "currency": "EUR",
        },
    },
    "IT": {  # Italy
        "rome": {
            "property_tax_rate": 0.008,  # IMU
            "avg_insurance_rate": 0.002,
            "avg_utilities_per_sqm": 2.20,
            "avg_internet": 28.0,
            "avg_parking": 60.0,
            "currency": "EUR",
        },
        "milan": {
            "property_tax_rate": 0.008,
            "avg_insurance_rate": 0.002,
            "avg_utilities_per_sqm": 2.50,
            "avg_internet": 30.0,
            "avg_parking": 80.0,
            "currency": "EUR",
        },
    },
    "NL": {  # Netherlands
        "amsterdam": {
            "property_tax_rate": 0.006,  # Onroerendezaakbelasting
            "avg_insurance_rate": 0.002,
            "avg_utilities_per_sqm": 3.00,
            "avg_internet": 40.0,
            "avg_parking": 100.0,
            "currency": "EUR",
        },
        "rotterdam": {
            "property_tax_rate": 0.006,
            "avg_insurance_rate": 0.002,
            "avg_utilities_per_sqm": 2.80,
            "avg_internet": 38.0,
            "avg_parking": 70.0,
            "currency": "EUR",
        },
    },
    # ===========================================
    # UNITED STATES
    # ===========================================
    "US": {
        # New York
        "new_york_city": {
            "property_tax_rate": 0.018,  # NYC effective rate
            "avg_insurance_rate": 0.004,
            "avg_utilities_per_sqm": 4.00,  # USD/sqm/month
            "avg_internet": 70.0,
            "avg_parking": 400.0,  # Very high in Manhattan
            "currency": "USD",
        },
        "buffalo": {
            "property_tax_rate": 0.025,  # High NY state taxes
            "avg_insurance_rate": 0.003,
            "avg_utilities_per_sqm": 2.50,
            "avg_internet": 60.0,
            "avg_parking": 50.0,
            "currency": "USD",
        },
        # California
        "san_francisco": {
            "property_tax_rate": 0.011,  # Prop 13 caps at 1%
            "avg_insurance_rate": 0.003,
            "avg_utilities_per_sqm": 3.50,
            "avg_internet": 70.0,
            "avg_parking": 300.0,
            "currency": "USD",
        },
        "los_angeles": {
            "property_tax_rate": 0.011,
            "avg_insurance_rate": 0.003,
            "avg_utilities_per_sqm": 3.00,
            "avg_internet": 65.0,
            "avg_parking": 150.0,
            "currency": "USD",
        },
        "san_diego": {
            "property_tax_rate": 0.011,
            "avg_insurance_rate": 0.003,
            "avg_utilities_per_sqm": 2.80,
            "avg_internet": 65.0,
            "avg_parking": 100.0,
            "currency": "USD",
        },
        # Texas (no state income tax, but high property tax)
        "austin": {
            "property_tax_rate": 0.022,
            "avg_insurance_rate": 0.005,
            "avg_utilities_per_sqm": 2.50,
            "avg_internet": 60.0,
            "avg_parking": 75.0,
            "currency": "USD",
        },
        "houston": {
            "property_tax_rate": 0.024,
            "avg_insurance_rate": 0.006,  # Higher due to flood risk
            "avg_utilities_per_sqm": 2.40,
            "avg_internet": 60.0,
            "avg_parking": 60.0,
            "currency": "USD",
        },
        "dallas": {
            "property_tax_rate": 0.023,
            "avg_insurance_rate": 0.004,
            "avg_utilities_per_sqm": 2.30,
            "avg_internet": 60.0,
            "avg_parking": 65.0,
            "currency": "USD",
        },
        # Florida (no state income tax)
        "miami": {
            "property_tax_rate": 0.010,
            "avg_insurance_rate": 0.008,  # Very high due to hurricane risk
            "avg_utilities_per_sqm": 2.80,
            "avg_internet": 65.0,
            "avg_parking": 100.0,
            "currency": "USD",
        },
        "tampa": {
            "property_tax_rate": 0.010,
            "avg_insurance_rate": 0.007,
            "avg_utilities_per_sqm": 2.60,
            "avg_internet": 60.0,
            "avg_parking": 70.0,
            "currency": "USD",
        },
        "orlando": {
            "property_tax_rate": 0.010,
            "avg_insurance_rate": 0.006,
            "avg_utilities_per_sqm": 2.50,
            "avg_internet": 60.0,
            "avg_parking": 60.0,
            "currency": "USD",
        },
        # Other major metros
        "chicago": {
            "property_tax_rate": 0.020,
            "avg_insurance_rate": 0.003,
            "avg_utilities_per_sqm": 2.70,
            "avg_internet": 60.0,
            "avg_parking": 120.0,
            "currency": "USD",
        },
        "seattle": {
            "property_tax_rate": 0.011,
            "avg_insurance_rate": 0.003,
            "avg_utilities_per_sqm": 2.80,
            "avg_internet": 70.0,
            "avg_parking": 150.0,
            "currency": "USD",
        },
        "denver": {
            "property_tax_rate": 0.008,
            "avg_insurance_rate": 0.003,
            "avg_utilities_per_sqm": 2.40,
            "avg_internet": 65.0,
            "avg_parking": 80.0,
            "currency": "USD",
        },
        "phoenix": {
            "property_tax_rate": 0.006,
            "avg_insurance_rate": 0.003,
            "avg_utilities_per_sqm": 2.50,  # High AC costs
            "avg_internet": 60.0,
            "avg_parking": 50.0,
            "currency": "USD",
        },
        "boston": {
            "property_tax_rate": 0.011,
            "avg_insurance_rate": 0.003,
            "avg_utilities_per_sqm": 3.20,
            "avg_internet": 70.0,
            "avg_parking": 200.0,
            "currency": "USD",
        },
        "washington_dc": {
            "property_tax_rate": 0.006,
            "avg_insurance_rate": 0.003,
            "avg_utilities_per_sqm": 3.00,
            "avg_internet": 70.0,
            "avg_parking": 250.0,
            "currency": "USD",
        },
    },
}

# Country-level defaults (used when specific region not found)
COUNTRY_DEFAULTS: dict[str, dict[str, Any]] = {
    "DE": {
        "property_tax_rate": 0.012,
        "avg_insurance_rate": 0.002,
        "avg_utilities_per_sqm": 2.60,
        "avg_internet": 35.0,
        "avg_parking": 55.0,
        "currency": "EUR",
    },
    "ES": {
        "property_tax_rate": 0.004,
        "avg_insurance_rate": 0.002,
        "avg_utilities_per_sqm": 1.90,
        "avg_internet": 29.0,
        "avg_parking": 38.0,
        "currency": "EUR",
    },
    "GB": {
        "property_tax_rate": 0.005,
        "avg_insurance_rate": 0.002,
        "avg_utilities_per_sqm": 2.90,
        "avg_internet": 32.0,
        "avg_parking": 90.0,
        "currency": "GBP",
    },
    "FR": {
        "property_tax_rate": 0.007,
        "avg_insurance_rate": 0.002,
        "avg_utilities_per_sqm": 2.60,
        "avg_internet": 33.0,
        "avg_parking": 65.0,
        "currency": "EUR",
    },
    "IT": {
        "property_tax_rate": 0.008,
        "avg_insurance_rate": 0.002,
        "avg_utilities_per_sqm": 2.30,
        "avg_internet": 29.0,
        "avg_parking": 65.0,
        "currency": "EUR",
    },
    "NL": {
        "property_tax_rate": 0.006,
        "avg_insurance_rate": 0.002,
        "avg_utilities_per_sqm": 2.90,
        "avg_internet": 39.0,
        "avg_parking": 85.0,
        "currency": "EUR",
    },
    "US": {
        "property_tax_rate": 0.012,
        "avg_insurance_rate": 0.004,
        "avg_utilities_per_sqm": 2.80,
        "avg_internet": 65.0,
        "avg_parking": 100.0,
        "currency": "USD",
    },
}


def get_location_defaults(country: str, region: str | None = None) -> dict[str, Any]:
    """
    Get location-based default cost estimates.

    Args:
        country: ISO 3166-1 alpha-2 country code (e.g., "DE", "US")
        region: Region/city name (e.g., "berlin", "new_york_city")

    Returns:
        Dictionary with default cost estimates for the location
    """
    country = country.upper()

    # Try to get region-specific defaults
    if region:
        region = region.lower().replace(" ", "_").replace("-", "_")
        if country in LOCATION_DEFAULTS and region in LOCATION_DEFAULTS[country]:
            return LOCATION_DEFAULTS[country][region].copy()

    # Fall back to country defaults
    if country in COUNTRY_DEFAULTS:
        return COUNTRY_DEFAULTS[country].copy()

    # Ultimate fallback (conservative estimates)
    return {
        "property_tax_rate": 0.01,
        "avg_insurance_rate": 0.003,
        "avg_utilities_per_sqm": 2.50,
        "avg_internet": 40.0,
        "avg_parking": 50.0,
        "currency": "USD",
    }


def get_available_locations() -> dict[str, list[str]]:
    """
    Get all available locations with defaults.

    Returns:
        Dictionary mapping country codes to lists of available regions
    """
    result = {}
    for country, regions in LOCATION_DEFAULTS.items():
        result[country] = list(regions.keys())
    return result
