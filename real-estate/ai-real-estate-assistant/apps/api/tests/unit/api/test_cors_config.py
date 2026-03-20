import os

import pytest

from config.settings import AppSettings


def test_dev_env_allows_all_origins():
    old_env = os.environ.get("ENVIRONMENT")
    try:
        os.environ["ENVIRONMENT"] = "development"
        if "CORS_ALLOW_ORIGINS" in os.environ:
            del os.environ["CORS_ALLOW_ORIGINS"]
        settings = AppSettings()
        assert settings.cors_allow_origins == ["*"]
    finally:
        if old_env is None:
            os.environ.pop("ENVIRONMENT", None)
        else:
            os.environ["ENVIRONMENT"] = old_env


def test_prod_env_pins_origins():
    old_env = os.environ.get("ENVIRONMENT")
    old_cors = os.environ.get("CORS_ALLOW_ORIGINS")
    try:
        os.environ["ENVIRONMENT"] = "production"
        os.environ["CORS_ALLOW_ORIGINS"] = "https://example.com, https://app.local"
        settings = AppSettings()
        assert settings.cors_allow_origins == ["https://example.com", "https://app.local"]
    finally:
        if old_env is None:
            os.environ.pop("ENVIRONMENT", None)
        else:
            os.environ["ENVIRONMENT"] = old_env
        if old_cors is None:
            os.environ.pop("CORS_ALLOW_ORIGINS", None)
        else:
            os.environ["CORS_ALLOW_ORIGINS"] = old_cors


def test_production_rejects_wildcard_cors_origins():
    """Production environment should reject wildcard '*' in CORS_ALLOW_ORIGINS."""
    old_env = os.environ.get("ENVIRONMENT")
    old_cors = os.environ.get("CORS_ALLOW_ORIGINS")
    try:
        os.environ["ENVIRONMENT"] = "production"
        os.environ["CORS_ALLOW_ORIGINS"] = "*"
        with pytest.raises(ValueError) as exc_info:
            AppSettings()
        assert "cannot contain wildcard '*'" in str(exc_info.value).lower()
    finally:
        if old_env is None:
            os.environ.pop("ENVIRONMENT", None)
        else:
            os.environ["ENVIRONMENT"] = old_env
        if old_cors is None:
            os.environ.pop("CORS_ALLOW_ORIGINS", None)
        else:
            os.environ["CORS_ALLOW_ORIGINS"] = old_cors


def test_production_rejects_wildcard_in_list_of_cors_origins():
    """Production environment should reject even if wildcard is in a list of origins."""
    old_env = os.environ.get("ENVIRONMENT")
    old_cors = os.environ.get("CORS_ALLOW_ORIGINS")
    try:
        os.environ["ENVIRONMENT"] = "production"
        os.environ["CORS_ALLOW_ORIGINS"] = "https://example.com, *, https://app.local"
        with pytest.raises(ValueError) as exc_info:
            AppSettings()
        assert "cannot contain wildcard '*'" in str(exc_info.value).lower()
    finally:
        if old_env is None:
            os.environ.pop("ENVIRONMENT", None)
        else:
            os.environ["ENVIRONMENT"] = old_env
        if old_cors is None:
            os.environ.pop("CORS_ALLOW_ORIGINS", None)
        else:
            os.environ["CORS_ALLOW_ORIGINS"] = old_cors


def test_production_rejects_empty_cors_origins():
    """Production environment should reject empty CORS_ALLOW_ORIGINS."""
    old_env = os.environ.get("ENVIRONMENT")
    old_cors = os.environ.get("CORS_ALLOW_ORIGINS")
    try:
        os.environ["ENVIRONMENT"] = "production"
        if "CORS_ALLOW_ORIGINS" in os.environ:
            del os.environ["CORS_ALLOW_ORIGINS"]
        with pytest.raises(ValueError) as exc_info:
            AppSettings()
        assert "must be set" in str(exc_info.value).lower()
    finally:
        if old_env is None:
            os.environ.pop("ENVIRONMENT", None)
        else:
            os.environ["ENVIRONMENT"] = old_env
        if old_cors is None:
            os.environ.pop("CORS_ALLOW_ORIGINS", None)
        else:
            os.environ["CORS_ALLOW_ORIGINS"] = old_cors


def test_production_accepts_specific_cors_origins():
    """Production environment should accept specific, non-wildcard origins."""
    old_env = os.environ.get("ENVIRONMENT")
    old_cors = os.environ.get("CORS_ALLOW_ORIGINS")
    try:
        os.environ["ENVIRONMENT"] = "production"
        os.environ["CORS_ALLOW_ORIGINS"] = (
            "https://example.com, https://app.local, https://api.example.com"
        )
        settings = AppSettings()
        assert settings.cors_allow_origins == [
            "https://example.com",
            "https://app.local",
            "https://api.example.com",
        ]
    finally:
        if old_env is None:
            os.environ.pop("ENVIRONMENT", None)
        else:
            os.environ["ENVIRONMENT"] = old_env
        if old_cors is None:
            os.environ.pop("CORS_ALLOW_ORIGINS", None)
        else:
            os.environ["CORS_ALLOW_ORIGINS"] = old_cors


def test_development_allows_wildcard_cors_origins():
    """Development environment should allow wildcard CORS origins."""
    old_env = os.environ.get("ENVIRONMENT")
    old_cors = os.environ.get("CORS_ALLOW_ORIGINS")
    try:
        os.environ["ENVIRONMENT"] = "development"
        os.environ["CORS_ALLOW_ORIGINS"] = "*"
        settings = AppSettings()
        assert settings.cors_allow_origins == ["*"]
    finally:
        if old_env is None:
            os.environ.pop("ENVIRONMENT", None)
        else:
            os.environ["ENVIRONMENT"] = old_env
        if old_cors is None:
            os.environ.pop("CORS_ALLOW_ORIGINS", None)
        else:
            os.environ["CORS_ALLOW_ORIGINS"] = old_cors


def test_staging_env_allows_wildcard_cors_origins():
    """Staging environment allows wildcard CORS origins (only production is restrictive)."""
    old_env = os.environ.get("ENVIRONMENT")
    old_cors = os.environ.get("CORS_ALLOW_ORIGINS")
    try:
        os.environ["ENVIRONMENT"] = "staging"
        os.environ["CORS_ALLOW_ORIGINS"] = "*"
        # Staging is not production, so wildcard is allowed (uses default behavior)
        settings = AppSettings()
        assert settings.cors_allow_origins == ["*"]
    finally:
        if old_env is None:
            os.environ.pop("ENVIRONMENT", None)
        else:
            os.environ["ENVIRONMENT"] = old_env
        if old_cors is None:
            os.environ.pop("CORS_ALLOW_ORIGINS", None)
        else:
            os.environ["CORS_ALLOW_ORIGINS"] = old_cors
