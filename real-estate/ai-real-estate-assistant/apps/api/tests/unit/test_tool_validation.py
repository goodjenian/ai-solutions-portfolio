"""
Tests for tool input validation and sensitive data redaction.

Part of TASK-003.2: Tool registry and execution safety.
"""

import pytest

from tools.property_tools import (
    LocationAnalysisInput,
    LocationAnalysisTool,
    MortgageCalculatorTool,
    PriceAnalysisInput,
    PriceAnalysisTool,
    PropertyComparisonInput,
    PropertyComparisonTool,
)
from utils.sanitization import redact_sensitive_data, sanitize_intermediate_steps


class TestMortgageCalculatorTool:
    """Tests for mortgage calculator tool."""

    def test_calculate_valid_input(self):
        """Test mortgage calculation with valid input."""
        result = MortgageCalculatorTool.calculate(
            property_price=500000, down_payment_percent=20, interest_rate=4.5, loan_years=30
        )
        assert result.monthly_payment > 0
        assert result.total_interest > 0
        assert result.down_payment == 100000
        assert result.loan_amount == 400000

    def test_calculate_invalid_price_raises_error(self):
        """Test that invalid price raises ValueError."""
        with pytest.raises(ValueError, match="Property price must be positive"):
            MortgageCalculatorTool.calculate(property_price=0)

    def test_calculate_invalid_down_payment_raises_error(self):
        """Test that invalid down payment raises ValueError."""
        with pytest.raises(ValueError, match="Down payment must be between 0 and 100"):
            MortgageCalculatorTool.calculate(property_price=500000, down_payment_percent=150)

    def test_calculate_invalid_interest_rate_raises_error(self):
        """Test that negative interest rate raises ValueError."""
        with pytest.raises(ValueError, match="Interest rate cannot be negative"):
            MortgageCalculatorTool.calculate(property_price=500000, interest_rate=-1)

    def test_calculate_invalid_loan_term_raises_error(self):
        """Test that invalid loan term raises ValueError."""
        with pytest.raises(ValueError, match="Loan term must be positive"):
            MortgageCalculatorTool.calculate(property_price=500000, loan_years=0)

    def test_run_with_edge_case_zero_interest(self):
        """Test calculation with zero interest rate."""
        result = MortgageCalculatorTool.calculate(
            property_price=100000, down_payment_percent=10, interest_rate=0, loan_years=10
        )
        # With 0% interest, monthly payment should be principal / num_payments
        assert result.monthly_payment > 0
        assert result.total_interest == 0


class TestPropertyComparisonTool:
    """Tests for property comparison tool."""

    def test_args_schema_is_pydantic_model(self):
        """Test that tool has Pydantic args_schema."""
        tool = PropertyComparisonTool()
        assert tool.args_schema == PropertyComparisonInput

    def test_args_schema_validation(self):
        """Test that args_schema validates input."""
        schema = PropertyComparisonInput
        # Valid input
        valid = schema(property_ids="prop1,prop2,prop3")
        assert valid.property_ids == "prop1,prop2,prop3"

        # Invalid input (empty string)
        with pytest.raises(ValueError):  # Pydantic ValidationError inherits from ValueError
            schema(property_ids="")


class TestPriceAnalysisTool:
    """Tests for price analysis tool."""

    def test_args_schema_is_pydantic_model(self):
        """Test that tool has Pydantic args_schema."""
        tool = PriceAnalysisTool()
        assert tool.args_schema == PriceAnalysisInput

    def test_args_schema_validation(self):
        """Test that args_schema validates input."""
        schema = PriceAnalysisInput
        # Valid input
        valid = schema(query="apartments in Madrid")
        assert valid.query == "apartments in Madrid"

        # Invalid input (empty string)
        with pytest.raises(ValueError):  # Pydantic ValidationError inherits from ValueError
            schema(query="")


class TestLocationAnalysisTool:
    """Tests for location analysis tool."""

    def test_args_schema_is_pydantic_model(self):
        """Test that tool has Pydantic args_schema."""
        tool = LocationAnalysisTool()
        assert tool.args_schema == LocationAnalysisInput

    def test_args_schema_validation(self):
        """Test that args_schema validates input."""
        schema = LocationAnalysisInput
        # Valid input
        valid = schema(property_id="prop-12345")
        assert valid.property_id == "prop-12345"

        # Invalid input (empty string)
        with pytest.raises(ValueError):  # Pydantic ValidationError inherits from ValueError
            schema(property_id="")


