"""
External portal adapters for fetching property data from real estate portals.

This package provides an extensible adapter system for ingesting property data
from external APIs and web scraping sources.
"""

from data.adapters.air_quality_adapter import (
    AirQualityAdapter,
    AirQualityResult,
    AirQualityStation,
    get_air_quality_adapter,
)
from data.adapters.base import (
    ExternalSourceAdapter,
    PortalFetchResult,
    PortalFilter,
)
from data.adapters.neighborhood_adapter import NeighborhoodAdapter, get_neighborhood_adapter
from data.adapters.noise_adapter import (
    NoiseAdapter,
    NoiseResult,
    NoiseSource,
    get_noise_adapter,
)
from data.adapters.overpass_adapter import OverpassAdapter
from data.adapters.registry import (
    AdapterRegistry,
    get_adapter,
    register_adapter,
)
from data.adapters.safety_adapter import (
    SafetyAdapter,
    SafetyPOI,
    SafetyResult,
    get_safety_adapter,
)
from data.adapters.transport_adapter import (
    TransportAdapter,
    TransportResult,
    TransportStop,
    get_transport_adapter,
)

# Register built-in adapters
AdapterRegistry.register(OverpassAdapter)

__all__ = [
    # Base classes
    "ExternalSourceAdapter",
    "PortalFetchResult",
    "PortalFilter",
    "AdapterRegistry",
    "get_adapter",
    "register_adapter",
    # Built-in adapters
    "OverpassAdapter",
    "NeighborhoodAdapter",
    "AirQualityAdapter",
    "AirQualityResult",
    "AirQualityStation",
    "TransportAdapter",
    "TransportResult",
    "TransportStop",
    "NoiseAdapter",
    "NoiseResult",
    "NoiseSource",
    "SafetyAdapter",
    "SafetyPOI",
    "SafetyResult",
    # Adapter getters
    "get_neighborhood_adapter",
    "get_air_quality_adapter",
    "get_transport_adapter",
    "get_noise_adapter",
    "get_safety_adapter",
]
