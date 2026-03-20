"""
Configuration for RuleEngine.
"""

from typing import List

# Files or path substrings to ignore during validation
IGNORE_PATTERNS: List[str] = [
    "i18n/translations.py",
    "notifications/email_templates.py",
]

# Maximum allowed line length
MAX_LINE_LENGTH: int = 120
