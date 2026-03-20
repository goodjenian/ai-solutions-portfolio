from unittest.mock import patch

from langchain_core.documents import Document

from tools.property_tools import (
    MortgageCalculatorTool,
    PriceAnalysisTool,
    PropertyComparisonTool,
    TCOCalculatorTool,
)


def test_mortgage_calculator_tool_handles_value_error():
    tool = MortgageCalculatorTool()
    out = tool._run(property_price=0)
    assert out.startswith("Error:")


def test_mortgage_calculator_tool_handles_unexpected_error():
    tool = MortgageCalculatorTool()
    with patch.object(MortgageCalculatorTool, "calculate", side_effect=RuntimeError("boom")):
        out = tool._run(property_price=100000)
    assert out.startswith("Error calculating mortgage:")


def test_property_comparison_tool_handles_missing_store_and_empty_ids():
    tool = PropertyComparisonTool(vector_store=None)
    out = tool._run("p1")
    assert "Provide a comma-separated list of property IDs" in out

    tool2 = PropertyComparisonTool(vector_store=object())
    out2 = tool2._run(" , ")
    assert "Please provide at least one property ID" in out2


def test_property_comparison_tool_handles_store_without_id_retrieval():
    tool = PropertyComparisonTool(vector_store=object())
    out = tool._run("p1")
    assert "does not support retrieving by IDs" in out


def test_property_comparison_tool_handles_no_docs_and_formats_values():
    class StoreEmpty:
        def get_properties_by_ids(self, ids):
            return []

    tool = PropertyComparisonTool(vector_store=StoreEmpty())
    out = tool._run("p1")
    assert "No properties found" in out

    class Store:
        def get_properties_by_ids(self, ids):
            return [
                Document(
                    page_content="",
                    metadata={"id": "p1", "price": 1000, "price_per_sqm": 20, "area_sqm": 50},
                ),
                Document(
                    page_content="",
                    metadata={"id": "p2", "price": 2000, "price_per_sqm": 40, "area_sqm": 60},
                ),
            ]

    tool2 = PropertyComparisonTool(vector_store=Store())
    out2 = tool2._run("p1, p2")
    assert "$1,000" in out2
    assert "/m²" in out2
    assert "Price difference" in out2


def test_price_analysis_tool_handles_empty_results_and_missing_prices():
    tool = PriceAnalysisTool(vector_store=None)
    out = tool._run("warsaw")
    assert "Provide a data source" in out

    class StoreEmpty:
        def search(self, query, k=20):
            return []

    tool2 = PriceAnalysisTool(vector_store=StoreEmpty())
    out2 = tool2._run("warsaw")
    assert "No properties found" in out2

    class StoreNoPrices:
        def search(self, query, k=20):
            return [(Document(page_content="", metadata={"price": "bad"}), 0.5)]

    tool3 = PriceAnalysisTool(vector_store=StoreNoPrices())
    out3 = tool3._run("warsaw")
    assert "no price data available" in out3.lower()


def test_tco_calculator_tool_handles_value_error():
    """Test TCO calculator handles invalid input."""
    tool = TCOCalculatorTool()
    out = tool._run(property_price=0)
    assert out.startswith("Error:")


def test_tco_calculator_tool_handles_unexpected_error():
    """Test TCO calculator handles unexpected errors."""
    tool = TCOCalculatorTool()
    with patch.object(TCOCalculatorTool, "calculate", side_effect=RuntimeError("boom")):
        out = tool._run(property_price=100000)
        assert out.startswith("Error calculating TCO:")


def test_tco_calculator_tool_returns_complete_breakdown():
    """Test TCO calculator returns all expected fields."""
    result = TCOCalculatorTool.calculate(
        property_price=500000,
        down_payment_percent=20,
        interest_rate=4.5,
        loan_years=30,
        monthly_hoa=200,
        annual_property_tax=6000,
        annual_insurance=1800,
        monthly_utilities=150,
        monthly_internet=50,
        monthly_parking=100,
        maintenance_percent=1,
    )

    # Verify all monthly TCO components are calculated
    assert result.monthly_tco > result.monthly_mortgage
    assert result.monthly_property_tax == 500  # 6000/12
    assert result.monthly_insurance == 150  # 1800/12
    assert result.monthly_hoa == 200
    assert result.monthly_utilities == 150
    assert result.monthly_internet == 50
    assert result.monthly_parking == 100
    assert result.monthly_maintenance > 0

    # Verify total calculations
    assert result.total_ownership_cost > 0
    assert result.total_all_costs == result.total_ownership_cost + result.down_payment

    # Verify breakdown contains all expected keys
    expected_keys = {
        "mortgage",
        "property_tax",
        "insurance",
        "hoa",
        "utilities",
        "internet",
        "parking",
        "maintenance",
    }
    assert set(result.breakdown.keys()) == expected_keys


