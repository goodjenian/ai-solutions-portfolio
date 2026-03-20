"""Tests for cache-related settings (TASK-017: Production Deployment Optimization)."""

import os
from unittest.mock import patch

from config.settings import AppSettings


class TestCacheSettings:
    """Tests for Response Cache configuration settings."""

    @patch.dict(os.environ, {}, clear=True)
    def test_default_cache_settings(self, monkeypatch):
        """Test that cache settings have correct default values."""
        settings = AppSettings()
        assert settings.cache_enabled is True
        assert settings.cache_ttl_seconds == 300
        assert settings.cache_prefix == "api_cache"

    @patch.dict(os.environ, {"CACHE_ENABLED": "false"})
    def test_cache_enabled_can_be_disabled(self, monkeypatch):
        """Test that cache can be disabled via environment variable."""
        settings = AppSettings()
        assert settings.cache_enabled is False

    @patch.dict(os.environ, {"CACHE_ENABLED": "0"})
    def test_cache_disabled_with_zero(self, monkeypatch):
        """Test that cache disabled with '0' value."""
        settings = AppSettings()
        assert settings.cache_enabled is False

    @patch.dict(os.environ, {"CACHE_TTL_SECONDS": "600"})
    def test_cache_ttl_seconds_from_env(self, monkeypatch):
        """Test that TTL can be configured via environment variable."""
        settings = AppSettings()
        assert settings.cache_ttl_seconds == 600

    @patch.dict(os.environ, {"CACHE_PREFIX": "custom_cache"})
    def test_cache_prefix_from_env(self, monkeypatch):
        """Test that cache prefix can be configured via environment variable."""
        settings = AppSettings()
        assert settings.cache_prefix == "custom_cache"

    @patch.dict(os.environ, {"CACHE_MAX_MEMORY_MB": "200"})
    def test_cache_max_memory_mb_from_env(self, monkeypatch):
        """Test that max memory can be configured via environment variable."""
        settings = AppSettings()
        assert settings.cache_max_memory_mb == 200

    @patch.dict(os.environ, {"CACHE_STALE_WHILE_REVALIDATE": "true"})
    def test_cache_stale_while_revalidate_from_env(self, monkeypatch):
        """Test that stale-while-revalidate can be enabled via environment variable."""
        settings = AppSettings()
        assert settings.cache_stale_while_revalidate is True

    @patch.dict(os.environ, {"CACHE_REDIS_URL": "redis://localhost:6380"})
    def test_cache_redis_url_from_env(self, monkeypatch):
        """Test that Redis URL can be configured via environment variable."""
        settings = AppSettings()
        assert settings.cache_redis_url == "redis://localhost:6380"


class TestMetricsSettings:
    """Tests for Metrics configuration settings (TASK-017)."""

    @patch.dict(os.environ, {}, clear=True)
    def test_default_metrics_settings(self, monkeypatch):
        """Test that metrics settings have correct default values."""
        settings = AppSettings()
        assert settings.metrics_enabled is True

    @patch.dict(os.environ, {"METRICS_ENABLED": "false"})
    def test_metrics_can_be_disabled(self, monkeypatch):
        """Test that metrics can be disabled via environment variable."""
        settings = AppSettings()
        assert settings.metrics_enabled is False
