"""Tests for MCPConnectorResult dataclass."""

import pytest

from mcp.result import MCPConnectorResult


class TestMCPConnectorResult:
    """Tests for MCPConnectorResult dataclass."""

    def test_success_result_factory(self) -> None:
        """Test success_result factory method."""
        result = MCPConnectorResult.success_result(
            data={"key": "value"},
            connector_name="test_connector",
            operation="query",
            execution_time_ms=100.5,
            metadata={"extra": "data"},
            request_id="req-123",
        )

        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.connector_name == "test_connector"
        assert result.operation == "query"
        assert result.execution_time_ms == 100.5
        assert result.metadata == {"extra": "data"}
        assert result.request_id == "req-123"
        assert result.errors == []
        assert result.warnings == []

    def test_error_result_factory(self) -> None:
        """Test error_result factory method."""
        result = MCPConnectorResult.error_result(
            errors=["Error 1", "Error 2"],
            connector_name="test_connector",
            operation="query",
            execution_time_ms=50.0,
        )

        assert result.success is False
        assert result.data is None
        assert result.errors == ["Error 1", "Error 2"]
        assert result.connector_name == "test_connector"
        assert result.operation == "query"

    def test_add_error(self) -> None:
        """Test add_error method updates success flag."""
        result = MCPConnectorResult.success_result(
            data={},
            connector_name="test",
            operation="test",
        )

        assert result.success is True

        result.add_error("Something went wrong")

        assert result.success is False
        assert "Something went wrong" in result.errors

    def test_add_warning(self) -> None:
        """Test add_warning method."""
        result = MCPConnectorResult.success_result(
            data={},
            connector_name="test",
            operation="test",
        )

        result.add_warning("This is a warning")

        assert "This is a warning" in result.warnings
        assert result.success is True  # Warnings don't affect success

    def test_to_dict(self) -> None:
        """Test to_dict serialization."""
        result = MCPConnectorResult.success_result(
            data={"items": [1, 2, 3]},
            connector_name="test",
            operation="query",
            execution_time_ms=123.45,
        )

        d = result.to_dict()

        assert d["success"] is True
        assert d["data"] == {"items": [1, 2, 3]}
        assert d["connector_name"] == "test"
        assert d["operation"] == "query"
        assert d["execution_time_ms"] == 123.45
        assert "timestamp" in d

    def test_default_values(self) -> None:
        """Test default values for optional fields."""
        result = MCPConnectorResult(success=True)

        assert result.data is None
        assert result.connector_name == ""
        assert result.operation == ""
        assert result.execution_time_ms == 0.0
        assert result.metadata == {}
        assert result.errors == []
        assert result.warnings == []
        assert result.request_id is None

    def test_generic_type(self) -> None:
        """Test that generic type works with different data types."""
        # With dict
        dict_result: MCPConnectorResult[dict] = MCPConnectorResult.success_result(
            data={"key": "value"},
            connector_name="test",
            operation="test",
        )
        assert isinstance(dict_result.data, dict)

        # With list
        list_result: MCPConnectorResult[list] = MCPConnectorResult.success_result(
            data=[1, 2, 3],
            connector_name="test",
            operation="test",
        )
        assert isinstance(list_result.data, list)

        # With string
        str_result: MCPConnectorResult[str] = MCPConnectorResult.success_result(
            data="hello",
            connector_name="test",
            operation="test",
        )
        assert isinstance(str_result.data, str)
