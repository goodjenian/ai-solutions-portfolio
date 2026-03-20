"""
Rule definitions for Code Quality, Security, and Performance.
"""

import re
from typing import Any, Dict, List

from .base import BaseRule, RuleViolation


class LineLengthRule(BaseRule):
    def __init__(self, max_length: int = 100):
        super().__init__("Q001", "Line Length", "Lines should not exceed max length", "warning")
        self.max_length = max_length

    def check(self, context: Dict[str, Any]) -> List[RuleViolation]:
        violations = []
        content = context.get("content", "")
        file_path = context.get("file_path", "")

        for i, line in enumerate(content.splitlines()):
            if len(line) > self.max_length:
                violations.append(
                    RuleViolation(
                        rule_id=self.rule_id,
                        message=f"Line too long ({len(line)} > {self.max_length})",
                        severity=self.severity,
                        file_path=file_path,
                        line_number=i + 1,
                    )
                )
        return violations


class NoSecretsRule(BaseRule):
    def __init__(self):
        super().__init__("S001", "No Secrets", "No hardcoded secrets allowed", "error")
        self.patterns = [
            r"API_KEY\s*=\s*['\"][a-zA-Z0-9_\-]{20,}['\"]",
            r"PASSWORD\s*=\s*['\"][^'\"]{8,}['\"]",
        ]

    def check(self, context: Dict[str, Any]) -> List[RuleViolation]:
        violations = []
        content = context.get("content", "")
        file_path = context.get("file_path", "")

        for i, line in enumerate(content.splitlines()):
            for pattern in self.patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    violations.append(
                        RuleViolation(
                            rule_id=self.rule_id,
                            message="Potential secret found",
                            severity=self.severity,
                            file_path=file_path,
                            line_number=i + 1,
                        )
                    )
        return violations


class PerformanceLoopRule(BaseRule):
    def __init__(self):
        super().__init__(
            "P001", "Efficient Loops", "Avoid string concatenation in loops", "warning"
        )

    def check(self, context: Dict[str, Any]) -> List[RuleViolation]:
        violations = []
        content = context.get("content", "")
        file_path = context.get("file_path", "")

        pattern = re.compile(
            r"(?m)^(?:\\s*)(for|while)\\s.*:\\s*(?:\\r?\\n)(?:[ \\t].*\\r?\\n)*[ \\t].*\\+=.*"
        )
        if pattern.search(content):
            violations.append(
                RuleViolation(
                    rule_id=self.rule_id,
                    message="Possible inefficient string concatenation in loop",
                    severity=self.severity,
                    file_path=file_path,
                )
            )
        return violations
