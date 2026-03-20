"""
Unit tests for advanced investment analytics calculator.

Tests cover:
- Cash flow projections
- Tax implications
- Appreciation scenarios
- Risk assessment
"""

import pytest

from analytics.financial_metrics import ExpenseParams, MortgageParams
from analytics.investment_analytics import (
    InvestmentAnalyticsCalculator,
)


class TestCashFlowProjection:
    """Test suite for cash flow projection calculations."""

    def test_basic_projection_generates_correct_years(self):
        """Test that projection generates correct number of yearly breakdowns."""
        result = InvestmentAnalyticsCalculator.project_cash_flows(
            property_price=100_000,
            monthly_rent=1_000,
            mortgage=MortgageParams(down_payment_percent=20, interest_rate=4.0, loan_term_years=30),
            expenses=ExpenseParams(),
            projection_years=10,
        )

        assert len(result.yearly_breakdown) == 10
        assert result.projection_years == 10

    def test_projection_year_increments(self):
        """Test that years increment correctly."""
        result = InvestmentAnalyticsCalculator.project_cash_flows(
            property_price=100_000,
            monthly_rent=1_000,
            projection_years=5,
        )

        years = [y.year for y in result.yearly_breakdown]
        assert years == [1, 2, 3, 4, 5]

    def test_property_appreciation_increases_value(self):
        """Test that property value increases with positive appreciation."""
        result = InvestmentAnalyticsCalculator.project_cash_flows(
            property_price=100_000,
            monthly_rent=1_000,
            appreciation_rate=3.0,  # 3% annual
            projection_years=5,
        )

        # After 5 years at 3%, value should be ~115,927
        final_value = result.yearly_breakdown[-1].property_value
        expected_value = 100_000 * (1.03**5)

        assert abs(final_value - expected_value) < 500  # Allow small rounding

    def test_depreciation_decreases_value(self):
        """Test that negative appreciation decreases property value."""
        result = InvestmentAnalyticsCalculator.project_cash_flows(
            property_price=100_000,
            monthly_rent=1_000,
            appreciation_rate=-2.0,  # -2% annual
            projection_years=5,
        )

        final_value = result.yearly_breakdown[-1].property_value
        assert final_value < 100_000

    def test_rent_growth_increases_income(self):
        """Test that rent growth increases gross income over time."""
        result = InvestmentAnalyticsCalculator.project_cash_flows(
            property_price=100_000,
            monthly_rent=1_000,
            rent_growth_rate=3.0,
            projection_years=5,
        )

        first_year_income = result.yearly_breakdown[0].gross_income
        last_year_income = result.yearly_breakdown[-1].gross_income

        assert last_year_income > first_year_income

    def test_cumulative_cash_flow_accumulates(self):
        """Test that cumulative cash flow accumulates correctly."""
        result = InvestmentAnalyticsCalculator.project_cash_flows(
            property_price=100_000,
            monthly_rent=1_500,  # High rent for positive cash flow
            mortgage=MortgageParams(down_payment_percent=50, interest_rate=4.0),
            projection_years=5,
        )

        # Cumulative should be sum of all cash flows
        total_from_breakdown = sum(y.cash_flow for y in result.yearly_breakdown)
        assert abs(result.total_cash_flow - total_from_breakdown) < 1

    def test_loan_balance_decreases_over_time(self):
        """Test that loan balance decreases as principal is paid."""
        result = InvestmentAnalyticsCalculator.project_cash_flows(
            property_price=100_000,
            monthly_rent=1_000,
            mortgage=MortgageParams(down_payment_percent=20, interest_rate=4.0, loan_term_years=30),
            projection_years=10,
        )

        initial_balance = result.yearly_breakdown[0].loan_balance
        final_balance = result.yearly_breakdown[-1].loan_balance

        assert final_balance < initial_balance

    def test_equity_increases_with_appreciation_and_paydown(self):
        """Test that equity increases from both appreciation and loan paydown."""
        result = InvestmentAnalyticsCalculator.project_cash_flows(
            property_price=100_000,
            monthly_rent=1_000,
            mortgage=MortgageParams(down_payment_percent=20, interest_rate=4.0),
            appreciation_rate=3.0,
            projection_years=10,
        )

        initial_equity = result.yearly_breakdown[0].equity
        final_equity = result.yearly_breakdown[-1].equity

        assert final_equity > initial_equity

    def test_projection_with_no_mortgage(self):
        """Test projection with 100% down payment (no mortgage)."""
        result = InvestmentAnalyticsCalculator.project_cash_flows(
            property_price=100_000,
            monthly_rent=1_000,
            mortgage=MortgageParams(down_payment_percent=100, interest_rate=0),
            projection_years=5,
        )

        # All mortgage payments should be 0
        for year in result.yearly_breakdown:
            assert year.mortgage_payment == 0

    def test_projection_invalid_years_raises_error(self):
        """Test that invalid projection years raises ValueError."""
        with pytest.raises(ValueError, match="between 1 and 30"):
            InvestmentAnalyticsCalculator.project_cash_flows(
                property_price=100_000,
                monthly_rent=1_000,
                projection_years=50,
            )

    def test_projection_invalid_price_raises_error(self):
        """Test that invalid property price raises ValueError."""
        with pytest.raises(ValueError, match="must be greater than 0"):
            InvestmentAnalyticsCalculator.project_cash_flows(
                property_price=0,
                monthly_rent=1_000,
                projection_years=5,
            )


