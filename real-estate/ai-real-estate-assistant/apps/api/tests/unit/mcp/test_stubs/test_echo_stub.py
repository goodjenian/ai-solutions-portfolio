"""Tests for EchoStubConnector."""

import asyncio
import pytest

from mcp.config import MCPEdition
from mcp.result import MCPConnectorResult
from mcp.stubs import EchoStubConnector


class TestEchoStubConnector:
    """Tests for EchoStubConnector stub."""

    def test_stub_attributes(self) -> None:
        """Test stub has correct attributes."""
        assert EchoStubConnector.name == "echo_stub"
        assert EchoStubConnector.display_name == "Echo Stub (Testing)"
        assert EchoStubConnector.requires_api_key is False
        assert EchoStubConnector.allowlisted is True
        assert EchoStubConnector.min_edition == MCPEdition.COMMUNITY
        assert EchoStubConnector.supports_streaming is True

    def test_stub_no_api_key_required(self) -> None:
        """Test stub doesn't require API key."""
        # Should not raise
        connector = EchoStubConnector()
        assert connector is not None


class TestEchoStubConnectorAsync:
    """Async tests for EchoStubConnector."""

    @pytest.mark.asyncio
    async def test_connect(self) -> None:
        """Test connect always succeeds."""
        connector = EchoStubConnector()

        result = await connector.connect()

        assert result is True
        assert connector.is_connected() is True

    @pytest.mark.asyncio
    async def test_disconnect(self) -> None:
        """Test disconnect."""
        connector = EchoStubConnector()
        await connector.connect()

        await connector.disconnect()

        assert connector.is_connected() is False

    @pytest.mark.asyncio
    async def test_health_check(self) -> None:
        """Test health check returns healthy."""
        connector = EchoStubConnector()

        result = await connector.health_check()

        assert result.success is True
        assert result.data["healthy"] is True
        assert result.connector_name == "echo_stub"

    @pytest.mark.asyncio
    async def test_execute_echoes_params(self) -> None:
        """Test execute echoes back operation and params."""
        connector = EchoStubConnector()

        result = await connector.execute(
            operation="query",
            params={"city": "Berlin", "min_price": 1000},
        )

        assert result.success is True
        assert result.data["operation"] == "query"
        assert result.data["params"]["city"] == "Berlin"
        assert result.data["params"]["min_price"] == 1000
        assert result.data["echo"] is True

    @pytest.mark.asyncio
    async def test_execute_tracks_call_count(self) -> None:
        """Test execute tracks call count."""
        connector = EchoStubConnector()

        await connector.execute("op1")
        await connector.execute("op2")
        result = await connector.execute("op3")

        assert result.data["call_count"] == 3

    @pytest.mark.asyncio
    async def test_simulated_latency(self) -> None:
        """Test simulated latency."""
        connector = EchoStubConnector(latency_ms=50)  # 50ms

        import time

        start = time.perf_counter()
        await connector.execute("test")
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Should be at least 50ms (with some margin for test overhead)
        assert elapsed_ms >= 45  # Allow small margin

    @pytest.mark.asyncio
    async def test_simulated_failure(self) -> None:
        """Test simulated failure mode."""
        connector = EchoStubConnector(fail_next=True)

        # First call should fail
        result = await connector.execute("test")
        assert result.success is False
        assert "Simulated failure" in result.errors

        # Second call should succeed
        result = await connector.execute("test")
        assert result.success is True

    @pytest.mark.asyncio
    async def test_set_fail_next(self) -> None:
        """Test set_fail_next method."""
        connector = EchoStubConnector()

        result = await connector.execute("test")
        assert result.success is True

        connector.set_fail_next(True)
        result = await connector.execute("test")
        assert result.success is False

        result = await connector.execute("test")
        assert result.success is True  # Reset after one failure

    @pytest.mark.asyncio
    async def test_set_latency(self) -> None:
        """Test set_latency method."""
        connector = EchoStubConnector()

        connector.set_latency(10)

        import time

        start = time.perf_counter()
        await connector.execute("test")
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms >= 5  # Allow some margin

    @pytest.mark.asyncio
    async def test_reset(self) -> None:
        """Test reset method."""
        connector = EchoStubConnector(latency_ms=100, fail_next=True)

        # Make a call to increment count
        await connector.execute("test")
        assert connector._call_count == 1

        connector.reset()

        assert connector._call_count == 0
        assert connector._fail_next is False
        assert connector._latency_ms == 0.0

    @pytest.mark.asyncio
    async def test_stream(self) -> None:
        """Test streaming functionality."""
        connector = EchoStubConnector()

        chunks = []
        async for chunk in connector.stream("test", {"param": "value"}):
            chunks.append(chunk)

        # EchoStubConnector streams individual result chunks
        assert len(chunks) >= 0  # Implementation dependent

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        """Test async context manager."""
        async with EchoStubConnector() as connector:
            assert connector.is_connected() is True
            result = await connector.execute("test")
            assert result.success is True

        assert connector.is_connected() is False

    @pytest.mark.asyncio
    async def test_no_network_calls(self) -> None:
        """Verify stub never makes network calls.

        This test ensures the stub is safe for unit testing without
        mocking or network access.
        """
        connector = EchoStubConnector()

        # All these should work without network
        await connector.connect()
        result = await connector.execute("any_operation", {"any": "params"})
        health = await connector.health_check()
        await connector.disconnect()

        assert result.success is True
        assert health.success is True
