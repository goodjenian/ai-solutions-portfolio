from typing import Any, Dict, Protocol, runtime_checkable
import requests


@runtime_checkable
class CRMConnector(Protocol):
    def create_deal(self, payload: Dict[str, Any]) -> str: ...

    def create_task(self, payload: Dict[str, Any]) -> str: ...

    def sync_contact(self, contact: Dict[str, Any]) -> str: ...


class WebhookCRMConnector:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def create_deal(self, payload: Dict[str, Any]) -> str:
        r = requests.post(f"{self.webhook_url}/deal", json=payload, timeout=10)
        r.raise_for_status()
        data = r.json()
        return str(data.get("id", ""))

    def create_task(self, payload: Dict[str, Any]) -> str:
        r = requests.post(f"{self.webhook_url}/task", json=payload, timeout=10)
        r.raise_for_status()
        data = r.json()
        return str(data.get("id", ""))

    def sync_contact(self, contact: Dict[str, Any]) -> str:
        r = requests.post(f"{self.webhook_url}/contact", json=contact, timeout=10)
        r.raise_for_status()
        data = r.json()
        return str(data.get("id", ""))
