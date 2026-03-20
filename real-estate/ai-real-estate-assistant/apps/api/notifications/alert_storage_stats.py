from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


@dataclass(frozen=True)
class AlertStorageSummary:
    sent_total: int
    pending_total: int
    pending_by_type: Dict[str, int]
    pending_oldest_created_at: Optional[datetime]
    pending_newest_created_at: Optional[datetime]


def load_alert_storage_summary(storage_path: str) -> AlertStorageSummary:
    root = Path(storage_path)
    sent_alerts_path = root / "sent_alerts.json"
    pending_alerts_path = root / "pending_alerts.json"

    sent_total = 0
    if sent_alerts_path.exists():
        try:
            sent_data = json.loads(sent_alerts_path.read_text(encoding="utf-8"))
            sent_total = len(sent_data.get("alerts", []) or [])
        except Exception:
            sent_total = 0

    pending_by_type: Dict[str, int] = {}
    created_at_values: list[datetime] = []
    pending_total = 0

    if pending_alerts_path.exists():
        try:
            pending_data = json.loads(pending_alerts_path.read_text(encoding="utf-8"))
            pending_alerts = pending_data.get("alerts", []) or []
            pending_total = len(pending_alerts)
            for raw in pending_alerts:
                if not isinstance(raw, dict):
                    continue
                alert_type = raw.get("alert_type") or "unknown"
                pending_by_type[str(alert_type)] = pending_by_type.get(str(alert_type), 0) + 1

                created_at_raw = raw.get("created_at")
                if not created_at_raw:
                    continue
                try:
                    created_at_values.append(datetime.fromisoformat(str(created_at_raw)))
                except Exception:
                    continue
        except Exception:
            pending_total = 0

    oldest = min(created_at_values) if created_at_values else None
    newest = max(created_at_values) if created_at_values else None

    return AlertStorageSummary(
        sent_total=sent_total,
        pending_total=pending_total,
        pending_by_type=pending_by_type,
        pending_oldest_created_at=oldest,
        pending_newest_created_at=newest,
    )
