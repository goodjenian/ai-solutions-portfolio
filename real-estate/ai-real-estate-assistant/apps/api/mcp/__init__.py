"""
MCP Connector Interface Package.

This package provides the standard connector interface for external tools
and data sources following the Model Context Protocol (MCP) pattern.

Usage:
    from mcp import MCPConnector, MCPConnectorConfig, MCPConnectorRegistry

    # Register a custom connector
    @register_mcp_connector
    class MyConnector(MCPConnector):
        name = "my_connector"
        ...

    # Get a connector instance
    connector = get_mcp_connector("my_connector")
    result = await connector.execute("query", {"param": "value"})

Community Edition Notes:
    - Only allowlisted connectors are available
    - Data minimization is enabled by default
    - No PII egress without explicit consent
"""

from mcp.base import MCPConnector
from mcp.config import (
    ConnectionPoolConfig,
    MCPConnectorConfig,
    MCPEdition,
)
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
from mcp.registry import (
    MCPConnectorRegistry,
    get_mcp_connector,
    register_mcp_connector,
)
from mcp.result import MCPConnectorResult
from mcp.stubs import EchoStubConnector

__all__ = [
    # Base classes
    "MCPConnector",
    # Configuration
    "MCPConnectorConfig",
    "ConnectionPoolConfig",
    "MCPEdition",
    # Results
    "MCPConnectorResult",
    # Registry
    "MCPConnectorRegistry",
    "register_mcp_connector",
    "get_mcp_connector",
    # Exceptions
    "MCPError",
    "MCPConnectionError",
    "MCPTimeoutError",
    "MCPAuthenticationError",
    "MCPNotAllowlistedError",
    "MCPConnectorNotFoundError",
    "MCPConfigError",
    "MCPOperationError",
    "MCPConnectionPoolExhaustedError",
    # Stubs
    "EchoStubConnector",
]
