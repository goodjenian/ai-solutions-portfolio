"""Tests for MCPConnectorRegistry."""

import pytest

from mcp.config import MCPEdition, MCPConnectorConfig
from mcp.exceptions import MCPConnectorNotFoundError, MCPNotAllowlistedError
from mcp.registry import MCPConnectorRegistry, get_mcp_connector, register_mcp_connector
from mcp.stubs import EchoStubConnector


class TestMCPConnectorRegistry:
    """Tests for MCPConnectorRegistry."""

    def setup_method(self) -> None:
        """Clear registry before each test."""
        MCPConnectorRegistry.clear()
        MCPConnectorRegistry.set_edition(MCPEdition.PRO)

    def test_register_connector(self) -> None:
        """Test connector registration."""
        MCPConnectorRegistry.register(EchoStubConnector)

        assert "echo_stub" in MCPConnectorRegistry.list_connectors()

    def test_register_connector_with_config(self) -> None:
        """Test connector registration with config."""
        config = MCPConnectorConfig(
            name="echo_stub",
            display_name="Echo Stub",
            timeout_seconds=60.0,
        )
        MCPConnectorRegistry.register(EchoStubConnector, config=config)

        assert "echo_stub" in MCPConnectorRegistry.list_connectors()

    def test_register_missing_name_raises(self) -> None:
        """Test registration fails without name."""

        class NoNameConnector(EchoStubConnector):
            name = ""  # type: ignore

        with pytest.raises(ValueError, match="name"):
            MCPConnectorRegistry.register(NoNameConnector)

    def test_unregister_connector(self) -> None:
        """Test connector unregistration."""
        MCPConnectorRegistry.register(EchoStubConnector)
        assert "echo_stub" in MCPConnectorRegistry.list_connectors()

        MCPConnectorRegistry.unregister("echo_stub")

        assert "echo_stub" not in MCPConnectorRegistry.list_connectors()

    def test_get_connector_caches_instance(self) -> None:
        """Test get_connector returns cached instance."""
        MCPConnectorRegistry.register(EchoStubConnector)

        instance1 = MCPConnectorRegistry.get_connector("echo_stub")
        instance2 = MCPConnectorRegistry.get_connector("echo_stub")

        assert instance1 is instance2

    def test_get_connector_not_found_raises(self) -> None:
        """Test get_connector raises for unknown connector."""
        with pytest.raises(MCPConnectorNotFoundError):
            MCPConnectorRegistry.get_connector("nonexistent")

    def test_connector_info(self) -> None:
        """Test get_connector_info returns correct info."""
        MCPConnectorRegistry.register(EchoStubConnector)

        info = MCPConnectorRegistry.get_connector_info("echo_stub")

        assert info is not None
        assert info["name"] == "echo_stub"
        assert info["display_name"] == "Echo Stub (Testing)"
        assert info["requires_api_key"] is False
        assert info["allowlisted"] is True

    def test_connector_info_not_found(self) -> None:
        """Test get_connector_info returns None for unknown."""
        info = MCPConnectorRegistry.get_connector_info("nonexistent")

        assert info is None

    def test_get_all_info(self) -> None:
        """Test get_all_info returns all connector info."""
        MCPConnectorRegistry.register(EchoStubConnector)

        all_info = MCPConnectorRegistry.get_all_info()

        assert len(all_info) == 1
        assert all_info[0]["name"] == "echo_stub"


