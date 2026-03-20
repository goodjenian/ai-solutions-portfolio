"""
Audit logging — thread-safe, daily-rotating CSV + structured log.
Adapted from ai-real-estate-assistant (MIT).
"""

import csv
import hashlib
import logging
import os
import threading
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field


class AuditEventType(str, Enum):
    AUTH_SUCCESS = "auth.success"
    AUTH_FAILURE = "auth.failure"
    RATE_LIMITED = "security.rate_limit"
    BUDGET_EXCEEDED = "security.budget_exceeded"
    BUDGET_WARNING = "security.budget_warning"
    AI_RUN = "ai.run"
    AI_ERROR = "ai.error"
    API_REQUEST = "api.request"


class AuditLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class AuditEvent(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    event_type: AuditEventType
    level: AuditLevel
    client_id: Optional[str] = None   # hashed — never raw key
    resource: Optional[str] = None
    action: Optional[str] = None
    result: str
    request_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class AuditLogger:
    _CSV_HEADERS = [
        "timestamp", "event_type", "level", "client_id",
        "resource", "action", "result", "request_id", "metadata",
    ]

    def __init__(self, log_dir: Optional[Path] = None) -> None:
        enabled_raw = os.getenv("AUDIT_LOGGING_ENABLED", "true").strip().lower()
        self._enabled = enabled_raw in {"1", "true", "yes", "on"}

        if log_dir is None:
            log_dir = Path(os.getenv("AUDIT_LOG_DIR", "data/audit"))
        self._log_dir = Path(log_dir)
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._log_file: Optional[Path] = None
        self._rotate()
        self._logger = logging.getLogger("goodyseo.audit")

    def _rotate(self) -> None:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        new_file = self._log_dir / f"audit_{today}.csv"
        if new_file != self._log_file:
            self._log_file = new_file
            if not self._log_file.exists():
                with open(self._log_file, "w", newline="", encoding="utf-8") as f:
                    csv.writer(f).writerow(self._CSV_HEADERS)

    @staticmethod
    def _hash(value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        return hashlib.sha256(value.encode()).hexdigest()[:16]

    def log(self, event: AuditEvent) -> None:
        if not self._enabled:
            return
        with self._lock:
            try:
                self._rotate()
                with open(self._log_file, "a", newline="", encoding="utf-8") as f:  # type: ignore[arg-type]
                    csv.writer(f).writerow([
                        event.timestamp,
                        event.event_type,
                        event.level,
                        self._hash(event.client_id) or "",
                        event.resource or "",
                        event.action or "",
                        event.result,
                        event.request_id or "",
                        str(event.metadata),
                    ])
            except Exception as e:
                self._logger.error("Audit write failed: %s", e)

        level_map = {
            AuditLevel.CRITICAL: self._logger.critical,
            AuditLevel.HIGH: self._logger.warning,
            AuditLevel.MEDIUM: self._logger.info,
            AuditLevel.LOW: self._logger.debug,
        }
        level_map.get(event.level, self._logger.info)(  # type: ignore[call-arg]
            event.event_type,
            extra={"audit": True, **event.metadata},
        )

    # ── convenience helpers ──────────────────────────────────────────────────

    def log_auth_success(self, client_id: str, request_id: Optional[str] = None) -> None:
        self.log(AuditEvent(
            event_type=AuditEventType.AUTH_SUCCESS, level=AuditLevel.MEDIUM,
            client_id=client_id, result="success", request_id=request_id,
        ))

    def log_auth_failure(self, reason: str, request_id: Optional[str] = None,
                         path: Optional[str] = None) -> None:
        self.log(AuditEvent(
            event_type=AuditEventType.AUTH_FAILURE, level=AuditLevel.HIGH,
            resource=path, result="failure", request_id=request_id,
            metadata={"reason": reason},
        ))

    def log_ai_run(self, tool: str, client_id: str, tokens: int,
                   cost_usd: float, duration_s: float,
                   request_id: Optional[str] = None) -> None:
        self.log(AuditEvent(
            event_type=AuditEventType.AI_RUN, level=AuditLevel.LOW,
            client_id=client_id, resource=tool, action="run",
            result="success", request_id=request_id,
            metadata={"tokens": tokens, "cost_usd": round(cost_usd, 6),
                      "duration_s": round(duration_s, 2)},
        ))

    def log_budget_event(self, client_id: str, tool: str, used_usd: float,
                         limit_usd: float, exceeded: bool) -> None:
        self.log(AuditEvent(
            event_type=AuditEventType.BUDGET_EXCEEDED if exceeded else AuditEventType.BUDGET_WARNING,
            level=AuditLevel.HIGH if exceeded else AuditLevel.MEDIUM,
            client_id=client_id, resource=tool,
            result="blocked" if exceeded else "warning",
            metadata={"used_usd": round(used_usd, 4), "limit_usd": limit_usd,
                      "pct": round(used_usd / limit_usd * 100, 1) if limit_usd else 0},
        ))


# ── singleton ────────────────────────────────────────────────────────────────

_instance: Optional[AuditLogger] = None
_lock = threading.Lock()


def get_audit_logger() -> AuditLogger:
    global _instance
    with _lock:
        if _instance is None:
            _instance = AuditLogger()
        return _instance
