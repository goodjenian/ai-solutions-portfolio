"""
MCP connector configuration dataclass.

This module defines configuration structures for MCP connectors,
including endpoint settings, authentication, and allowlist management.
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class MCPEdition(Enum):
    """Edition types for MCP connector access control."""

    COMMUNITY = "community"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass
class ConnectionPoolConfig:
    """
    Configuration for connection pooling.

    Attributes:
        max_connections: Maximum number of connections in the pool
        min_connections: Minimum number of idle connections to maintain
        connection_timeout_seconds: Timeout for acquiring a connection
        idle_timeout_seconds: Time before idle connections are closed
        max_lifetime_seconds: Maximum lifetime of a connection
    """

    max_connections: int = 10
    min_connections: int = 1
    connection_timeout_seconds: float = 30.0
    idle_timeout_seconds: float = 300.0
    max_lifetime_seconds: float = 3600.0


@dataclass
class MCPConnectorConfig:
    """
    Configuration for an MCP connector instance.

    Attributes:
        name: Unique identifier for the connector (e.g., 'google-maps', 'stripe')
        display_name: Human-readable name for UI display
        endpoint: Base URL or connection string for the service
        api_key: Optional API key for authentication (loaded from env)
        api_key_env_var: Environment variable name for the API key
        timeout_seconds: Request timeout in seconds
        retry_count: Number of retry attempts for transient failures
        retry_delay_seconds: Base delay between retries (exponential backoff)
        enabled: Whether this connector is enabled
        allowlisted: Whether this connector is in the CE allowlist
        min_edition: Minimum edition required to use this connector
        supports_streaming: Whether the connector supports streaming responses
        data_minimization_enabled: Whether to strip PII from requests
        pool_config: Connection pooling configuration
        extra: Additional connector-specific configuration
    """

    name: str
    display_name: str
    endpoint: Optional[str] = None
    api_key: Optional[str] = None
    api_key_env_var: Optional[str] = None
    timeout_seconds: float = 30.0
    retry_count: int = 3
    retry_delay_seconds: float = 1.0
    enabled: bool = True
    allowlisted: bool = False
    min_edition: MCPEdition = MCPEdition.PRO
    supports_streaming: bool = False
    data_minimization_enabled: bool = True
    pool_config: ConnectionPoolConfig = field(default_factory=ConnectionPoolConfig)
    extra: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate and load API key from environment if needed."""
        if not self.api_key and self.api_key_env_var:
            self.api_key = os.getenv(self.api_key_env_var)

    def is_available_for_edition(self, edition: MCPEdition) -> bool:
        """Check if connector is available for the given edition."""
        edition_order = {
            MCPEdition.COMMUNITY: 0,
            MCPEdition.PRO: 1,
            MCPEdition.ENTERPRISE: 2,
        }
        return edition_order.get(edition, 0) >= edition_order.get(self.min_edition, 1)

    def is_accessible_in_ce(self) -> bool:
        """Check if connector is accessible in Community Edition."""
        return self.allowlisted and self.min_edition == MCPEdition.COMMUNITY

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary (excluding sensitive data)."""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "endpoint": self.endpoint,
            "has_api_key": bool(self.api_key),
            "timeout_seconds": self.timeout_seconds,
            "enabled": self.enabled,
            "allowlisted": self.allowlisted,
            "min_edition": self.min_edition.value,
            "supports_streaming": self.supports_streaming,
            "data_minimization_enabled": self.data_minimization_enabled,
        }
