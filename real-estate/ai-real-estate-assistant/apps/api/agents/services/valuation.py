from typing import Any, Dict, Protocol, runtime_checkable


@runtime_checkable
class ValuationProvider(Protocol):
    def estimate_value(self, property_data: Dict[str, Any]) -> float: ...


class SimpleValuationProvider:
    def estimate_value(self, property_data: Dict[str, Any]) -> float:
        area = float(property_data.get("area", 0) or 0)
        price_per_sqm = float(property_data.get("price_per_sqm", 0) or 0)
        value = area * price_per_sqm
        return float(value)
