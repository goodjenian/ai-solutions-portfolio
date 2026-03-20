"""
Unit tests for portfolio analytics calculator.

Tests cover:
- Portfolio metrics aggregation
- Diversification analysis
- Portfolio risk assessment
"""

import pytest

from analytics.portfolio_analytics import (
    PortfolioAnalyticsCalculator,
    PropertyHolding,
)


class TestPropertyHolding:
    """Test PropertyHolding dataclass."""

    def test_create_holding(self):
        """Test creating a property holding."""
        holding = PropertyHolding(
            property_id="prop-001",
            property_price=100_000,
            monthly_rent=1_000,
            property_type="apartment",
            city="Berlin",
            monthly_cash_flow=200,
            cap_rate=5.5,
        )

        assert holding.property_id == "prop-001"
        assert holding.property_price == 100_000
        assert holding.property_type_category == "residential"  # default


class TestPortfolioMetrics:
    """Test suite for portfolio metrics calculations."""

    @pytest.fixture
    def sample_holdings(self):
        """Create sample property holdings."""
        return [
            PropertyHolding(
                property_id="prop-001",
                property_price=100_000,
                monthly_rent=1_000,
                property_type="apartment",
                city="Berlin",
                monthly_cash_flow=200,
                cap_rate=5.0,
            ),
            PropertyHolding(
                property_id="prop-002",
                property_price=200_000,
                monthly_rent=2_000,
                property_type="house",
                city="Munich",
                monthly_cash_flow=400,
                cap_rate=6.0,
            ),
            PropertyHolding(
                property_id="prop-003",
                property_price=150_000,
                monthly_rent=1_500,
                property_type="apartment",
                city="Hamburg",
                monthly_cash_flow=300,
                cap_rate=7.0,
            ),
        ]

    def test_empty_portfolio(self):
        """Test metrics with empty portfolio."""
        result = PortfolioAnalyticsCalculator.calculate_portfolio_metrics([])

        assert result.total_properties == 0
        assert result.total_value == 0
        assert result.total_monthly_cash_flow == 0

    def test_total_properties_count(self, sample_holdings):
        """Test total property count."""
        result = PortfolioAnalyticsCalculator.calculate_portfolio_metrics(sample_holdings)

        assert result.total_properties == 3

    def test_total_value_sum(self, sample_holdings):
        """Test total value is sum of all property prices."""
        result = PortfolioAnalyticsCalculator.calculate_portfolio_metrics(sample_holdings)

        expected_total = 100_000 + 200_000 + 150_000
        assert result.total_value == expected_total

    def test_total_cash_flow_sum(self, sample_holdings):
        """Test cash flow is sum of all monthly cash flows."""
        result = PortfolioAnalyticsCalculator.calculate_portfolio_metrics(sample_holdings)

        expected_monthly = 200 + 400 + 300
        expected_annual = expected_monthly * 12

        assert result.total_monthly_cash_flow == expected_monthly
        assert result.total_annual_cash_flow == expected_annual

    def test_weighted_avg_cap_rate(self, sample_holdings):
        """Test weighted average cap rate calculation."""
        result = PortfolioAnalyticsCalculator.calculate_portfolio_metrics(sample_holdings)

        # Weighted by property value
        # 100k * 5% + 200k * 6% + 150k * 7% / 450k
        # = 5000 + 12000 + 10500 / 450 = 27500/450 = 6.11%
        expected_cap = (100_000 * 5.0 + 200_000 * 6.0 + 150_000 * 7.0) / 450_000

        assert abs(result.weighted_avg_cap_rate - expected_cap) < 0.1

    def test_with_equity_and_debt(self, sample_holdings):
        """Test metrics with equity and debt values."""
        result = PortfolioAnalyticsCalculator.calculate_portfolio_metrics(
            sample_holdings,
            total_equity=300_000,
            total_debt=150_000,
        )

        assert result.total_equity == 300_000
        assert result.total_debt == 150_000


