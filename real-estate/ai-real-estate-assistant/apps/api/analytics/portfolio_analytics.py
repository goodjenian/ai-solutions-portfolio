"""
Portfolio analytics for multi-property investment analysis.

This module provides calculators for:
- Aggregate portfolio metrics
- Diversification scoring
- Portfolio-level risk assessment
"""

import logging
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes for Portfolio
# ============================================================================


@dataclass
class PropertyHolding:
    """A single property in a portfolio."""

    property_id: str
    property_price: float
    monthly_rent: float
    property_type: str  # apartment, house, commercial, etc.
    city: str
    monthly_cash_flow: float
    cap_rate: float
    property_type_category: str = "residential"  # residential, commercial, mixed


@dataclass
class PortfolioMetrics:
    """Aggregate metrics for a portfolio."""

    total_properties: int
    total_value: float
    total_monthly_cash_flow: float
    total_annual_cash_flow: float
    weighted_avg_cap_rate: float
    weighted_avg_yield: float
    total_equity: Optional[float] = None
    total_debt: Optional[float] = None


@dataclass
class DiversificationAnalysis:
    """Analysis of portfolio diversification."""

    geographic_diversification: float  # 0-100 score
    property_type_diversification: float  # 0-100 score
    city_distribution: Dict[str, int]  # city -> count
    type_distribution: Dict[str, int]  # type -> count
    concentration_risk: float  # 0-100 (higher = more concentrated = more risk)
    largest_holding_percent: float  # % of portfolio in single largest property


@dataclass
class PortfolioRiskAssessment:
    """Portfolio-level risk assessment."""

    overall_risk_score: float  # 0-100 (higher = lower risk)
    geographic_diversification: float  # 0-100
    property_type_diversification: float  # 0-100
    concentration_risk: float  # 0-100
    cash_flow_risk: float  # 0-100
    recommendations: List[str] = field(default_factory=list)


# ============================================================================
# Portfolio Analytics Calculator
# ============================================================================