class TestTaxImplications:
    """Test suite for tax implications calculations."""

    def test_basic_depreciation_calculation(self):
        """Test straight-line depreciation over 27.5 years."""
        result = InvestmentAnalyticsCalculator.calculate_tax_implications(
            property_price=275_000,
            land_value_ratio=0.2,  # 20% land = 55,000; 80% building = 220,000
            marginal_tax_rate=0,
        )

        # 220,000 / 27.5 = 8,000 annual depreciation
        assert result.annual_depreciation == 8_000
        assert result.depreciation_years == 27.5

    def test_total_deductions_sum(self):
        """Test that total deductions equals sum of all deductions."""
        result = InvestmentAnalyticsCalculator.calculate_tax_implications(
            property_price=100_000,
            land_value_ratio=0.2,
            mortgage_interest_annual=5_000,
            property_tax_annual=2_000,
            marginal_tax_rate=25,
        )

        expected_total = (
            result.annual_depreciation
            + result.property_tax_deduction
            + result.mortgage_interest_deduction
        )
        assert result.total_annual_deductions == expected_total

    def test_tax_benefit_calculation(self):
        """Test effective tax benefit based on marginal rate."""
        result = InvestmentAnalyticsCalculator.calculate_tax_implications(
            property_price=100_000,
            land_value_ratio=0.2,  # Building = 80,000, Depreciation = 2,909.09
            mortgage_interest_annual=0,
            property_tax_annual=0,
            marginal_tax_rate=25,  # 25% tax bracket
        )

        # Tax benefit = deductions * tax rate
        expected_benefit = result.total_annual_deductions * 0.25
        assert abs(result.effective_tax_benefit - expected_benefit) < 1

    def test_zero_tax_rate_no_benefit(self):
        """Test that 0% tax rate results in no tax benefit."""
        result = InvestmentAnalyticsCalculator.calculate_tax_implications(
            property_price=100_000,
            marginal_tax_rate=0,
        )

        assert result.effective_tax_benefit == 0

    def test_land_value_affects_depreciation(self):
        """Test that higher land ratio reduces depreciation."""
        result_low_land = InvestmentAnalyticsCalculator.calculate_tax_implications(
            property_price=100_000,
            land_value_ratio=0.1,  # 10% land
            marginal_tax_rate=0,
        )

        result_high_land = InvestmentAnalyticsCalculator.calculate_tax_implications(
            property_price=100_000,
            land_value_ratio=0.3,  # 30% land
            marginal_tax_rate=0,
        )

        # Lower land ratio = more building = more depreciation
        assert result_low_land.annual_depreciation > result_high_land.annual_depreciation


