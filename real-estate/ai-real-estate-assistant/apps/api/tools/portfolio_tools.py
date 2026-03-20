"""
Portfolio analysis tools for multi-property investment analysis.

This module provides tools for:
- Portfolio metrics aggregation
- Diversification analysis
- Portfolio risk assessment
"""

from typing import Any, Dict, List, Optional

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from analytics.portfolio_analytics import (
    PortfolioAnalyticsCalculator,
    PropertyHolding,
)


class PortfolioAnalysisInput(BaseModel):
    """Input for portfolio analysis."""

    properties: List[Dict[str, Any]] = Field(
        description="List of properties with their metrics",
        min_length=1,
    )
    market_volatility_by_city: Optional[Dict[str, float]] = Field(
        default=None,
        description="Optional market volatility by city (0-1 scale)",
    )


class PortfolioMetricsResult(BaseModel):
    """Portfolio metrics result."""

    total_properties: int
    total_value: float
    total_monthly_cash_flow: float
    total_annual_cash_flow: float
    weighted_avg_cap_rate: float
    weighted_avg_yield: float


class PortfolioRiskResult(BaseModel):
    """Portfolio risk assessment result."""

    overall_risk_score: float
    geographic_diversification: float
    property_type_diversification: float
    concentration_risk: float
    cash_flow_risk: float
    recommendations: List[str]


class PortfolioAnalysisResult(BaseModel):
    """Complete portfolio analysis result."""

    metrics: PortfolioMetricsResult
    diversification: Dict[str, Any]
    risk_assessment: PortfolioRiskResult
    performance: Dict[str, float]


class PortfolioAnalyzerTool(BaseTool):
    """Tool for analyzing investment property portfolios."""

    name: str = "portfolio_analyzer"
    description: str = (
        "Analyze a portfolio of investment properties. "
        "Calculates aggregate metrics, diversification scores, and risk assessment."
    )
    args_schema: type[PortfolioAnalysisInput] = PortfolioAnalysisInput

    @staticmethod
    def calculate(
        properties: List[Dict[str, Any]],
        market_volatility_by_city: Optional[Dict[str, float]] = None,
    ) -> PortfolioAnalysisResult:
        """
        Calculate comprehensive portfolio analysis.

        Args:
            properties: List of property dicts with keys:
                - property_id: str
                - property_price: float
                - monthly_rent: float
                - property_type: str
                - city: str
                - monthly_cash_flow: float
                - cap_rate: float
            market_volatility_by_city: Optional volatility by city

        Returns:
            PortfolioAnalysisResult with metrics, diversification, and risk
        """
        # Convert to PropertyHolding objects
        holdings = [
            PropertyHolding(
                property_id=p.get("property_id", f"prop-{i}"),
                property_price=float(p.get("property_price", 0)),
                monthly_rent=float(p.get("monthly_rent", 0)),
                property_type=p.get("property_type", "apartment"),
                city=p.get("city", "Unknown"),
                monthly_cash_flow=float(p.get("monthly_cash_flow", 0)),
                cap_rate=float(p.get("cap_rate", 0)),
            )
            for i, p in enumerate(properties)
        ]

        # Calculate portfolio metrics
        metrics = PortfolioAnalyticsCalculator.calculate_portfolio_metrics(holdings)

        # Analyze diversification
        div_analysis = PortfolioAnalyticsCalculator.analyze_diversification(holdings)

        # Assess portfolio risk
        risk = PortfolioAnalyticsCalculator.assess_portfolio_risk(
            holdings, market_volatility_by_city
        )

        # Calculate performance (assuming initial investment = total value for simplicity)
        performance = PortfolioAnalyticsCalculator.calculate_portfolio_performance(
            holdings, initial_investment=metrics.total_value, holding_period_years=1.0
        )

        return PortfolioAnalysisResult(
            metrics=PortfolioMetricsResult(
                total_properties=metrics.total_properties,
                total_value=metrics.total_value,
                total_monthly_cash_flow=metrics.total_monthly_cash_flow,
                total_annual_cash_flow=metrics.total_annual_cash_flow,
                weighted_avg_cap_rate=metrics.weighted_avg_cap_rate,
                weighted_avg_yield=metrics.weighted_avg_yield,
            ),
            diversification={
                "geographic_score": div_analysis.geographic_diversification,
                "property_type_score": div_analysis.property_type_diversification,
                "city_distribution": div_analysis.city_distribution,
                "type_distribution": div_analysis.type_distribution,
                "concentration_risk": div_analysis.concentration_risk,
                "largest_holding_percent": div_analysis.largest_holding_percent,
            },
            risk_assessment=PortfolioRiskResult(
                overall_risk_score=risk.overall_risk_score,
                geographic_diversification=risk.geographic_diversification,
                property_type_diversification=risk.property_type_diversification,
                concentration_risk=risk.concentration_risk,
                cash_flow_risk=risk.cash_flow_risk,
                recommendations=risk.recommendations,
            ),
            performance=performance,
        )

    def _run(self, **kwargs: Any) -> str:
        """Execute portfolio analysis."""
        try:
            result = self.calculate(**kwargs)

            output = [
                "Portfolio Analysis Report",
                "=" * 40,
                "",
                "PORTFOLIO METRICS",
                f"  Total Properties: {result.metrics.total_properties}",
                f"  Total Value: ${result.metrics.total_value:,.2f}",
                f"  Monthly Cash Flow: ${result.metrics.total_monthly_cash_flow:,.2f}",
                f"  Annual Cash Flow: ${result.metrics.total_annual_cash_flow:,.2f}",
                f"  Avg Cap Rate: {result.metrics.weighted_avg_cap_rate:.2f}%",
                f"  Avg Yield: {result.metrics.weighted_avg_yield:.2f}%",
                "",
                "DIVERSIFICATION",
                f"  Geographic Score: {result.diversification['geographic_score']:.1f}/100",
                f"  Property Type Score: {result.diversification['property_type_score']:.1f}/100",
                f"  Concentration Risk: {result.diversification['concentration_risk']:.1f}%",
                "",
                "RISK ASSESSMENT",
                f"  Overall Risk Score: {result.risk_assessment.overall_risk_score:.1f}/100",
            ]

            if result.risk_assessment.recommendations:
                output.append("  Recommendations:")
                for rec in result.risk_assessment.recommendations[:5]:
                    output.append(f"    - {rec}")

            output.extend(
                [
                    "",
                    "PERFORMANCE",
                    f"  Cash on Cash Return: {result.performance['cash_on_cash_return']:.2f}%",
                ]
            )

            return "\n".join(output)

        except Exception as e:
            return f"Portfolio Analysis Error: {str(e)}"

    async def _arun(self, **kwargs: Any) -> str:
        """Async version."""
        return self._run(**kwargs)


def create_portfolio_tools() -> List[BaseTool]:
    """Create portfolio analysis tools."""
    return [PortfolioAnalyzerTool()]
