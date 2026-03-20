"""Tests for MCPConnector abstract base class."""

import pytest

from mcp.base import MCPConnector
from mcp.config import MCPEdition, MCPConnectorConfig
from mcp.exceptions import MCPNotAllowlistedError
from mcp.result import MCPConnectorResult


class ConcreteConnector(MCPConnector[dict]):
    """Concrete implementation for testing."""

    name = "concrete"
    display_name = "Concrete Connector"
    description = "A concrete connector for testing"
    requires_api_key = False
    allowlisted = True
    min_edition = MCPEdition.COMMUNITY

    async def connect(self) -> bool:
        self._connected = True
        return True

    async def disconnect(self) -> None:
        self._connected = False

    async def health_check(self) -> MCPConnectorResult[dict]:
        return MCPConnectorResult.success_result(
            data={"healthy": True},
            connector_name=self.name,
            operation="health_check",
        )

    async def execute(
        self,
        operation: str,
        params: dict | None = None,
        **kwargs,
    ) -> MCPConnectorResult[dict]:
        return MCPConnectorResult.success_result(
            data={"operation": operation, "params": params},
            connector_name=self.name,
            operation=operation,
        )


class TestMCPConnector:
    """Tests for MCPConnector base class."""

    def test_connector_requires_name(self) -> None:
        """Test connector must have a name."""

        class NoNameConnector(MCPConnector[dict]):
            name = ""

            async def connect(self) -> bool:
                return True

            async def disconnect(self) -> None:
                pass

            async def health_check(self) -> MCPConnectorResult[dict]:
                pass  # type: ignore

            async def execute(
                self, operation: str, params: dict | None = None, **kwargs
            ) -> MCPConnectorResult[dict]:
                pass  # type: ignore

        with pytest.raises(ValueError, match="name"):
            NoNameConnector()

    def test_connector_requires_api_key_when_specified(self) -> None:
        """Test connector validates API key requirement."""

        class RequiresKeyConnector(MCPConnector[dict]):
            name = "requires_key"
            requires_api_key = True
            api_key_env_var = "REQUIRED_API_KEY"

            async def connect(self) -> bool:
                return True

            async def disconnect(self) -> None:
                pass

            async def health_check(self) -> MCPConnectorResult[dict]:
                pass  # type: ignore

            async def execute(
                self, operation: str, params: dict | None = None, **kwargs
            ) -> MCPConnectorResult[dict]:
                pass  # type: ignore

        with pytest.raises(ValueError, match="API key"):
            RequiresKeyConnector()

    def test_connector_with_config(self) -> None:
        """Test connector accepts custom config."""
        config = MCPConnectorConfig(
            name="concrete",
            display_name="Concrete",
            timeout_seconds=60.0,
        )

        connector = ConcreteConnector(config=config)

        assert connector.get_config().timeout_seconds == 60.0

    def test_check_edition_access_community_allowlisted(self) -> None:
        """Test edition access check for allowlisted connector."""
        connector = ConcreteConnector()

        # Should not raise - connector is allowlisted
        connector.check_edition_access(MCPEdition.COMMUNITY)

    def test_check_edition_access_community_not_allowlisted(self) -> None:
        """Test edition access check blocks non-allowlisted in CE."""

        class NotAllowlistedConnector(ConcreteConnector):
            name = "not_allowlisted"
            allowlisted = False
            min_edition = MCPEdition.PRO

        connector = NotAllowlistedConnector()

        with pytest.raises(MCPNotAllowlistedError):
            connector.check_edition_access(MCPEdition.COMMUNITY)

    def test_is_connected(self) -> None:
        """Test is_connected method."""
        connector = ConcreteConnector()

        assert connector.is_connected() is False

    def test_get_status(self) -> None:
        """Test get_status method."""
        connector = ConcreteConnector()

        status = connector.get_status()

        assert status["name"] == "concrete"
        assert status["display_name"] == "Concrete Connector"
        assert status["connected"] is False
        assert "config" in status


class TestMCPConnectorAsync:
    """Async tests for MCPConnector base class."""

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        """Test async context manager."""
        connector = ConcreteConnector()

        assert connector.is_connected() is False

        async with connector as ctx:
            assert ctx is connector
            assert connector.is_connected() is True

        assert connector.is_connected() is False

    @pytest.mark.asyncio
    async def test_execute_with_timing(self) -> None:
        """Test execute_with_timing measures time."""
        connector = ConcreteConnector()

        result = await connector.execute_with_timing("test_op", {"param": "value"})

        assert result.success is True
        assert result.operation == "test_op"
        assert result.execution_time_ms >= 0

    @pytest.mark.asyncio
    async def test_execute_with_timing_on_error(self) -> None:
        """Test execute_with_timing handles errors."""

        class ErrorConnector(ConcreteConnector):
            async def execute(
                self, operation: str, params: dict | None = None, **kwargs
            ) -> MCPConnectorResult[dict]:
                raise RuntimeError("Test error")

        connector = ErrorConnector()

        result = await connector.execute_with_timing("test_op")

        assert result.success is False
        assert "Test error" in result.errors
        assert result.execution_time_ms >= 0

    @pytest.mark.asyncio
    async def test_health_check(self) -> None:
        """Test health_check method."""
        connector = ConcreteConnector()

        result = await connector.health_check()

        assert result.success is True
        assert result.data["healthy"] is True

    @pytest.mark.asyncio
    async def test_stream_not_supported(self) -> None:
        """Test stream raises NotImplementedError when not supported."""

        class NoStreamConnector(ConcreteConnector):
            supports_streaming = False

        connector = NoStreamConnector()

        with pytest.raises(NotImplementedError, match="streaming"):
            async for _ in connector.stream("test"):
                pass

    @pytest.mark.asyncio
    async def test_stream_supported(self) -> None:
        """Test stream works when supported."""

        class StreamConnector(ConcreteConnector):
            supports_streaming = True

            async def stream(self, operation: str, params=None, **kwargs):
                yield {"chunk": 1}
                yield {"chunk": 2}

        connector = StreamConnector()

        chunks = []
        async for chunk in connector.stream("test"):
            chunks.append(chunk)

        assert len(chunks) == 2