class TestAppreciationScenarios:
    """Test suite for appreciation scenario calculations."""

    def test_three_scenarios_generated(self):
        """Test that three scenarios are generated by default."""
        result = InvestmentAnalyticsCalculator.calculate_appreciation_scenarios(
            property_price=100_000,
            years=10,
        )

        assert len(result) == 3
        scenario_names = {s.name for s in result}
        assert scenario_names == {"pessimistic", "realistic", "optimistic"}

    def test_default_rates_applied(self):
        """Test that default rates are applied correctly."""
        result = InvestmentAnalyticsCalculator.calculate_appreciation_scenarios(
            property_price=100_000,
            years=10,
        )

        rates = {s.name: s.annual_rate for s in result}
        assert rates["pessimistic"] == -2.0
        assert rates["realistic"] == 3.0
        assert rates["optimistic"] == 7.0

    def test_custom_rates(self):
        """Test custom appreciation rates."""
        custom_rates = {
            "conservative": 1.0,
            "moderate": 4.0,
            "aggressive": 10.0,
        }

        result = InvestmentAnalyticsCalculator.calculate_appreciation_scenarios(
            property_price=100_000,
            years=5,
            custom_rates=custom_rates,
        )

        assert len(result) == 3
        names = {s.name for s in result}
        assert names == {"conservative", "moderate", "aggressive"}

    def test_projected_values_count(self):
        """Test that projected values has correct number of years."""
        result = InvestmentAnalyticsCalculator.calculate_appreciation_scenarios(
            property_price=100_000,
            years=10,
        )

        for scenario in result:
            assert len(scenario.projected_values) == 10

    def test_pessimistic_scenario_lower_value(self):
        """Test that pessimistic scenario results in lower final value."""
        result = InvestmentAnalyticsCalculator.calculate_appreciation_scenarios(
            property_price=100_000,
            years=10,
        )

        pessimistic = next(s for s in result if s.name == "pessimistic")
        optimistic = next(s for s in result if s.name == "optimistic")

        final_pessimistic = list(pessimistic.projected_values.values())[-1]
        final_optimistic = list(optimistic.projected_values.values())[-1]

        assert final_pessimistic < 100_000  # Lost value
        assert final_optimistic > 100_000  # Gained value

    def test_appreciation_amount_calculation(self):
        """Test total appreciation amount calculation."""
        result = InvestmentAnalyticsCalculator.calculate_appreciation_scenarios(
            property_price=100_000,
            years=5,
        )

        realistic = next(s for s in result if s.name == "realistic")
        expected_final = 100_000 * (1.03**5)
        expected_appreciation = expected_final - 100_000

        assert abs(realistic.total_appreciation_amount - expected_appreciation) < 100

    def test_invalid_years_raises_error(self):
        """Test that invalid years raises ValueError."""
        with pytest.raises(ValueError, match="between 1 and 30"):
            InvestmentAnalyticsCalculator.calculate_appreciation_scenarios(
                property_price=100_000,
                years=50,
            )


