"""
OpenAI cost guard — per-client daily budget enforcement.

Features:
- Tracks token usage (input + output) per client per day
- Converts tokens to USD using configurable price table
- Warns at 80% of daily budget (BUDGET_WARNING_PCT)
- Hard-blocks at 100% (raises BudgetExceededError)
- Resets at midnight UTC

Usage:
    guard = CostGuard(daily_budget_usd=5.0)
    guard.check_and_record(client_id="abc", model="gpt-4o",
                           input_tokens=1200, output_tokens=800)
"""

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from .audit import get_audit_logger

logger = logging.getLogger("goodyseo.cost_guard")

# ── OpenAI pricing table (USD per 1M tokens) — update as prices change ───────
# Source: platform.openai.com/pricing  (March 2025)
_PRICE_TABLE: dict[str, dict[str, float]] = {
    "gpt-4o":               {"input": 2.50,  "output": 10.00},
    "gpt-4o-mini":          {"input": 0.15,  "output": 0.60},
    "gpt-4-turbo":          {"input": 10.00, "output": 30.00},
    "gpt-4":                {"input": 30.00, "output": 60.00},
    "gpt-3.5-turbo":        {"input": 0.50,  "output": 1.50},
    "gpt-3.5-turbo-0125":   {"input": 0.50,  "output": 1.50},
    "o1":                   {"input": 15.00, "output": 60.00},
    "o1-mini":              {"input": 3.00,  "output": 12.00},
    # Claude models (used via some tools)
    "claude-sonnet-4-6":    {"input": 3.00,  "output": 15.00},
    "claude-haiku-4-5":     {"input": 0.25,  "output": 1.25},
}
_DEFAULT_PRICE = {"input": 5.00, "output": 15.00}  # conservative fallback
_WARNING_PCT = 0.80


class BudgetExceededError(Exception):
    """Raised when a client's daily budget is exhausted."""
    def __init__(self, client_id: str, used: float, limit: float) -> None:
        self.client_id = client_id
        self.used = used
        self.limit = limit
        super().__init__(
            f"Daily budget exceeded for client {client_id[:6]}***. "
            f"Used: ${used:.4f} / Limit: ${limit:.2f}"
        )


@dataclass
class ClientUsage:
    date: str = ""              # YYYY-MM-DD UTC
    total_usd: float = 0.0
    total_tokens: int = 0
    run_count: int = 0
    warned: bool = False


class CostGuard:
    """
    Thread-safe per-client daily cost tracker.

    Args:
        daily_budget_usd: Hard limit in USD per client per day.
                          Set to 0 to disable (allow unlimited).
    """

    def __init__(self, daily_budget_usd: float = 5.0) -> None:
        self._budget = daily_budget_usd
        self._lock = threading.Lock()
        self._usage: dict[str, ClientUsage] = {}
        self._audit = get_audit_logger()

    @staticmethod
    def _today() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    @staticmethod
    def tokens_to_usd(model: str, input_tokens: int, output_tokens: int) -> float:
        prices = _PRICE_TABLE.get(model, _DEFAULT_PRICE)
        cost = (input_tokens * prices["input"] + output_tokens * prices["output"]) / 1_000_000
        return round(cost, 8)

    def check_and_record(
        self,
        client_id: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        tool_name: Optional[str] = None,
    ) -> float:
        """
        Record token usage and enforce budget.

        Returns: cost_usd for this call.
        Raises: BudgetExceededError if daily limit reached.
        """
        cost = self.tokens_to_usd(model, input_tokens, output_tokens)

        with self._lock:
            today = self._today()
            rec = self._usage.setdefault(client_id, ClientUsage())

            # Reset on new day
            if rec.date != today:
                rec.date = today
                rec.total_usd = 0.0
                rec.total_tokens = 0
                rec.run_count = 0
                rec.warned = False

            # Hard block
            if self._budget > 0 and rec.total_usd >= self._budget:
                self._audit.log_budget_event(
                    client_id=client_id,
                    tool=tool_name or model,
                    used_usd=rec.total_usd,
                    limit_usd=self._budget,
                    exceeded=True,
                )
                raise BudgetExceededError(client_id, rec.total_usd, self._budget)

            rec.total_usd += cost
            rec.total_tokens += input_tokens + output_tokens
            rec.run_count += 1

            # 80% warning (once per day)
            if (self._budget > 0
                    and not rec.warned
                    and rec.total_usd >= self._budget * _WARNING_PCT):
                rec.warned = True
                logger.warning(
                    "Budget warning: client %s... at %.1f%% of daily limit ($%.4f/$%.2f)",
                    client_id[:6], rec.total_usd / self._budget * 100,
                    rec.total_usd, self._budget,
                )
                self._audit.log_budget_event(
                    client_id=client_id,
                    tool=tool_name or model,
                    used_usd=rec.total_usd,
                    limit_usd=self._budget,
                    exceeded=False,
                )

        return cost

    def get_usage(self, client_id: str) -> dict:
        with self._lock:
            rec = self._usage.get(client_id, ClientUsage())
            return {
                "date": rec.date or self._today(),
                "total_usd": round(rec.total_usd, 6),
                "total_tokens": rec.total_tokens,
                "run_count": rec.run_count,
                "budget_usd": self._budget,
                "remaining_usd": max(0.0, round(self._budget - rec.total_usd, 6))
                    if self._budget > 0 else None,
                "pct_used": round(rec.total_usd / self._budget * 100, 1)
                    if self._budget > 0 else None,
            }

    def all_usage(self) -> dict[str, dict]:
        with self._lock:
            return {cid: self.get_usage(cid) for cid in self._usage}
