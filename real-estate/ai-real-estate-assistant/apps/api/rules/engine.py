"""
Engine to execute rules.
"""

from typing import List

from .base import BaseRule, RuleViolation
from .config import IGNORE_PATTERNS, MAX_LINE_LENGTH
from .definitions import LineLengthRule, NoSecretsRule, PerformanceLoopRule


class RuleEngine:
    def __init__(self):
        self.rules: List[BaseRule] = [
            LineLengthRule(max_length=MAX_LINE_LENGTH),
            NoSecretsRule(),
            PerformanceLoopRule(),
        ]

    def add_rule(self, rule: BaseRule):
        self.rules.append(rule)

    def validate_code(self, content: str, file_path: str = "unknown") -> List[RuleViolation]:
        context = {"content": content, "file_path": file_path}
        violations = []
        for rule in self.rules:
            violations.extend(rule.check(context))
        return violations

    def validate_file(self, file_path: str) -> List[RuleViolation]:
        try:
            for pat in IGNORE_PATTERNS:
                if pat in file_path.replace("\\", "/"):
                    return []
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return self.validate_code(content, file_path)
        except Exception as e:
            return [
                RuleViolation(
                    rule_id="SYS001",
                    message=f"Could not read file: {e}",
                    severity="error",
                    file_path=file_path,
                )
            ]
