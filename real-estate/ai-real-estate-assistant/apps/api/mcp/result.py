"""
MCP connector result dataclass for standardized responses.

This module defines the result structure returned by all MCP connectors,
ensuring consistent response handling across different connector implementations.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar

T = TypeVar("T")


@dataclass
class MCPConnectorResult(Generic[T]):
    """
    Standardized result from MCP connector operations.

    Generic type T represents the payload type (e.g., Dict[str, Any] for JSON,
    bytes for binary data, etc.)

    Attributes:
        success: Whether the operation completed successfully
        data: The response payload (type varies by connector)
        connector_name: Identifier of the connector that produced this result
        operation: The operation that was performed (e.g., 'query', 'execute')
        timestamp: When this result was generated
        execution_time_ms: Time taken to execute the operation in milliseconds
        metadata: Additional metadata about the operation
        errors: List of error messages if success is False
        warnings: Non-fatal warning messages
        request_id: Optional request ID for tracing
    """

    success: bool
    data: Optional[T] = None
    connector_name: str = ""
    operation: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(tz=UTC))
    execution_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    request_id: Optional[str] = None

    def add_error(self, error: str) -> None:
        """Add an error message to the result."""
        self.errors.append(error)
        self.success = False

    def add_warning(self, warning: str) -> None:
        """Add a warning message to the result."""
        self.warnings.append(warning)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            "success": self.success,
            "data": self.data,
            "connector_name": self.connector_name,
            "operation": self.operation,
            "timestamp": self.timestamp.isoformat(),
            "execution_time_ms": self.execution_time_ms,
            "metadata": self.metadata,
            "errors": self.errors,
            "warnings": self.warnings,
            "request_id": self.request_id,
        }

    @classmethod
    def success_result(
        cls,
        data: T,
        connector_name: str,
        operation: str,
        execution_time_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> "MCPConnectorResult[T]":
        """Factory method for successful results."""
        return cls(
            success=True,
            data=data,
            connector_name=connector_name,
            operation=operation,
            execution_time_ms=execution_time_ms,
            metadata=metadata or {},
            request_id=request_id,
        )

    @classmethod
    def error_result(
        cls,
        errors: List[str],
        connector_name: str,
        operation: str,
        execution_time_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> "MCPConnectorResult[T]":
        """Factory method for error results."""
        return cls(
            success=False,
            data=None,
            connector_name=connector_name,
            operation=operation,
            execution_time_ms=execution_time_ms,
            metadata=metadata or {},
            errors=errors,
            request_id=request_id,
        )
