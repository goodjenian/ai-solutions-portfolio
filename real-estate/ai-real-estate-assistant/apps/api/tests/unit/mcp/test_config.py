"""Tests for MCP configuration classes."""

import os
import pytest

from mcp.config import ConnectionPoolConfig, MCPEdition, MCPConnectorConfig


class TestMCPEdition:
    """Tests for MCPEdition enum."""

    def test_edition_values(self) -> None:
        """Test edition enum values."""
        assert MCPEdition.COMMUNITY.value == "community"
        assert MCPEdition.PRO.value == "pro"
        assert MCPEdition.ENTERPRISE.value == "enterprise"


class TestConnectionPoolConfig:
    """Tests for ConnectionPoolConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = ConnectionPoolConfig()

        assert config.max_connections == 10
        assert config.min_connections == 1
        assert config.connection_timeout_seconds == 30.0
        assert config.idle_timeout_seconds == 300.0
        assert config.max_lifetime_seconds == 3600.0

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = ConnectionPoolConfig(
            max_connections=20,
            min_connections=5,
            connection_timeout_seconds=60.0,
        )

        assert config.max_connections == 20
        assert config.min_connections == 5
        assert config.connection_timeout_seconds == 60.0


class TestMCPConnectorConfig:
    """Tests for MCPConnectorConfig dataclass."""

    def test_minimal_config(self) -> None:
        """Test minimal configuration with required fields."""
        config = MCPConnectorConfig(
            name="test_connector",
            display_name="Test Connector",
        )

        assert config.name == "test_connector"
        assert config.display_name == "Test Connector"
        assert config.endpoint is None
        assert config.api_key is None
        assert config.timeout_seconds == 30.0
        assert config.enabled is True
        assert config.allowlisted is False
        assert config.min_edition == MCPEdition.PRO

    def test_full_config(self) -> None:
        """Test full configuration with all fields."""
        pool_config = ConnectionPoolConfig(max_connections=15)
        config = MCPConnectorConfig(
            name="full_connector",
            display_name="Full Connector",
            endpoint="https://api.example.com",
            api_key="test-key",
            timeout_seconds=60.0,
            retry_count=5,
            allowlisted=True,
            min_edition=MCPEdition.COMMUNITY,
            supports_streaming=True,
            pool_config=pool_config,
            extra={"custom": "value"},
        )

        assert config.name == "full_connector"
        assert config.endpoint == "https://api.example.com"
        assert config.api_key == "test-key"
        assert config.timeout_seconds == 60.0
        assert config.retry_count == 5
        assert config.allowlisted is True
        assert config.min_edition == MCPEdition.COMMUNITY
        assert config.supports_streaming is True
        assert config.pool_config.max_connections == 15
        assert config.extra == {"custom": "value"}

    def test_is_available_for_edition(self) -> None:
        """Test edition availability check."""
        # Pro connector
        pro_config = MCPConnectorConfig(
            name="pro_connector",
            display_name="Pro Connector",
            min_edition=MCPEdition.PRO,
        )

        assert pro_config.is_available_for_edition(MCPEdition.COMMUNITY) is False
        assert pro_config.is_available_for_edition(MCPEdition.PRO) is True
        assert pro_config.is_available_for_edition(MCPEdition.ENTERPRISE) is True

        # Community connector
        ce_config = MCPConnectorConfig(
            name="ce_connector",
            display_name="CE Connector",
            min_edition=MCPEdition.COMMUNITY,
        )

        assert ce_config.is_available_for_edition(MCPEdition.COMMUNITY) is True
        assert ce_config.is_available_for_edition(MCPEdition.PRO) is True
        assert ce_config.is_available_for_edition(MCPEdition.ENTERPRISE) is True

    def test_is_accessible_in_ce(self) -> None:
        """Test CE accessibility check."""
        # Allowlisted community connector
        ce_allowed = MCPConnectorConfig(
            name="ce_allowed",
            display_name="CE Allowed",
            allowlisted=True,
            min_edition=MCPEdition.COMMUNITY,
        )
        assert ce_allowed.is_accessible_in_ce() is True

        # Non-allowlisted community connector
        ce_not_allowed = MCPConnectorConfig(
            name="ce_not_allowed",
            display_name="CE Not Allowed",
            allowlisted=False,
            min_edition=MCPEdition.COMMUNITY,
        )
        assert ce_not_allowed.is_accessible_in_ce() is False

        # Allowlisted but Pro connector
        pro_allowed = MCPConnectorConfig(
            name="pro_allowed",
            display_name="Pro Allowed",
            allowlisted=True,
            min_edition=MCPEdition.PRO,
        )
        assert pro_allowed.is_accessible_in_ce() is False

    def test_to_dict_excludes_api_key(self) -> None:
        """Test that to_dict excludes sensitive API key."""
        config = MCPConnectorConfig(
            name="test",
            display_name="Test",
            api_key="secret-key-123",
        )

        d = config.to_dict()

        assert "api_key" not in d
        assert d["has_api_key"] is True

    def test_api_key_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test loading API key from environment variable."""
        monkeypatch.setenv("TEST_API_KEY", "env-api-key-123")

        config = MCPConnectorConfig(
            name="test",
            display_name="Test",
            api_key_env_var="TEST_API_KEY",
        )

        assert config.api_key == "env-api-key-123"

    def test_api_key_env_not_set(self) -> None:
        """Test behavior when env var is not set."""
        config = MCPConnectorConfig(
            name="test",
            display_name="Test",
            api_key_env_var="NONEXISTENT_KEY",
        )

        assert config.api_key is None
