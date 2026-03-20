"""
MCP stub connectors for deterministic testing.

These stubs provide predictable behavior for unit tests
without requiring network access.
"""

from mcp.stubs.echo_stub import EchoStubConnector

__all__ = ["EchoStubConnector"]
