"""
Financial metrics and investment analysis for real estate properties.

This module provides calculators for:
- Mortgage payments
- Rental yields (Gross/Net)
- Cash on Cash return
- Cap Rate
- Detailed expense breakdown
"""

import logging
from dataclasses import dataclass
from typing import Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class MortgageParams:
    """Parameters for mortgage calculation."""

    interest_rate: float = 5.0  # Annual percentage (e.g., 5.0 for 5%)
    loan_term_years: int = 30
    down_payment_percent: float = 20.0  # e.g., 20.0 for 20%


@dataclass
class ExpenseParams:
    """Parameters for operating expenses."""

    property_tax_rate: float = 1.0  # Annual % of property value
    insurance_annual: float = 0.0
    maintenance_rate: float = 1.0  # Annual % of property value
    vacancy_rate: float = 5.0  # % of potential rental income
    management_fee_rate: float = 0.0  # % of collected rent
    hoa_monthly: float = 0.0
    utilities_monthly: float = 0.0
    other_monthly: float = 0.0


@dataclass
class InvestmentMetrics:
    """Result of investment analysis."""

    gross_yield: float  # %
    net_yield: float  # %
    cap_rate: float  # %
    cash_on_cash_return: float  # %

    monthly_income: float
    monthly_expenses: float
    monthly_mortgage: float
    monthly_cash_flow: float

    total_initial_investment: float
    annual_noi: float  # Net Operating Income

    expense_breakdown: Dict[str, float]


class FinancialCalculator:
    """Calculator for real estate financial metrics."""

    @staticmethod
    def calculate_mortgage_payment(principal: float, annual_rate: float, years: int) -> float:
        """
        Calculate monthly mortgage payment (Principal + Interest).
        Formula: M = P [ i(1 + i)^n ] / [ (1 + i)^n – 1 ]
        """
        if principal <= 0:
            return 0.0
        if annual_rate <= 0:
            return principal / (years * 12)
        if years <= 0:
            return principal  # Edge case, assume immediate repayment? Or error. Returning principal for safety.

        monthly_rate = annual_rate / 100 / 12
        num_payments = years * 12

        numerator = monthly_rate * ((1 + monthly_rate) ** num_payments)
        denominator = ((1 + monthly_rate) ** num_payments) - 1

        return principal * (numerator / denominator)

    @staticmethod
    def analyze_investment(
        property_price: float,
        monthly_rent: float,
        mortgage: Optional[MortgageParams] = None,
        expenses: Optional[ExpenseParams] = None,
    ) -> InvestmentMetrics:
        """
        Perform comprehensive investment analysis.
        """
        if property_price <= 0:
            raise ValueError("Property price must be greater than 0")

        mortgage = mortgage or MortgageParams()
        expenses = expenses or ExpenseParams()

        # 1. Initial Investment
        down_payment = property_price * (mortgage.down_payment_percent / 100)
        loan_amount = property_price - down_payment
        closing_costs = property_price * 0.02  # Estimated 2% closing costs
        total_initial_investment = down_payment + closing_costs

        # 2. Income
        annual_gross_rent = monthly_rent * 12
        potential_gross_income = annual_gross_rent

        # 3. Operating Expenses
        vacancy_loss = (potential_gross_income * (expenses.vacancy_rate / 100)) / 12
        management_fee = monthly_rent * (expenses.management_fee_rate / 100)
        property_tax_monthly = (property_price * (expenses.property_tax_rate / 100)) / 12
        insurance_monthly = expenses.insurance_annual / 12
        maintenance_monthly = (property_price * (expenses.maintenance_rate / 100)) / 12

        monthly_operating_expenses = (
            vacancy_loss
            + management_fee
            + property_tax_monthly
            + insurance_monthly
            + maintenance_monthly
            + expenses.hoa_monthly
            + expenses.utilities_monthly
            + expenses.other_monthly
        )

        annual_operating_expenses = monthly_operating_expenses * 12

        # 4. Net Operating Income (NOI)
        annual_noi = annual_gross_rent - annual_operating_expenses

        # 5. Debt Service
        monthly_mortgage = FinancialCalculator.calculate_mortgage_payment(
            loan_amount, mortgage.interest_rate, mortgage.loan_term_years
        )
        annual_debt_service = monthly_mortgage * 12

        # 6. Cash Flow
        annual_cash_flow = annual_noi - annual_debt_service
        monthly_cash_flow = annual_cash_flow / 12

        # 7. Metrics
        gross_yield = (annual_gross_rent / property_price) * 100
        net_yield = (
            annual_noi / property_price
        ) * 100  # Often synonymous with Cap Rate if calculated on full price
        cap_rate = (annual_noi / property_price) * 100

        cash_on_cash = 0.0
        if total_initial_investment > 0:
            cash_on_cash = (annual_cash_flow / total_initial_investment) * 100

        expense_breakdown = {
            "vacancy": vacancy_loss,
            "management": management_fee,
            "tax": property_tax_monthly,
            "insurance": insurance_monthly,
            "maintenance": maintenance_monthly,
            "hoa": expenses.hoa_monthly,
            "utilities": expenses.utilities_monthly,
            "other": expenses.other_monthly,
            "mortgage": monthly_mortgage,
        }

        return InvestmentMetrics(
            gross_yield=round(gross_yield, 2),
            net_yield=round(net_yield, 2),
            cap_rate=round(cap_rate, 2),
            cash_on_cash_return=round(cash_on_cash, 2),
            monthly_income=monthly_rent,
            monthly_expenses=round(monthly_operating_expenses, 2),
            monthly_mortgage=round(monthly_mortgage, 2),
            monthly_cash_flow=round(monthly_cash_flow, 2),
            total_initial_investment=round(total_initial_investment, 2),
            annual_noi=round(annual_noi, 2),
            expense_breakdown=expense_breakdown,
        )