class PortfolioAnalyticsCalculator:
    """Calculator for portfolio-level analytics."""

    @staticmethod
    def calculate_portfolio_metrics(
        holdings: List[PropertyHolding],
        total_equity: Optional[float] = None,
        total_debt: Optional[float] = None,
    ) -> PortfolioMetrics:
        """
        Calculate aggregate portfolio metrics.

        Args:
            holdings: List of property holdings
            total_equity: Optional total equity across all properties
            total_debt: Optional total debt across all properties

        Returns:
            PortfolioMetrics with aggregated values
        """
        if not holdings:
            return PortfolioMetrics(
                total_properties=0,
                total_value=0.0,
                total_monthly_cash_flow=0.0,
                total_annual_cash_flow=0.0,
                weighted_avg_cap_rate=0.0,
                weighted_avg_yield=0.0,
                total_equity=total_equity,
                total_debt=total_debt,
            )

        total_value = sum(h.property_price for h in holdings)
        total_monthly_cash_flow = sum(h.monthly_cash_flow for h in holdings)
        total_annual_cash_flow = total_monthly_cash_flow * 12

        # Weighted average cap rate (weighted by property value)
        weighted_cap_rate = 0.0
        weighted_yield = 0.0

        for holding in holdings:
            weight = holding.property_price / total_value if total_value > 0 else 0
            weighted_cap_rate += holding.cap_rate * weight
            # Calculate yield (annual rent / property value)
            annual_yield = (
                (holding.monthly_rent * 12 / holding.property_price * 100)
                if holding.property_price > 0
                else 0
            )
            weighted_yield += annual_yield * weight

        return PortfolioMetrics(
            total_properties=len(holdings),
            total_value=round(total_value, 2),
            total_monthly_cash_flow=round(total_monthly_cash_flow, 2),
            total_annual_cash_flow=round(total_annual_cash_flow, 2),
            weighted_avg_cap_rate=round(weighted_cap_rate, 2),
            weighted_avg_yield=round(weighted_yield, 2),
            total_equity=round(total_equity, 2) if total_equity else None,
            total_debt=round(total_debt, 2) if total_debt else None,
        )

    @staticmethod
    def analyze_diversification(holdings: List[PropertyHolding]) -> DiversificationAnalysis:
        """
        Analyze portfolio diversification across geography and property types.

        Args:
            holdings: List of property holdings

        Returns:
            DiversificationAnalysis with scores and distributions
        """
        if not holdings:
            return DiversificationAnalysis(
                geographic_diversification=0.0,
                property_type_diversification=0.0,
                city_distribution={},
                type_distribution={},
                concentration_risk=100.0,
                largest_holding_percent=0.0,
            )

        total_value = sum(h.property_price for h in holdings)

        # City distribution
        city_counter: Counter = Counter()
        city_values: Dict[str, float] = {}

        for holding in holdings:
            city_counter[holding.city] += 1
            city_values[holding.city] = city_values.get(holding.city, 0) + holding.property_price

        city_distribution = dict(city_counter)

        # Property type distribution
        type_counter: Counter = Counter()
        type_values: Dict[str, float] = {}

        for holding in holdings:
            type_counter[holding.property_type] += 1
            type_values[holding.property_type] = (
                type_values.get(holding.property_type, 0) + holding.property_price
            )

        type_distribution = dict(type_counter)

        # Calculate geographic diversification (Herfindahl-Hirschman Index based)
        # HHI ranges from 1/n to 1, where lower = more diversified
        num_cities = len(city_distribution)
        if num_cities == 1:
            geo_hhi = 1.0
        else:
            geo_hhi = sum((v / total_value) ** 2 for v in city_values.values())

        # Convert HHI to score (1 = concentrated, 0 = perfectly diversified)
        # Invert and scale to 0-100
        geographic_diversification = (
            round((1 - geo_hhi) * 100 / (1 - 1 / num_cities)) if num_cities > 1 else 0
        )

        # Calculate property type diversification
        num_types = len(type_distribution)
        if num_types == 1:
            type_hhi = 1.0
        else:
            type_hhi = sum((v / total_value) ** 2 for v in type_values.values())

        property_type_diversification = (
            round((1 - type_hhi) * 100 / (1 - 1 / num_types)) if num_types > 1 else 0
        )

        # Calculate concentration risk (largest holding as % of portfolio)
        largest_holding = max(h.property_price for h in holdings)
        largest_holding_percent = (largest_holding / total_value * 100) if total_value > 0 else 0

        # Concentration risk score (higher = more risk)
        if largest_holding_percent > 50:
            concentration_risk = 80
        elif largest_holding_percent > 30:
            concentration_risk = 60
        elif largest_holding_percent > 20:
            concentration_risk = 40
        else:
            concentration_risk = 20

        return DiversificationAnalysis(
            geographic_diversification=min(100, geographic_diversification),
            property_type_diversification=min(100, property_type_diversification),
            city_distribution=city_distribution,
            type_distribution=type_distribution,
            concentration_risk=concentration_risk,
            largest_holding_percent=round(largest_holding_percent, 1),
        )

    @staticmethod
    def assess_portfolio_risk(
        holdings: List[PropertyHolding],
        market_volatility_by_city: Optional[Dict[str, float]] = None,
    ) -> PortfolioRiskAssessment:
        """
        Assess portfolio-level risk.

        Args:
            holdings: List of property holdings
            market_volatility_by_city: Optional dict of city -> volatility (0-1)

        Returns:
            PortfolioRiskAssessment with scores and recommendations
        """
        if not holdings:
            return PortfolioRiskAssessment(
                overall_risk_score=0.0,
                geographic_diversification=0.0,
                property_type_diversification=0.0,
                concentration_risk=100.0,
                cash_flow_risk=100.0,
                recommendations=["Add properties to your portfolio to begin analysis"],
            )

        recommendations: List[str] = []

        # Get diversification analysis
        div_analysis = PortfolioAnalyticsCalculator.analyze_diversification(holdings)

        # Calculate cash flow risk
        positive_cash_flow_count = sum(1 for h in holdings if h.monthly_cash_flow > 0)
        cash_flow_ratio = positive_cash_flow_count / len(holdings)

        total_monthly_cash_flow = sum(h.monthly_cash_flow for h in holdings)
        if total_monthly_cash_flow > 0:
            cash_flow_risk = 20 + cash_flow_ratio * 60  # 20-80 range
        else:
            cash_flow_risk = 80
            recommendations.append("Portfolio has negative overall cash flow")

        # Adjust for market volatility if provided
        if market_volatility_by_city:
            total_value = sum(h.property_price for h in holdings)
            weighted_volatility = 0.0

            for holding in holdings:
                city_volatility = market_volatility_by_city.get(holding.city, 0.5)
                weight = holding.property_price / total_value if total_value > 0 else 0
                weighted_volatility += city_volatility * weight

            # High volatility increases risk
            if weighted_volatility > 0.7:
                cash_flow_risk = min(100, cash_flow_risk + 15)
                recommendations.append("High market volatility in portfolio locations")
            elif weighted_volatility > 0.4:
                cash_flow_risk = min(100, cash_flow_risk + 5)

        # Calculate overall risk score (inverse - higher = safer)
        # We want: high diversification = high score, high concentration = low score
        weights = {
            "geo_diversification": 0.25,
            "type_diversification": 0.20,
            "concentration": 0.25,  # inverted
            "cash_flow": 0.30,
        }

        # Concentration risk is inverted (high concentration = low score)
        concentration_score = 100 - div_analysis.concentration_risk

        overall_score = (
            div_analysis.geographic_diversification * weights["geo_diversification"]
            + div_analysis.property_type_diversification * weights["type_diversification"]
            + concentration_score * weights["concentration"]
            + (100 - cash_flow_risk) * weights["cash_flow"]
        )

        # Generate recommendations
        if div_analysis.geographic_diversification < 30:
            recommendations.append("Consider diversifying across more cities/regions")

        if div_analysis.property_type_diversification < 30:
            recommendations.append("Consider diversifying across different property types")

        if div_analysis.concentration_risk > 60:
            recommendations.append(
                f"Largest property is {div_analysis.largest_holding_percent}% of portfolio - consider rebalancing"
            )

        if overall_score < 40:
            recommendations.append("Portfolio carries significant risk - review holdings")
        elif overall_score > 70 and not recommendations:
            recommendations.append("Well-diversified portfolio with good risk profile")

        return PortfolioRiskAssessment(
            overall_risk_score=round(overall_score, 1),
            geographic_diversification=div_analysis.geographic_diversification,
            property_type_diversification=div_analysis.property_type_diversification,
            concentration_risk=div_analysis.concentration_risk,
            cash_flow_risk=round(cash_flow_risk, 1),
            recommendations=recommendations
            if recommendations
            else ["Portfolio risk is within acceptable range"],
        )

    @staticmethod
    def calculate_portfolio_performance(
        holdings: List[PropertyHolding],
        initial_investment: float,
        holding_period_years: float = 1.0,
    ) -> Dict[str, float]:
        """
        Calculate portfolio performance metrics.

        Args:
            holdings: List of property holdings
            initial_investment: Total initial investment
            holding_period_years: How long properties have been held

        Returns:
            Dict with performance metrics
        """
        if not holdings or initial_investment <= 0:
            return {
                "total_return": 0.0,
                "annualized_return": 0.0,
                "cash_on_cash_return": 0.0,
                "appreciation": 0.0,
            }

        total_value = sum(h.property_price for h in holdings)
        total_annual_cash_flow = sum(h.monthly_cash_flow for h in holdings) * 12

        # Assume 3% annual appreciation for current value estimation
        appreciation_rate = 0.03
        estimated_original_value = total_value / ((1 + appreciation_rate) ** holding_period_years)
        appreciation = total_value - estimated_original_value

        # Total return = cash flow + appreciation
        total_return = (
            (total_annual_cash_flow * holding_period_years + appreciation)
            / initial_investment
            * 100
        )

        # Annualized return
        if holding_period_years > 0:
            annualized_return = ((1 + total_return / 100) ** (1 / holding_period_years) - 1) * 100
        else:
            annualized_return = total_return

        # Cash on cash return
        cash_on_cash = (
            (total_annual_cash_flow / initial_investment) * 100 if initial_investment > 0 else 0
        )

        return {
            "total_return": round(total_return, 2),
            "annualized_return": round(annualized_return, 2),
            "cash_on_cash_return": round(cash_on_cash, 2),
            "appreciation": round(appreciation, 2),
        }
