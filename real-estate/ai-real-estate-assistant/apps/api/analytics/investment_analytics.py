"""
Advanced investment analytics for real estate properties.

This module provides advanced calculators for:
- Multi-year cash flow projections
- Tax implications (depreciation, deductions)
- Appreciation scenarios (pessimistic, realistic, optimistic)
- Risk assessment scoring
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from analytics.financial_metrics import ExpenseParams, FinancialCalculator, MortgageParams

logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes for Projections
# ============================================================================


@dataclass
class YearlyCashFlow:
    """Cash flow breakdown for a single year."""

    year: int
    gross_income: float
    operating_expenses: float
    mortgage_payment: float
    noi: float  # Net Operating Income
    cash_flow: float
    cumulative_cash_flow: float
    property_value: float  # With appreciation
    equity: float  # Property value - loan balance
    loan_balance: float


@dataclass
class CashFlowProjection:
    """Multi-year cash flow projection result."""

    property_price: float
    projection_years: int
    yearly_breakdown: List[YearlyCashFlow]
    total_cash_flow: float
    total_principal_paid: float
    final_equity: float
    irr: Optional[float] = None  # Internal Rate of Return


@dataclass
class TaxImplications:
    """Tax implications of real estate investment."""

    annual_depreciation: float
    property_tax_deduction: float
    mortgage_interest_deduction: float
    total_annual_deductions: float
    taxable_income_reduction: float
    effective_tax_benefit: float  # Actual tax savings
    depreciation_years: int


@dataclass
class AppreciationScenario:
    """Single appreciation scenario."""

    name: str  # "pessimistic", "realistic", "optimistic"
    annual_rate: float  # Annual appreciation rate as percentage
    projected_values: Dict[int, float]  # year -> projected value
    total_appreciation_percent: float
    total_appreciation_amount: float


@dataclass
class RiskAssessment:
    """Comprehensive risk assessment for investment property."""

    overall_score: float  # 0-100 (higher = lower risk)
    market_volatility_score: float  # 0-100
    cash_flow_stability_score: float  # 0-100
    debt_risk_score: float  # 0-100
    liquidity_score: float  # 0-100
    risk_factors: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


# ============================================================================
# Investment Analytics Calculator
# ============================================================================


class InvestmentAnalyticsCalculator:
    """Advanced investment analytics calculator."""

    # Default appreciation rates for scenarios
    DEFAULT_APPRECIATION_RATES = {
        "pessimistic": -2.0,  # -2% annual
        "realistic": 3.0,  # 3% annual
        "optimistic": 7.0,  # 7% annual
    }

    @staticmethod
    def project_cash_flows(
        property_price: float,
        monthly_rent: float,
        mortgage: Optional[MortgageParams] = None,
        expenses: Optional[ExpenseParams] = None,
        appreciation_rate: float = 3.0,
        rent_growth_rate: float = 2.0,
        projection_years: int = 20,
    ) -> CashFlowProjection:
        """
        Project cash flows over specified years with annual breakdown.

        Args:
            property_price: Purchase price of property
            monthly_rent: Initial monthly rent
            mortgage: Mortgage parameters
            expenses: Operating expense parameters
            appreciation_rate: Annual property appreciation rate (%)
            rent_growth_rate: Annual rent growth rate (%)
            projection_years: Number of years to project

        Returns:
            CashFlowProjection with yearly breakdown
        """
        if property_price <= 0:
            raise ValueError("Property price must be greater than 0")
        if projection_years < 1 or projection_years > 30:
            raise ValueError("Projection years must be between 1 and 30")

        mortgage = mortgage or MortgageParams()
        expenses = expenses or ExpenseParams()

        # Calculate initial values
        down_payment = property_price * (mortgage.down_payment_percent / 100)
        loan_amount = property_price - down_payment

        yearly_breakdown: List[YearlyCashFlow] = []
        cumulative_cash_flow = 0.0
        total_principal_paid = 0.0
        current_loan_balance = loan_amount
        current_property_value = property_price
        current_monthly_rent = monthly_rent

        for year in range(1, projection_years + 1):
            # Calculate yearly income with rent growth
            annual_gross_income = current_monthly_rent * 12

            # Calculate operating expenses for the year
            vacancy_loss = annual_gross_income * (expenses.vacancy_rate / 100)
            management_fee = annual_gross_income * (expenses.management_fee_rate / 100)
            property_tax = current_property_value * (expenses.property_tax_rate / 100)
            insurance = expenses.insurance_annual
            maintenance = current_property_value * (expenses.maintenance_rate / 100)
            hoa = expenses.hoa_monthly * 12
            utilities = expenses.utilities_monthly * 12
            other = expenses.other_monthly * 12

            annual_operating_expenses = (
                vacancy_loss
                + management_fee
                + property_tax
                + insurance
                + maintenance
                + hoa
                + utilities
                + other
            )

            # Net Operating Income
            annual_noi = annual_gross_income - annual_operating_expenses

            # Calculate annual mortgage payment and interest/principal split
            monthly_mortgage = FinancialCalculator.calculate_mortgage_payment(
                loan_amount, mortgage.interest_rate, mortgage.loan_term_years
            )
            annual_mortgage = monthly_mortgage * 12

            # Calculate interest and principal for this year
            annual_interest = current_loan_balance * (mortgage.interest_rate / 100)
            annual_principal = min(annual_mortgage - annual_interest, current_loan_balance)
            if annual_principal < 0:
                annual_principal = 0

            # Update loan balance
            current_loan_balance = max(0, current_loan_balance - annual_principal)
            total_principal_paid += annual_principal

            # Annual cash flow
            annual_cash_flow = annual_noi - annual_mortgage
            cumulative_cash_flow += annual_cash_flow

            # Update property value with appreciation
            current_property_value *= 1 + (appreciation_rate / 100)

            # Calculate equity
            current_equity = current_property_value - current_loan_balance

            yearly_breakdown.append(
                YearlyCashFlow(
                    year=year,
                    gross_income=round(annual_gross_income, 2),
                    operating_expenses=round(annual_operating_expenses, 2),
                    mortgage_payment=round(annual_mortgage, 2),
                    noi=round(annual_noi, 2),
                    cash_flow=round(annual_cash_flow, 2),
                    cumulative_cash_flow=round(cumulative_cash_flow, 2),
                    property_value=round(current_property_value, 2),
                    equity=round(current_equity, 2),
                    loan_balance=round(current_loan_balance, 2),
                )
            )

            # Increase rent for next year
            current_monthly_rent *= 1 + (rent_growth_rate / 100)

        # Calculate final equity
        final_equity = current_property_value - current_loan_balance

        # Calculate IRR (simplified - using cash flows vs initial investment)
        irr = InvestmentAnalyticsCalculator._calculate_irr(
            initial_investment=down_payment + property_price * 0.02,  # down + closing
            yearly_cash_flows=[y.cash_flow for y in yearly_breakdown],
            final_value=final_equity,
        )

        return CashFlowProjection(
            property_price=property_price,
            projection_years=projection_years,
            yearly_breakdown=yearly_breakdown,
            total_cash_flow=round(cumulative_cash_flow, 2),
            total_principal_paid=round(total_principal_paid, 2),
            final_equity=round(final_equity, 2),
            irr=irr,
        )

    @staticmethod
    def _calculate_irr(
        initial_investment: float,
        yearly_cash_flows: List[float],
        final_value: float,
        tolerance: float = 0.0001,
        max_iterations: int = 100,
    ) -> Optional[float]:
        """
        Calculate Internal Rate of Return using Newton-Raphson method.

        Args:
            initial_investment: Initial cash outflow
            yearly_cash_flows: List of annual cash flows
            final_value: Final property value/equity
            tolerance: Convergence tolerance
            max_iterations: Maximum iterations

        Returns:
            IRR as percentage or None if calculation fails
        """
        if initial_investment <= 0:
            return None

        # Append final value to last cash flow
        cash_flows = [-initial_investment] + yearly_cash_flows.copy()
        cash_flows[-1] += final_value

        # Newton-Raphson method for IRR
        rate = 0.1  # Initial guess: 10%

        for _ in range(max_iterations):
            npv = 0.0
            d_npv = 0.0  # Derivative of NPV

            for t, cf in enumerate(cash_flows):
                discount_factor = (1 + rate) ** t
                npv += cf / discount_factor
                if t > 0:
                    d_npv -= t * cf / ((1 + rate) ** (t + 1))

            if abs(npv) < tolerance:
                return round(rate * 100, 2)

            if d_npv == 0:
                break

            rate = rate - npv / d_npv

            # Bound the rate to reasonable values
            rate = max(-0.99, min(rate, 10.0))

        return round(rate * 100, 2) if abs(npv) < 0.01 else None

    @staticmethod
    def calculate_tax_implications(
        property_price: float,
        land_value_ratio: float = 0.2,
        mortgage_interest_annual: float = 0.0,
        property_tax_annual: float = 0.0,
        marginal_tax_rate: float = 0.0,
        depreciation_years: int = 27.5,
    ) -> TaxImplications:
        """
        Calculate tax benefits including depreciation.

        Args:
            property_price: Purchase price of property
            land_value_ratio: Ratio of land value to total (typically 20%)
            mortgage_interest_annual: Annual mortgage interest paid
            property_tax_annual: Annual property tax paid
            marginal_tax_rate: Investor's marginal tax rate (%)
            depreciation_years: Years over which to depreciate (27.5 for US residential)

        Returns:
            TaxImplications with deduction details
        """
        if property_price <= 0:
            raise ValueError("Property price must be greater than 0")

        # Only the building depreciates, not land
        building_value = property_price * (1 - land_value_ratio)

        # Annual depreciation (straight-line)
        annual_depreciation = building_value / depreciation_years

        # Deductible expenses
        property_tax_deduction = property_tax_annual
        mortgage_interest_deduction = mortgage_interest_annual

        # Total annual deductions
        total_annual_deductions = (
            annual_depreciation + property_tax_deduction + mortgage_interest_deduction
        )

        # Taxable income reduction (the deductions reduce taxable income)
        taxable_income_reduction = total_annual_deductions

        # Effective tax benefit (actual money saved)
        effective_tax_benefit = total_annual_deductions * (marginal_tax_rate / 100)

        return TaxImplications(
            annual_depreciation=round(annual_depreciation, 2),
            property_tax_deduction=round(property_tax_deduction, 2),
            mortgage_interest_deduction=round(mortgage_interest_deduction, 2),
            total_annual_deductions=round(total_annual_deductions, 2),
            taxable_income_reduction=round(taxable_income_reduction, 2),
            effective_tax_benefit=round(effective_tax_benefit, 2),
            depreciation_years=depreciation_years,
        )

    @staticmethod
    def calculate_appreciation_scenarios(
        property_price: float,
        years: int = 10,
        custom_rates: Optional[Dict[str, float]] = None,
    ) -> List[AppreciationScenario]:
        """
        Generate pessimistic, realistic, and optimistic appreciation scenarios.

        Args:
            property_price: Initial property value
            years: Number of years to project
            custom_rates: Optional custom rates dict like {"pessimistic": -1.0, "realistic": 4.0, "optimistic": 8.0}

        Returns:
            List of AppreciationScenario objects
        """
        if property_price <= 0:
            raise ValueError("Property price must be greater than 0")
        if years < 1 or years > 30:
            raise ValueError("Years must be between 1 and 30")

        rates = custom_rates or InvestmentAnalyticsCalculator.DEFAULT_APPRECIATION_RATES
        scenarios: List[AppreciationScenario] = []

        for scenario_name, annual_rate in rates.items():
            projected_values: Dict[int, float] = {}
            current_value = property_price

            for year in range(1, years + 1):
                current_value *= 1 + (annual_rate / 100)
                projected_values[year] = round(current_value, 2)

            total_appreciation_amount = current_value - property_price
            total_appreciation_percent = (total_appreciation_amount / property_price) * 100

            scenarios.append(
                AppreciationScenario(
                    name=scenario_name,
                    annual_rate=annual_rate,
                    projected_values=projected_values,
                    total_appreciation_percent=round(total_appreciation_percent, 2),
                    total_appreciation_amount=round(total_appreciation_amount, 2),
                )
            )

        return scenarios

    @staticmethod
    def assess_risk(
        property_price: float,
        monthly_cash_flow: float,
        cap_rate: float,
        debt_service_ratio: float,  # Annual NOI / Annual Debt Service
        vacancy_rate: float,
        market_volatility: float = 0.5,  # 0-1 scale
        loan_to_value: float = 0.8,  # LTV ratio
    ) -> RiskAssessment:
        """
        Calculate comprehensive risk score (0-100, higher = lower risk).

        Args:
            property_price: Property value
            monthly_cash_flow: Monthly cash flow (can be negative)
            cap_rate: Capitalization rate (%)
            debt_service_ratio: DSCR (Debt Service Coverage Ratio)
            vacancy_rate: Vacancy rate (%)
            market_volatility: Market volatility indicator (0=stable, 1=volatile)
            loan_to_value: Loan-to-Value ratio (0-1)

        Returns:
            RiskAssessment with scores and recommendations
        """
        risk_factors: List[str] = []
        recommendations: List[str] = []

        # 1. Market Volatility Score (higher volatility = lower score)
        market_volatility_score = 100 * (1 - market_volatility)
        if market_volatility > 0.7:
            risk_factors.append("High market volatility")
            recommendations.append("Consider waiting for market stabilization")
        elif market_volatility > 0.4:
            risk_factors.append("Moderate market volatility")

        # 2. Cash Flow Stability Score
        if monthly_cash_flow > 0:
            # Positive cash flow - score based on margin
            cash_flow_margin = (monthly_cash_flow / property_price) * 12 * 100  # Annual %
            cash_flow_stability_score = min(100, 50 + cash_flow_margin * 10)
            if cash_flow_margin < 3:
                risk_factors.append("Low cash flow margin (<3% annually)")
                recommendations.append("Build cash reserves for unexpected expenses")
        else:
            # Negative cash flow - high risk
            cash_flow_stability_score = max(0, 30 + monthly_cash_flow * 0.1)
            risk_factors.append("Negative cash flow")
            recommendations.append("Review expenses and consider rent increase")

        # 3. Debt Risk Score (based on DSCR and LTV)
        if debt_service_ratio >= 1.25:
            debt_risk_score = 100
        elif debt_service_ratio >= 1.0:
            debt_risk_score = 70 + (debt_service_ratio - 1.0) * 120
        else:
            debt_risk_score = max(0, debt_service_ratio * 70)
            risk_factors.append(f"Low DSCR ({debt_service_ratio:.2f})")
            recommendations.append("DSCR below 1.0 means expenses exceed income")

        # Adjust for LTV
        if loan_to_value > 0.9:
            debt_risk_score *= 0.7
            risk_factors.append("Very high LTV (>90%)")
        elif loan_to_value > 0.8:
            debt_risk_score *= 0.85
            risk_factors.append("High LTV (>80%)")

        # 4. Liquidity Score (based on cap rate and vacancy)
        # Higher cap rate = better return but potentially riskier market
        if 4 <= cap_rate <= 8:
            liquidity_score = 80
        elif cap_rate > 8:
            liquidity_score = 60  # High cap rate might indicate risky market
            risk_factors.append("Above-average cap rate may indicate market risk")
        else:
            liquidity_score = 70  # Low cap rate = expensive market

        # Adjust for vacancy
        if vacancy_rate > 10:
            liquidity_score *= 0.7
            risk_factors.append("High vacancy rate (>10%)")
        elif vacancy_rate > 5:
            liquidity_score *= 0.9

        liquidity_score = min(100, liquidity_score)

        # Calculate overall score (weighted average)
        weights = {
            "market": 0.15,
            "cash_flow": 0.35,
            "debt": 0.30,
            "liquidity": 0.20,
        }

        overall_score = (
            market_volatility_score * weights["market"]
            + cash_flow_stability_score * weights["cash_flow"]
            + debt_risk_score * weights["debt"]
            + liquidity_score * weights["liquidity"]
        )

        # Add general recommendations if score is low
        if overall_score < 50:
            recommendations.append("This investment carries significant risk")
            recommendations.append("Consider alternative properties or markets")
        elif overall_score < 70:
            recommendations.append("Moderate risk - ensure adequate reserves")

        return RiskAssessment(
            overall_score=round(overall_score, 1),
            market_volatility_score=round(market_volatility_score, 1),
            cash_flow_stability_score=round(cash_flow_stability_score, 1),
            debt_risk_score=round(debt_risk_score, 1),
            liquidity_score=round(liquidity_score, 1),
            risk_factors=risk_factors,
            recommendations=recommendations,
        )
