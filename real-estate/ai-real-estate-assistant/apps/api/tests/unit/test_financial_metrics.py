import unittest

from analytics.financial_metrics import ExpenseParams, FinancialCalculator, MortgageParams


class TestFinancialCalculator(unittest.TestCase):
    def test_mortgage_calculation_standard(self):
        # 100,000 principal, 5% rate, 30 years
        # Expected: ~536.82
        payment = FinancialCalculator.calculate_mortgage_payment(100000, 5.0, 30)
        self.assertAlmostEqual(payment, 536.82, places=2)

    def test_mortgage_calculation_zero_interest(self):
        # 120,000 principal, 0% rate, 10 years
        # Expected: 1000/mo
        payment = FinancialCalculator.calculate_mortgage_payment(120000, 0.0, 10)
        self.assertAlmostEqual(payment, 1000.0, places=2)

    def test_mortgage_calculation_zero_principal(self):
        payment = FinancialCalculator.calculate_mortgage_payment(0, 5.0, 30)
        self.assertEqual(payment, 0.0)

    def test_analyze_investment_basic(self):
        # Price: 100,000
        # Rent: 1,000/mo -> 12,000/yr
        # Gross Yield: 12%

        metrics = FinancialCalculator.analyze_investment(
            property_price=100000,
            monthly_rent=1000,
            mortgage=MortgageParams(down_payment_percent=100),  # All cash
            expenses=ExpenseParams(
                property_tax_rate=0,
                insurance_annual=0,
                maintenance_rate=0,
                vacancy_rate=0,
                management_fee_rate=0,
            ),
        )

        self.assertEqual(metrics.gross_yield, 12.0)
        self.assertEqual(metrics.net_yield, 12.0)
        self.assertEqual(metrics.monthly_mortgage, 0.0)
        self.assertEqual(metrics.monthly_cash_flow, 1000.0)

    def test_analyze_investment_with_expenses_and_mortgage(self):
        # Price: 200,000
        # Rent: 2,000/mo -> 24,000/yr
        # Down: 20% -> 40k. Loan: 160k.
        # Rate: 5%, 30yr -> Mortgage: ~858.91
        # Expenses:
        #   Tax: 1% -> 2,000/yr -> 166.67/mo
        #   Vacancy: 5% -> 100/mo
        #   Maintenance: 1% -> 166.67/mo

        metrics = FinancialCalculator.analyze_investment(
            property_price=200000,
            monthly_rent=2000,
            mortgage=MortgageParams(interest_rate=5.0, loan_term_years=30, down_payment_percent=20),
            expenses=ExpenseParams(
                property_tax_rate=1.0,
                maintenance_rate=1.0,
                vacancy_rate=5.0,
                insurance_annual=0,
                management_fee_rate=0,
            ),
        )

        self.assertEqual(metrics.gross_yield, 12.0)

        # Expenses check
        # Tax: 166.67
        # Maint: 166.67
        # Vacancy: 100.00
        # Total Ops: 433.34
        self.assertAlmostEqual(metrics.monthly_expenses, 433.33, delta=0.1)

        # Mortgage check
        self.assertAlmostEqual(metrics.monthly_mortgage, 858.91, delta=0.1)

        # Cash Flow
        # 2000 - 433.33 - 858.91 = 707.76
        self.assertAlmostEqual(metrics.monthly_cash_flow, 707.76, delta=0.2)

        # Cash on Cash
        # Invested: 40k + 2% closing (4k) = 44k
        # Annual CF: ~8493
        # CoC: (8493 / 44000) * 100 = ~19.3%
        self.assertGreater(metrics.cash_on_cash_return, 19.0)
        self.assertLess(metrics.cash_on_cash_return, 20.0)

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            FinancialCalculator.analyze_investment(0, 1000)


if __name__ == "__main__":
    unittest.main()
