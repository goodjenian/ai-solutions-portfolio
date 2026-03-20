"""
Echo stub connector for deterministic testing.

This module provides a stub MCP connector that echoes back input,
useful for unit testing without network dependencies.
"""

import asyncio
from typing import Any, AsyncGenerator, Dict, Optional

from mcp.base import MCPConnector
from mcp.config import MCPConnectorConfig, MCPEdition
from mcp.result import MCPConnectorResult


class EchoStubConnector(MCPConnector[Dict[str, Any]]):
    """
    Deterministic stub connector for testing.

    Echoes back the operation and params in the result data.
    Never makes network calls - safe for unit tests.

    Attributes:
        name: Always "echo_stub"
        display_name: "Echo Stub (Testing)"
        allowlisted: True (available in CE for testing)
        min_edition: COMMUNITY
    """

    name = "echo_stub"
    display_name = "Echo Stub (Testing)"
    description = "Deterministic stub connector for unit testing"
    requires_api_key = False
    allowlisted = True
    min_edition = MCPEdition.COMMUNITY
    supports_streaming = True

    def __init__(
        self,
        config: Optional[MCPConnectorConfig] = None,
        latency_ms: float = 0.0,
        fail_next: bool = False,
    ) -> None:
        """
        Initialize the echo stub.

        Args:
            config: Optional configuration
            latency_ms: Simulated latency in milliseconds
            fail_next: If True, next execute() will fail
        """
        # Skip parent validation since we don't require API key
        self._config = config or self._create_default_config()
        self._connected = False
        self._connection_pool = None
        self._latency_ms = latency_ms
        self._fail_next = fail_next
        self._call_count = 0

    async def connect(self) -> bool:
        """Simulate connection (always succeeds)."""
        # Simulate latency if configured
        if self._latency_ms > 0:
            await asyncio.sleep(self._latency_ms / 1000)
        self._connected = True
        return True

    async def disconnect(self) -> None:
        """Simulate disconnection."""
        self._connected = False

    async def health_check(self) -> MCPConnectorResult[Dict[str, Any]]:
        """Return healthy status."""
        return MCPConnectorResult.success_result(
            data={
                "healthy": True,
                "connected": self._connected,
                "call_count": self._call_count,
            },
            connector_name=self.name,
            operation="health_check",
        )

    async def execute(
        self,
        operation: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> MCPConnectorResult[Dict[str, Any]]:
        """
        Echo back the operation and params.

        Args:
            operation: Operation name to echo
            params: Parameters to echo

        Returns:
            Result containing the echoed operation and params
        """
        self._call_count += 1

        # Simulate latency if configured
        if self._latency_ms > 0:
            await asyncio.sleep(self._latency_ms / 1000)

        # Simulate failure if requested
        if self._fail_next:
            self._fail_next = False
            return MCPConnectorResult.error_result(
                errors=["Simulated failure"],
                connector_name=self.name,
                operation=operation,
            )

        return MCPConnectorResult.success_result(
            data={
                "operation": operation,
                "params": params or {},
                "kwargs": kwargs,
                "echo": True,
                "call_count": self._call_count,
            },
            connector_name=self.name,
            operation=operation,
            metadata={"stub": True},
        )

    async def stream(
        self,
        operation: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream echoed results.

        Args:
            operation: Operation name to echo
            params: Parameters to echo

        Yields:
            Chunks of the echoed data
        """
        self._call_count += 1

        # Simulate latency if configured
        if self._latency_ms > 0:
            await asyncio.sleep(self._latency_ms / 1000)

        # Simulate failure if requested
        if self._fail_next:
            self._fail_next = False
            yield {"error": "Simulated failure"}
            return

        # Yield data in chunks
        result = {
            "operation": operation,
            "params": params or {},
            "kwargs": kwargs,
            "echo": True,
            "streaming": True,
            "call_count": self._call_count,
        }

        # Yield each key-value pair as a chunk
        for key, value in result.items():
            yield {"key": key, "value": value}

    def set_fail_next(self, fail: bool = True) -> None:
        """Configure next execute() to fail."""
        self._fail_next = fail

    def set_latency(self, latency_ms: float) -> None:
        """Configure simulated latency."""
        self._latency_ms = latency_ms

    def reset(self) -> None:
        """Reset stub state."""
        self._call_count = 0
        self._fail_next = False
        self._latency_ms = 0.0
