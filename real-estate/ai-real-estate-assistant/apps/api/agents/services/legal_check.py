from typing import Any, Dict, Protocol, runtime_checkable


@runtime_checkable
class LegalCheckService(Protocol):
    def analyze_contract(self, text: str) -> Dict[str, Any]: ...


class BasicLegalCheckService:
    def analyze_contract(self, text: str) -> Dict[str, Any]:
        return {"risks": [], "score": 0.0}