class TestSensitiveDataRedaction:
    """Tests for sensitive data redaction."""

    def test_redact_api_key(self):
        """Test that API keys are redacted."""
        data = "api_key='sk-abc123def456789012345678'"
        redacted = redact_sensitive_data(data)
        assert "sk-***" in redacted
        assert "abc123" not in redacted

    def test_redact_bearer_token(self):
        """Test that Bearer tokens are redacted."""
        data = "Authorization: Bearer ghp_abc123def456789012345678901"
        redacted = redact_sensitive_data(data)
        assert "Bearer ***" in redacted
        assert "ghp_" not in redacted

    def test_redact_password(self):
        """Test that passwords are redacted."""
        data = "password='secret123'"
        redacted = redact_sensitive_data(data)
        assert "***" in redacted
        assert "secret123" not in redacted

    def test_redact_email(self):
        """Test that email addresses are partially redacted."""
        data = "Contact: user@example.com"
        redacted = redact_sensitive_data(data)
        assert "@***" in redacted
        assert "user@example.com" not in redacted

    def test_redact_dict(self):
        """Test that dictionaries are recursively redacted."""
        data = {
            "api_key": "sk-abc123",
            "user": "john@example.com",
            "nested": {"token": "ghp_secret"},
        }
        redacted = redact_sensitive_data(data)
        assert redacted["api_key"] == "sk-***"
        assert "@***" in redacted["user"]
        assert redacted["nested"]["token"] == "***"

    def test_redact_list(self):
        """Test that lists are recursively redacted."""
        data = [{"api_key": "sk-abc123"}, "Bearer token123", {"nested": {"pwd": "password123"}}]
        redacted = redact_sensitive_data(data)
        assert "***" in str(redacted)
        assert "sk-abc123" not in str(redacted)
        assert "password123" not in str(redacted)


class TestSanitizeIntermediateSteps:
    """Tests for intermediate steps sanitization."""

    def test_sanitize_empty_steps(self):
        """Test that empty steps return empty list."""
        result = sanitize_intermediate_steps([])
        assert result == []

    def test_sanitize_redacts_sensitive_data(self):
        """Test that sensitive data in steps is redacted."""
        steps = [
            {"tool": "search", "input": {"api_key": "sk-abc123"}},
            {"tool": "api_call", "output": "Bearer token123 response"},
            {"tool": "login", "input": {"user": "john@example.com", "pwd": "secret"}},
        ]
        result = sanitize_intermediate_steps(steps)

        # Should have same number of steps
        assert len(result) == 3

        # Should not contain sensitive data
        result_str = str(result)
        assert "sk-abc123" not in result_str
        assert "token123" not in result_str
        assert "secret" not in result_str
        assert "@***" in result_str  # Email should be partially redacted
        assert "***" in result_str

    def test_sanitize_limits_steps(self):
        """Test that excessive steps are limited."""
        # Create 100 steps
        steps = [{"tool": f"step_{i}", "input": "data"} for i in range(100)]
        result = sanitize_intermediate_steps(steps)

        # Should be limited to max_steps (50)
        assert len(result) == 50

    def test_sanitize_truncates_long_outputs(self):
        """Test that long outputs are truncated."""
        steps = [
            {
                "tool": "generate",
                "output": "x" * 2000,  # Very long output
            }
        ]
        result = sanitize_intermediate_steps(steps)

        assert len(result) == 1
        assert "(truncated)" in str(result[0])
        # Should be truncated to max_output_size (1000) + "... (truncated)"
        assert len(result[0]["output"]) < 1100

    def test_sanitize_handles_invalid_serialization(self):
        """Test that invalid objects are handled gracefully."""

        # Create an object that can't be serialized properly
        class Unserializable:
            def __str__(self):
                raise RuntimeError("Cannot serialize")

        steps = [{"tool": "bad", "data": Unserializable()}]
        result = sanitize_intermediate_steps(steps)

        # Should include a placeholder instead of crashing
        assert len(result) == 1
        assert "sanitization failed" in str(result).lower()