class TestDiversificationAnalysis:
    """Test suite for diversification analysis."""

    @pytest.fixture
    def diversified_holdings(self):
        """Create diversified property holdings."""
        return [
            PropertyHolding("p1", 100_000, 1_000, "apartment", "Berlin", 200, 5.0),
            PropertyHolding("p2", 100_000, 1_000, "house", "Munich", 200, 5.0),
            PropertyHolding("p3", 100_000, 1_000, "commercial", "Hamburg", 200, 5.0),
            PropertyHolding("p4", 100_000, 1_000, "apartment", "Frankfurt", 200, 5.0),
        ]

    @pytest.fixture
    def concentrated_holdings(self):
        """Create concentrated property holdings."""
        return [
            PropertyHolding("p1", 400_000, 4_000, "apartment", "Berlin", 800, 5.0),
            PropertyHolding("p2", 50_000, 500, "apartment", "Berlin", 100, 5.0),
        ]

    def test_empty_portfolio_diversification(self):
        """Test diversification with empty portfolio."""
        result = PortfolioAnalyticsCalculator.analyze_diversification([])

        assert result.geographic_diversification == 0
        assert result.concentration_risk == 100

    def test_city_distribution(self, diversified_holdings):
        """Test city distribution calculation."""
        result = PortfolioAnalyticsCalculator.analyze_diversification(diversified_holdings)

        assert result.city_distribution == {"Berlin": 1, "Munich": 1, "Hamburg": 1, "Frankfurt": 1}

    def test_type_distribution(self, diversified_holdings):
        """Test property type distribution."""
        result = PortfolioAnalyticsCalculator.analyze_diversification(diversified_holdings)

        assert result.type_distribution == {"apartment": 2, "house": 1, "commercial": 1}

    def test_diversified_portfolio_high_score(self, diversified_holdings):
        """Test that diversified portfolio has high diversification scores."""
        result = PortfolioAnalyticsCalculator.analyze_diversification(diversified_holdings)

        # 4 cities, 3 types = good diversification
        assert result.geographic_diversification > 50
        assert result.property_type_diversification > 50

    def test_concentrated_portfolio_low_score(self, concentrated_holdings):
        """Test that concentrated portfolio has low diversification scores."""
        result = PortfolioAnalyticsCalculator.analyze_diversification(concentrated_holdings)

        # 1 city, 1 type = poor diversification
        assert result.geographic_diversification < 50
        assert result.property_type_diversification == 0  # All same type

    def test_concentration_risk_calculation(self, concentrated_holdings):
        """Test concentration risk with one large property."""
        result = PortfolioAnalyticsCalculator.analyze_diversification(concentrated_holdings)

        # 400k out of 450k = 88.9% in one property
        assert result.largest_holding_percent > 80
        assert result.concentration_risk >= 60  # High risk

    def test_balanced_portfolio_low_concentration(self, diversified_holdings):
        """Test concentration with evenly distributed values."""
        result = PortfolioAnalyticsCalculator.analyze_diversification(diversified_holdings)

        # Each property is 25% of portfolio
        assert result.largest_holding_percent == 25
        assert result.concentration_risk <= 40  # Lower risk