def test_tco_calculator_tool_with_minimal_inputs():
    """Test TCO calculator works with just mortgage inputs."""
    result = TCOCalculatorTool.calculate(
        property_price=500000,
        down_payment_percent=20,
        interest_rate=4.5,
        loan_years=30,
    )

    # Should include maintenance (1% default) even with minimal inputs
    assert result.monthly_tco > result.monthly_mortgage
    assert result.monthly_maintenance > 0

    # Verify all other optional costs are zero
    assert result.monthly_property_tax == 0
    assert result.monthly_insurance == 0
    assert result.monthly_hoa == 0
    assert result.monthly_utilities == 0
    assert result.monthly_internet == 0
    assert result.monthly_parking == 0


def test_tco_calculator_tool_with_all_costs():
    """Test TCO calculator with all optional costs."""
    result = TCOCalculatorTool.calculate(
        property_price=300000,
        down_payment_percent=15,
        interest_rate=5.0,
        loan_years=20,
        monthly_hoa=300,
        annual_property_tax=3600,
        annual_insurance=1200,
        monthly_utilities=200,
        monthly_internet=60,
        monthly_parking=150,
        maintenance_percent=1.5,
    )

    # Verify all costs are included in TCO
    assert result.monthly_tco == (
        result.monthly_mortgage
        + result.monthly_property_tax
        + result.monthly_insurance
        + result.monthly_hoa
        + result.monthly_utilities
        + result.monthly_internet
        + result.monthly_parking
        + result.monthly_maintenance
    )

    # Verify maintenance is 1.5% of property price annually
    expected_monthly_maintenance = (300000 * 1.5 / 100) / 12
    assert result.monthly_maintenance == expected_monthly_maintenance


def test_tco_calculator_tool_zero_interest_rate():
    """Test TCO calculator handles zero interest rate edge case."""
    result = TCOCalculatorTool.calculate(
        property_price=400000,
        down_payment_percent=20,
        interest_rate=0,
        loan_years=15,
    )

    # Zero interest should still work
    assert result.monthly_mortgage > 0
    assert result.total_interest == 0


def test_tco_calculator_shorter_loan_term():
    """Test TCO calculator with shorter loan term."""
    result15 = TCOCalculatorTool.calculate(
        property_price=600000,
        down_payment_percent=20,
        interest_rate=4.5,
        loan_years=15,
    )

    result30 = TCOCalculatorTool.calculate(
        property_price=600000,
        down_payment_percent=20,
        interest_rate=4.5,
        loan_years=30,
    )

    # Shorter loan should have lower total interest
    assert result15.total_interest < result30.total_interest
    # But monthly payment should be higher
    assert result15.monthly_payment > result30.monthly_payment


def test_tco_calculator_tool_run_method_output():
    """Test TCO calculator _run method returns formatted output."""
    tool = TCOCalculatorTool()
    result = tool._run(
        property_price=500000,
        down_payment_percent=20,
        interest_rate=4.5,
        loan_years=30,
        monthly_hoa=200,
        annual_property_tax=6000,
        annual_insurance=1800,
    )

    # Verify formatted output contains key sections
    assert "Total Cost of Ownership" in result
    assert "Monthly Costs" in result
    assert "Annual Costs" in result
    assert "MONTHLY TCO" in result
    assert "ANNUAL TCO" in result
    assert "Total Ownership Cost" in result
    assert "TOTAL ALL-IN COST" in result

    # Verify values are formatted with dollar signs and decimals
    assert "$" in result
    assert "Mortgage Payment:" in result
    assert "Property Tax:" in result
    assert "Home Insurance:" in result
