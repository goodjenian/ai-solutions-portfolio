"""
Pre-computed city average scores for neighborhood comparison.

This module provides baseline scores for Polish and European cities
to enable comparison between property neighborhood scores and city averages.

Data sources:
- Safety: Numbeo Safety Index, Eurostat crime statistics
- Air Quality: WAQI historical data, WHO air quality database
- Transport: City transit authority data, GTFS feeds
- General: European urban statistics

Note: These are approximations based on publicly available data.
Actual neighborhood scores will vary significantly within cities.
"""

from typing import Dict, Optional

# City average scores for Poland (primary market) and other European cities
# All scores are on 0-100 scale where higher is better
CITY_AVERAGES: Dict[str, Dict[str, float]] = {
    # === POLAND ===
    "warsaw": {
        "safety": 75.0,
        "schools": 72.0,
        "amenities": 80.0,
        "walkability": 78.0,
        "green_space": 60.0,
        "air_quality": 55.0,  # Known air quality issues in winter
        "noise_level": 65.0,
        "public_transport": 85.0,  # Excellent metro/tram/bus network
        "overall": 71.0,
        "population": 1790658,
        "country": "Poland",
    },
    "krakow": {
        "safety": 78.0,
        "schools": 75.0,
        "amenities": 75.0,
        "walkability": 72.0,
        "green_space": 65.0,
        "air_quality": 48.0,  # Significant smog issues
        "noise_level": 60.0,
        "public_transport": 75.0,  # Good tram/bus, no metro
        "overall": 68.0,
        "population": 779115,
        "country": "Poland",
    },
    "wroclaw": {
        "safety": 76.0,
        "schools": 74.0,
        "amenities": 78.0,
        "walkability": 75.0,
        "green_space": 68.0,
        "air_quality": 58.0,
        "noise_level": 62.0,
        "public_transport": 72.0,
        "overall": 70.0,
        "population": 641607,
        "country": "Poland",
    },
    "poznan": {
        "safety": 80.0,
        "schools": 76.0,
        "amenities": 76.0,
        "walkability": 74.0,
        "green_space": 70.0,
        "air_quality": 62.0,
        "noise_level": 58.0,
        "public_transport": 70.0,
        "overall": 71.0,
        "population": 546859,
        "country": "Poland",
    },
    "gdansk": {
        "safety": 77.0,
        "schools": 73.0,
        "amenities": 74.0,
        "walkability": 73.0,
        "green_space": 72.0,  # Near sea and forests
        "air_quality": 68.0,  # Coastal air
        "noise_level": 55.0,
        "public_transport": 68.0,
        "overall": 70.0,
        "population": 470907,
        "country": "Poland",
    },
    "lodz": {
        "safety": 72.0,
        "schools": 70.0,
        "amenities": 70.0,
        "walkability": 68.0,
        "green_space": 58.0,
        "air_quality": 56.0,
        "noise_level": 64.0,
        "public_transport": 62.0,
        "overall": 65.0,
        "population": 672185,
        "country": "Poland",
    },
    "katowice": {
        "safety": 70.0,
        "schools": 69.0,
        "amenities": 72.0,
        "walkability": 66.0,
        "green_space": 55.0,  # Industrial heritage
        "air_quality": 50.0,  # Industrial area
        "noise_level": 68.0,
        "public_transport": 72.0,  # Good regional transit
        "overall": 65.0,
        "population": 292774,
        "country": "Poland",
    },
    "gdynia": {
        "safety": 78.0,
        "schools": 74.0,
        "amenities": 72.0,
        "walkability": 71.0,
        "green_space": 74.0,
        "air_quality": 70.0,
        "noise_level": 52.0,
        "public_transport": 70.0,
        "overall": 70.0,
        "population": 246306,
        "country": "Poland",
    },
    "szczecin": {
        "safety": 73.0,
        "schools": 71.0,
        "amenities": 70.0,
        "walkability": 68.0,
        "green_space": 66.0,
        "air_quality": 64.0,
        "noise_level": 58.0,
        "public_transport": 65.0,
        "overall": 67.0,
        "population": 398255,
        "country": "Poland",
    },
    "bydgoszcz": {
        "safety": 74.0,
        "schools": 72.0,
        "amenities": 68.0,
        "walkability": 66.0,
        "green_space": 64.0,
        "air_quality": 65.0,
        "noise_level": 56.0,
        "public_transport": 60.0,
        "overall": 66.0,
        "population": 348190,
        "country": "Poland",
    },
    "lublin": {
        "safety": 76.0,
        "schools": 73.0,
        "amenities": 67.0,
        "walkability": 65.0,
        "green_space": 62.0,
        "air_quality": 63.0,
        "noise_level": 54.0,
        "public_transport": 62.0,
        "overall": 65.0,
        "population": 339784,
        "country": "Poland",
    },
    # === SPAIN ===
    "madrid": {
        "safety": 72.0,
        "schools": 74.0,
        "amenities": 82.0,
        "walkability": 80.0,
        "green_space": 58.0,
        "air_quality": 52.0,
        "noise_level": 70.0,
        "public_transport": 88.0,  # Excellent metro
        "overall": 72.0,
        "population": 3223334,
        "country": "Spain",
    },
    "barcelona": {
        "safety": 68.0,
        "schools": 72.0,
        "amenities": 84.0,
        "walkability": 85.0,
        "green_space": 52.0,
        "air_quality": 55.0,
        "noise_level": 72.0,
        "public_transport": 82.0,
        "overall": 71.0,
        "population": 1620343,
        "country": "Spain",
    },
    "valencia": {
        "safety": 74.0,
        "schools": 70.0,
        "amenities": 78.0,
        "walkability": 76.0,
        "green_space": 65.0,  # Turia gardens
        "air_quality": 62.0,
        "noise_level": 62.0,
        "public_transport": 68.0,
        "overall": 69.0,
        "population": 791413,
        "country": "Spain",
    },
    # === GERMANY ===
    "berlin": {
        "safety": 82.0,
        "schools": 78.0,
        "amenities": 80.0,
        "walkability": 78.0,
        "green_space": 72.0,  # Many parks and forests
        "air_quality": 62.0,
        "noise_level": 68.0,
        "public_transport": 88.0,  # Excellent U-Bahn/S-Bahn
        "overall": 76.0,
        "population": 3644826,
        "country": "Germany",
    },
    "munich": {
        "safety": 85.0,
        "schools": 82.0,
        "amenities": 82.0,
        "walkability": 80.0,
        "green_space": 70.0,
        "air_quality": 60.0,
        "noise_level": 64.0,
        "public_transport": 90.0,  # One of the best
        "overall": 77.0,
        "population": 1471508,
        "country": "Germany",
    },
    "hamburg": {
        "safety": 80.0,
        "schools": 78.0,
        "amenities": 80.0,
        "walkability": 76.0,
        "green_space": 68.0,
        "air_quality": 64.0,
        "noise_level": 66.0,
        "public_transport": 84.0,
        "overall": 75.0,
        "population": 1841179,
        "country": "Germany",
    },
    "frankfurt": {
        "safety": 78.0,
        "schools": 76.0,
        "amenities": 80.0,
        "walkability": 74.0,
        "green_space": 60.0,
        "air_quality": 58.0,  # Airport impact
        "noise_level": 70.0,  # Airport noise
        "public_transport": 82.0,
        "overall": 72.0,
        "population": 753056,
        "country": "Germany",
    },
    # === FRANCE ===
    "paris": {
        "safety": 65.0,
        "schools": 76.0,
        "amenities": 88.0,
        "walkability": 90.0,  # Very walkable
        "green_space": 48.0,
        "air_quality": 48.0,  # Known issues
        "noise_level": 75.0,
        "public_transport": 92.0,  # Excellent metro
        "overall": 73.0,
        "population": 2161000,
        "country": "France",
    },
    "lyon": {
        "safety": 70.0,
        "schools": 74.0,
        "amenities": 80.0,
        "walkability": 78.0,
        "green_space": 58.0,
        "air_quality": 55.0,
        "noise_level": 64.0,
        "public_transport": 78.0,
        "overall": 70.0,
        "population": 513275,
        "country": "France",
    },
    # === UK ===
    "london": {
        "safety": 70.0,
        "schools": 74.0,
        "amenities": 86.0,
        "walkability": 82.0,
        "green_space": 55.0,
        "air_quality": 45.0,  # Known issues
        "noise_level": 76.0,
        "public_transport": 90.0,  # Excellent Underground
        "overall": 72.0,
        "population": 8982000,
        "country": "United Kingdom",
    },
    "manchester": {
        "safety": 68.0,
        "schools": 70.0,
        "amenities": 78.0,
        "walkability": 72.0,
        "green_space": 52.0,
        "air_quality": 55.0,
        "noise_level": 68.0,
        "public_transport": 72.0,
        "overall": 67.0,
        "population": 553230,
        "country": "United Kingdom",
    },
    # === DEFAULT ===
    "default": {
        "safety": 70.0,
        "schools": 70.0,
        "amenities": 70.0,
        "walkability": 70.0,
        "green_space": 60.0,
        "air_quality": 60.0,
        "noise_level": 60.0,
        "public_transport": 65.0,
        "overall": 66.0,
        "population": 0,
        "country": "Unknown",
    },
}