class TestPortfolioRiskAssessment:
    """Test suite for portfolio risk assessment."""

    @pytest.fixture
    def healthy_portfolio(self):
        """Create a healthy, diversified portfolio."""
        return [
            PropertyHolding("p1", 100_000, 1_200, "apartment", "Berlin", 300, 6.0),
            PropertyHolding("p2", 100_000, 1_200, "house", "Munich", 350, 6.5),
            PropertyHolding("p3", 100_000, 1_200, "apartment", "Hamburg", 280, 5.5),
            PropertyHolding("p4", 100_000, 1_200, "commercial", "Frankfurt", 400, 7.0),
        ]

    @pytest.fixture
    def risky_portfolio(self):
        """Create a risky, concentrated portfolio with negative cash flow."""
        return [
            PropertyHolding("p1", 400_000, 2_000, "apartment", "Berlin", -500, 3.0),
            PropertyHolding("p2", 50_000, 300, "apartment", "Berlin", -100, 2.5),
        ]

    def test_empty_portfolio_risk(self):
        """Test risk assessment with empty portfolio."""
        result = PortfolioAnalyticsCalculator.assess_portfolio_risk([])

        assert result.overall_risk_score == 0
        assert len(result.recommendations) > 0

    def test_healthy_portfolio_high_score(self, healthy_portfolio):
        """Test that healthy portfolio has high risk score."""
        result = PortfolioAnalyticsCalculator.assess_portfolio_risk(healthy_portfolio)

        assert result.overall_risk_score > 50
        # Cash flow risk is based on ratio, not absolute value
        assert result.geographic_diversification > 50

    def test_risky_portfolio_low_score(self, risky_portfolio):
        """Test that risky portfolio has low risk score."""
        result = PortfolioAnalyticsCalculator.assess_portfolio_risk(risky_portfolio)

        assert result.overall_risk_score < 60
        # Check for negative cash flow message (full text)
        recommendations_text = " ".join(result.recommendations)
        assert "negative" in recommendations_text.lower()

    def test_positive_cash_flow_reduces_risk(self, healthy_portfolio):
        """Test that positive cash flow reduces portfolio risk."""
        result = PortfolioAnalyticsCalculator.assess_portfolio_risk(healthy_portfolio)

        # All properties have positive cash flow - overall score should be decent
        assert result.overall_risk_score > 50

    def test_negative_cash_flow_increases_risk(self, risky_portfolio):
        """Test that negative cash flow increases portfolio risk."""
        result = PortfolioAnalyticsCalculator.assess_portfolio_risk(risky_portfolio)

        assert result.cash_flow_risk > 50

    def test_market_volatility_adjustment(self, healthy_portfolio):
        """Test that market volatility affects risk score."""
        volatility = {"Berlin": 0.8, "Munich": 0.3, "Hamburg": 0.4, "Frankfurt": 0.2}

        result_with_volatility = PortfolioAnalyticsCalculator.assess_portfolio_risk(
            healthy_portfolio, market_volatility_by_city=volatility
        )

        result_without_volatility = PortfolioAnalyticsCalculator.assess_portfolio_risk(
            healthy_portfolio
        )

        # High volatility should increase cash flow risk
        assert result_with_volatility.cash_flow_risk >= result_without_volatility.cash_flow_risk

    def test_recommendations_generated(self, risky_portfolio):
        """Test that recommendations are generated for risky portfolio."""
        result = PortfolioAnalyticsCalculator.assess_portfolio_risk(risky_portfolio)

        assert len(result.recommendations) > 0

    def test_diversification_recommendation(self):
        """Test recommendation to diversify single-city portfolio."""
        single_city = [
            PropertyHolding("p1", 100_000, 1_000, "apartment", "Berlin", 200, 5.0),
            PropertyHolding("p2", 100_000, 1_000, "apartment", "Berlin", 200, 5.0),
            PropertyHolding("p3", 100_000, 1_000, "apartment", "Berlin", 200, 5.0),
        ]

        result = PortfolioAnalyticsCalculator.assess_portfolio_risk(single_city)

        # Should recommend geographic diversification
        recommendations_text = " ".join(result.recommendations).lower()
        assert (
            "diversif" in recommendations_text
            or "city" in recommendations_text
            or "region" in recommendations_text
        )


class TestPortfolioPerformance:
    """Test suite for portfolio performance calculations."""

    @pytest.fixture
    def sample_holdings(self):
        """Create sample holdings for performance testing."""
        return [
            PropertyHolding("p1", 110_000, 1_000, "apartment", "Berlin", 200, 5.0),
            PropertyHolding("p2", 110_000, 1_000, "apartment", "Munich", 200, 5.0),
        ]

    def test_empty_portfolio_performance(self):
        """Test performance with empty portfolio."""
        result = PortfolioAnalyticsCalculator.calculate_portfolio_performance(
            [], initial_investment=100_000
        )

        assert result["total_return"] == 0
        assert result["annualized_return"] == 0

    def test_zero_investment_performance(self, sample_holdings):
        """Test performance with zero investment."""
        result = PortfolioAnalyticsCalculator.calculate_portfolio_performance(
            sample_holdings, initial_investment=0
        )

        assert result["total_return"] == 0

    def test_cash_on_cash_return(self, sample_holdings):
        """Test cash on cash return calculation."""
        initial = 200_000
        result = PortfolioAnalyticsCalculator.calculate_portfolio_performance(
            sample_holdings, initial_investment=initial
        )

        # Annual cash flow = 400 * 12 = 4800
        # CoC = 4800 / 200000 = 2.4%
        expected_coc = (400 * 12 / initial) * 100
        assert abs(result["cash_on_cash_return"] - expected_coc) < 0.5

    def test_annualized_return_calculation(self, sample_holdings):
        """Test annualized return over multiple years."""
        initial = 200_000
        result = PortfolioAnalyticsCalculator.calculate_portfolio_performance(
            sample_holdings, initial_investment=initial, holding_period_years=3.0
        )

        # Should have positive annualized return
        assert result["annualized_return"] != 0
