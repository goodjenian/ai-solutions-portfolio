"""
Base classes for the Rule Engine.
"""

from abc import ABC, abstractmethod
from typing import Any, List, Optional

from pydantic import BaseModel


class RuleViolation(BaseModel):
    rule_id: str
    message: str
    severity: str  # "error", "warning", "info"
    file_path: Optional[str] = None
    line_number: Optional[int] = None


class BaseRule(ABC):
    """Abstract base class for all rules."""

    def __init__(self, rule_id: str, name: str, description: str, severity: str = "error"):
        self.rule_id = rule_id
        self.name = name
        self.description = description
        self.severity = severity

    @abstractmethod
    def check(self, context: Any) -> List[RuleViolation]:
        """
        Check if the rule is violated.

        Args:
            context: The context to check (e.g., file content, AST, etc.)

        Returns:
            List of violations.
        """
        pass