# Factor weights for overall score calculation
FACTOR_WEIGHTS: Dict[str, float] = {
    "safety": 0.15,
    "schools": 0.15,
    "amenities": 0.15,
    "walkability": 0.15,
    "green_space": 0.10,
    "air_quality": 0.10,
    "noise_level": 0.10,
    "public_transport": 0.10,
}


def get_city_average(city: str) -> Dict[str, float]:
    """
    Get average scores for a city.

    Args:
        city: City name (case-insensitive)

    Returns:
        Dictionary with all factor scores for the city
    """
    return CITY_AVERAGES.get(city.lower(), CITY_AVERAGES["default"]).copy()


def get_city_factor_score(city: str, factor: str) -> float:
    """
    Get average score for a specific factor in a city.

    Args:
        city: City name (case-insensitive)
        factor: Factor name (e.g., 'safety', 'air_quality')

    Returns:
        Average score for the factor (0-100)
    """
    city_data = get_city_average(city)
    return city_data.get(factor, 70.0)


def calculate_percentile(
    city: str,
    factor: str,
    score: float,
    standard_deviation: float = 10.0,
) -> int:
    """
    Calculate percentile rank of a score within city distribution.

    Uses normal distribution approximation for simplicity.

    Args:
        city: City name
        factor: Factor name
        score: Score to calculate percentile for
        standard_deviation: Assumed std dev for distribution

    Returns:
        Percentile rank (0-100)
    """
    import math

    city_avg = get_city_factor_score(city, factor)

    # Z-score calculation
    if standard_deviation == 0:
        return 50

    z_score = (score - city_avg) / standard_deviation

    # Convert to percentile using error function
    # percentile = 0.5 * (1 + erf(z / sqrt(2)))
    percentile = 0.5 * (1 + math.erf(z_score / math.sqrt(2)))

    return int(max(0, min(100, percentile * 100)))


