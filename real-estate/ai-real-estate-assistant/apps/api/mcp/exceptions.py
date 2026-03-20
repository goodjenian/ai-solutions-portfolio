"""
Custom exceptions for MCP connector operations.

This module defines exception types for MCP-specific error conditions.
"""

from typing import Any, Dict, Optional


class MCPError(Exception):
    """Base exception for MCP-related errors."""

    def __init__(
        self,
        message: str,
        connector_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.connector_name = connector_name
        self.details = details or {}


class MCPConnectionError(MCPError):
    """Raised when connection to MCP service fails."""
    pass


class MCPTimeoutError(MCPError):
    """Raised when an MCP operation times out."""
    pass


class MCPAuthenticationError(MCPError):
    """Raised when authentication with MCP service fails."""
    pass


class MCPNotAllowlistedError(MCPError):
    """
    Raised when attempting to use a non-allowlisted connector in CE.

    This enforces the edition-based access control for connectors.
    """

    def __init__(
        self,
        connector_name: str,
        edition: str = "community",
    ) -> None:
        message = (
            f"Connector '{connector_name}' is not available in {edition} edition. "
            f"Upgrade to Pro or add to allowlist."
        )
        super().__init__(message, connector_name=connector_name)
        self.edition = edition


class MCPConnectorNotFoundError(MCPError):
    """Raised when a requested connector is not registered."""

    def __init__(self, connector_name: str) -> None:
        message = f"Connector '{connector_name}' not found in registry"
        super().__init__(message, connector_name=connector_name)


class MCPConfigError(MCPError):
    """Raised when connector configuration is invalid."""
    pass


class MCPOperationError(MCPError):
    """Raised when an MCP operation fails during execution."""
    pass


class MCPConnectionPoolExhaustedError(MCPError):
    """Raised when connection pool has no available connections."""
    pass