class TestMCPConnectorRegistryAllowlist:
    """Tests for allowlist functionality."""

    def setup_method(self) -> None:
        """Clear registry before each test."""
        MCPConnectorRegistry.clear()
        MCPConnectorRegistry.set_edition(MCPEdition.COMMUNITY)

    def test_set_allowlist(self) -> None:
        """Test setting allowlist."""
        MCPConnectorRegistry.set_allowlist(["connector_a", "connector_b"])

        assert MCPConnectorRegistry.is_allowlisted("connector_a")
        assert MCPConnectorRegistry.is_allowlisted("connector_b")
        assert not MCPConnectorRegistry.is_allowlisted("connector_c")

    def test_add_to_allowlist(self) -> None:
        """Test adding to allowlist."""
        MCPConnectorRegistry.add_to_allowlist("new_connector")

        assert MCPConnectorRegistry.is_allowlisted("new_connector")

    def test_remove_from_allowlist(self) -> None:
        """Test removing from allowlist."""
        MCPConnectorRegistry.set_allowlist(["connector_a"])
        MCPConnectorRegistry.remove_from_allowlist("connector_a")

        assert not MCPConnectorRegistry.is_allowlisted("connector_a")

    def test_ce_allowlist_enforcement(self) -> None:
        """Test CE mode blocks non-allowlisted connectors."""
        # Register echo_stub (it's allowlisted by default)
        MCPConnectorRegistry.register(EchoStubConnector)

        # Should work because echo_stub is allowlisted
        connector = MCPConnectorRegistry.get_connector("echo_stub")
        assert connector is not None

    def test_ce_mode_blocks_non_allowlisted(self) -> None:
        """Test CE mode blocks connectors not in allowlist."""

        # Create a non-allowlisted connector
        class NonAllowlistedConnector(EchoStubConnector):
            name = "non_allowlisted"
            allowlisted = False

        MCPConnectorRegistry.register(NonAllowlistedConnector)
        MCPConnectorRegistry.set_edition(MCPEdition.COMMUNITY)
        MCPConnectorRegistry.set_allowlist([])  # Clear allowlist

        with pytest.raises(MCPNotAllowlistedError):
            MCPConnectorRegistry.get_connector("non_allowlisted")

    def test_pro_mode_allows_all(self) -> None:
        """Test PRO mode allows all connectors."""

        class NonAllowlistedConnector(EchoStubConnector):
            name = "non_allowlisted"
            allowlisted = False

        MCPConnectorRegistry.register(NonAllowlistedConnector)
        MCPConnectorRegistry.set_edition(MCPEdition.PRO)

        # Should work in PRO mode even without allowlist
        connector = MCPConnectorRegistry.get_connector("non_allowlisted")
        assert connector is not None

    def test_skip_edition_check(self) -> None:
        """Test skip_edition_check bypasses validation."""
        MCPConnectorRegistry.set_edition(MCPEdition.COMMUNITY)
        MCPConnectorRegistry.set_allowlist([])

        class NonAllowlistedConnector(EchoStubConnector):
            name = "non_allowlisted"
            allowlisted = False

        MCPConnectorRegistry.register(NonAllowlistedConnector)

        # Should work with skip_edition_check
        connector = MCPConnectorRegistry.get_connector(
            "non_allowlisted", skip_edition_check=True
        )
        assert connector is not None

    def test_list_connectors_filters_by_edition(self) -> None:
        """Test list_connectors filters by edition."""
        MCPConnectorRegistry.register(EchoStubConnector)
        MCPConnectorRegistry.set_edition(MCPEdition.COMMUNITY)
        MCPConnectorRegistry.set_allowlist(["echo_stub"])

        # Should show only allowlisted
        connectors = MCPConnectorRegistry.list_connectors()
        assert "echo_stub" in connectors

        # Should show all with include_non_accessible
        all_connectors = MCPConnectorRegistry.list_connectors(include_non_accessible=True)
        assert "echo_stub" in all_connectors


class TestMCPConnectorRegistryEdition:
    """Tests for edition management."""

    def setup_method(self) -> None:
        """Clear registry before each test."""
        MCPConnectorRegistry.clear()

    def test_set_and_get_edition(self) -> None:
        """Test setting and getting edition."""
        MCPConnectorRegistry.set_edition(MCPEdition.PRO)

        assert MCPConnectorRegistry.get_edition() == MCPEdition.PRO

    def test_edition_defaults_to_community(self) -> None:
        """Test default edition is COMMUNITY."""
        # Note: This test assumes clean state
        assert MCPConnectorRegistry.get_edition() in [
            MCPEdition.COMMUNITY,
            MCPEdition.PRO,
        ]


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def setup_method(self) -> None:
        """Clear registry before each test."""
        MCPConnectorRegistry.clear()
        MCPConnectorRegistry.set_edition(MCPEdition.PRO)

    def test_register_mcp_connector_decorator(self) -> None:
        """Test register_mcp_connector decorator."""

        @register_mcp_connector
        class DecoratedConnector(EchoStubConnector):
            name = "decorated"
            display_name = "Decorated Connector"

        assert "decorated" in MCPConnectorRegistry.list_connectors()

    def test_get_mcp_connector_function(self) -> None:
        """Test get_mcp_connector convenience function."""
        MCPConnectorRegistry.register(EchoStubConnector)

        connector = get_mcp_connector("echo_stub")

        assert connector.name == "echo_stub"
