from typing import Any, Dict, Protocol, runtime_checkable


@runtime_checkable
class DataEnrichmentService(Protocol):
    def enrich(self, address: str) -> Dict[str, Any]: ...


class BasicDataEnrichmentService:
    def enrich(self, address: str) -> Dict[str, Any]:
        return {}
