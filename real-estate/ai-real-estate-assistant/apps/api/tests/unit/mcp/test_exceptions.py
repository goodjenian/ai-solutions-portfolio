"""Tests for MCP exceptions."""

import pytest

from mcp.exceptions import (
    MCPAuthenticationError,
    MCPConfigError,
    MCPConnectionError,
    MCPConnectionPoolExhaustedError,
    MCPConnectorNotFoundError,
    MCPError,
    MCPNotAllowlistedError,
    MCPOperationError,
    MCPTimeoutError,
)


class TestMCPError:
    """Tests for base MCPError."""

    def test_basic_error(self) -> None:
        """Test basic error creation."""
        error = MCPError("Something went wrong")

        assert str(error) == "Something went wrong"
        assert error.connector_name is None
        assert error.details == {}

    def test_error_with_connector_name(self) -> None:
        """Test error with connector name."""
        error = MCPError("Error occurred", connector_name="test_connector")

        assert error.connector_name == "test_connector"

    def test_error_with_details(self) -> None:
        """Test error with details."""
        error = MCPError(
            "Error occurred",
            connector_name="test",
            details={"status_code": 500, "retry_after": 30},
        )

        assert error.details["status_code"] == 500
        assert error.details["retry_after"] == 30


class TestMCPNotAllowlistedError:
    """Tests for MCPNotAllowlistedError."""

    def test_error_message(self) -> None:
        """Test error message format."""
        error = MCPNotAllowlistedError("premium_connector", "community")

        assert "premium_connector" in str(error)
        assert "community" in str(error)
        assert "Upgrade to Pro" in str(error)
        assert error.connector_name == "premium_connector"
        assert error.edition == "community"


class TestMCPConnectorNotFoundError:
    """Tests for MCPConnectorNotFoundError."""

    def test_error_message(self) -> None:
        """Test error message format."""
        error = MCPConnectorNotFoundError("nonexistent_connector")

        assert "nonexistent_connector" in str(error)
        assert "not found" in str(error)
        assert error.connector_name == "nonexistent_connector"


class TestExceptionInheritance:
    """Tests for exception inheritance."""

    def test_all_inherit_from_mcp_error(self) -> None:
        """Test all exceptions inherit from MCPError."""
        exceptions = [
            MCPConnectionError("test"),
            MCPTimeoutError("test"),
            MCPAuthenticationError("test"),
            MCPNotAllowlistedError("test"),
            MCPConnectorNotFoundError("test"),
            MCPConfigError("test"),
            MCPOperationError("test"),
            MCPConnectionPoolExhaustedError("test"),
        ]

        for exc in exceptions:
            assert isinstance(exc, MCPError)
            assert isinstance(exc, Exception)