class TestRiskAssessment:
    """Test suite for risk assessment calculations."""

    def test_risk_score_in_valid_range(self):
        """Test that overall risk score is 0-100."""
        result = InvestmentAnalyticsCalculator.assess_risk(
            property_price=100_000,
            monthly_cash_flow=500,
            cap_rate=6.0,
            debt_service_ratio=1.5,
            vacancy_rate=5.0,
            market_volatility=0.3,
            loan_to_value=0.8,
        )

        assert 0 <= result.overall_score <= 100
        assert 0 <= result.market_volatility_score <= 100
        assert 0 <= result.cash_flow_stability_score <= 100
        assert 0 <= result.debt_risk_score <= 100

    def test_positive_cash_flow_improves_score(self):
        """Test that positive cash flow results in better score."""
        result_positive = InvestmentAnalyticsCalculator.assess_risk(
            property_price=100_000,
            monthly_cash_flow=500,
            cap_rate=6.0,
            debt_service_ratio=1.5,
            vacancy_rate=5.0,
        )

        result_negative = InvestmentAnalyticsCalculator.assess_risk(
            property_price=100_000,
            monthly_cash_flow=-200,
            cap_rate=6.0,
            debt_service_ratio=1.5,
            vacancy_rate=5.0,
        )

        assert result_positive.overall_score > result_negative.overall_score
        assert "Negative cash flow" in result_negative.risk_factors

    def test_high_dscr_improves_debt_score(self):
        """Test that high DSCR improves debt risk score."""
        result_high_dscr = InvestmentAnalyticsCalculator.assess_risk(
            property_price=100_000,
            monthly_cash_flow=500,
            cap_rate=6.0,
            debt_service_ratio=1.5,
            vacancy_rate=5.0,
        )

        result_low_dscr = InvestmentAnalyticsCalculator.assess_risk(
            property_price=100_000,
            monthly_cash_flow=500,
            cap_rate=6.0,
            debt_service_ratio=0.8,
            vacancy_rate=5.0,
        )

        assert result_high_dscr.debt_risk_score > result_low_dscr.debt_risk_score
        assert any("DSCR" in f for f in result_low_dscr.risk_factors)

    def test_high_volatility_reduces_score(self):
        """Test that high market volatility reduces overall score."""
        result_stable = InvestmentAnalyticsCalculator.assess_risk(
            property_price=100_000,
            monthly_cash_flow=500,
            cap_rate=6.0,
            debt_service_ratio=1.5,
            vacancy_rate=5.0,
            market_volatility=0.1,  # Stable market
        )

        result_volatile = InvestmentAnalyticsCalculator.assess_risk(
            property_price=100_000,
            monthly_cash_flow=500,
            cap_rate=6.0,
            debt_service_ratio=1.5,
            vacancy_rate=5.0,
            market_volatility=0.9,  # Volatile market
        )

        assert result_stable.market_volatility_score > result_volatile.market_volatility_score
        assert "High market volatility" in result_volatile.risk_factors

    def test_high_ltv_increases_risk(self):
        """Test that high loan-to-value increases risk."""
        result_low_ltv = InvestmentAnalyticsCalculator.assess_risk(
            property_price=100_000,
            monthly_cash_flow=500,
            cap_rate=6.0,
            debt_service_ratio=1.5,
            vacancy_rate=5.0,
            loan_to_value=0.5,
        )

        result_high_ltv = InvestmentAnalyticsCalculator.assess_risk(
            property_price=100_000,
            monthly_cash_flow=500,
            cap_rate=6.0,
            debt_service_ratio=1.5,
            vacancy_rate=5.0,
            loan_to_value=0.95,
        )

        assert result_low_ltv.debt_risk_score > result_high_ltv.debt_risk_score
        assert any("Very high LTV" in f for f in result_high_ltv.risk_factors)

    def test_recommendations_generated_for_low_score(self):
        """Test that recommendations are generated for risky investments."""
        result = InvestmentAnalyticsCalculator.assess_risk(
            property_price=100_000,
            monthly_cash_flow=-500,  # Negative cash flow
            cap_rate=3.0,
            debt_service_ratio=0.7,  # Low DSCR
            vacancy_rate=15.0,  # High vacancy
            market_volatility=0.8,
            loan_to_value=0.95,
        )

        assert len(result.recommendations) > 0
        assert len(result.risk_factors) > 0

    def test_high_vacancy_affects_liquidity(self):
        """Test that high vacancy rate reduces liquidity score."""
        result_low_vacancy = InvestmentAnalyticsCalculator.assess_risk(
            property_price=100_000,
            monthly_cash_flow=500,
            cap_rate=6.0,
            debt_service_ratio=1.5,
            vacancy_rate=3.0,
        )

        result_high_vacancy = InvestmentAnalyticsCalculator.assess_risk(
            property_price=100_000,
            monthly_cash_flow=500,
            cap_rate=6.0,
            debt_service_ratio=1.5,
            vacancy_rate=15.0,
        )

        assert result_low_vacancy.liquidity_score > result_high_vacancy.liquidity_score


class TestIRRCalculation:
    """Test suite for IRR calculation helper."""

    def test_irr_with_positive_returns(self):
        """Test IRR calculation with positive returns."""
        # Simple case: invest 100, get 10/year for 5 years + 100 back
        irr = InvestmentAnalyticsCalculator._calculate_irr(
            initial_investment=100,
            yearly_cash_flows=[10, 10, 10, 10, 10],
            final_value=100,
        )

        # Should be around 10%
        assert irr is not None
        assert 8 <= irr <= 12

    def test_irr_with_no_investment(self):
        """Test IRR with zero investment returns None."""
        irr = InvestmentAnalyticsCalculator._calculate_irr(
            initial_investment=0,
            yearly_cash_flows=[10, 10],
            final_value=100,
        )

        assert irr is None

    def test_irr_negative_returns(self):
        """Test IRR with negative returns."""
        irr = InvestmentAnalyticsCalculator._calculate_irr(
            initial_investment=100,
            yearly_cash_flows=[-5, -5, -5],
            final_value=80,  # Lost value
        )

        # Should be negative
        assert irr is not None
        assert irr < 0
