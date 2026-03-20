"""
Internationalization (i18n) module for AI Real Estate Assistant.
"""

from .translations import (
    LANGUAGES,
    TRANSLATIONS,
    get_available_languages,
    get_language_name,
    get_text,
)

__all__ = ["get_text", "get_language_name", "get_available_languages", "LANGUAGES", "TRANSLATIONS"]