def compare_to_city(
    city: str,
    scores: Dict[str, float],
) -> Dict[str, Dict[str, float]]:
    """
    Compare property scores to city averages.

    Args:
        city: City name
        scores: Dictionary of property scores by factor

    Returns:
        Dictionary with comparison data:
        {
            "factor": {
                "property_score": float,
                "city_average": float,
                "difference": float,
                "percentile": int,
                "better_than_average": bool,
            },
            ...
        }
    """
    city_data = get_city_average(city)
    comparison: Dict[str, Dict[str, float]] = {}

    for factor, property_score in scores.items():
        city_avg = city_data.get(factor, 70.0)
        difference = property_score - city_avg

        comparison[factor] = {
            "property_score": property_score,
            "city_average": city_avg,
            "difference": round(difference, 1),
            "percentile": calculate_percentile(city, factor, property_score),
            "better_than_average": difference > 0,
        }

    return comparison


def get_supported_cities(country: Optional[str] = None) -> list[str]:
    """
    Get list of supported cities.

    Args:
        country: Filter by country (optional)

    Returns:
        List of city names
    """
    if country is None:
        return [city for city in CITY_AVERAGES.keys() if city != "default"]

    return [
        city
        for city, data in CITY_AVERAGES.items()
        if city != "default" and data.get("country", "").lower() == country.lower()
    ]


def get_polish_cities() -> list[str]:
    """Get list of supported Polish cities."""
    return get_supported_cities(country="Poland")
