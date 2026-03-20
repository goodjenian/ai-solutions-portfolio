"""
TradAI — API wrapper for stock_analysis crewAI crew.

Run:
    pip install -e ../../_shared
    uvicorn api_server:app --port 8005 --reload
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "_shared"))

from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field

from goodyseo_security.auth import get_api_key
from goodyseo_security.cost_guard import BudgetExceededError
from goodyseo_security.gateway import create_app
from goodyseo_security.rate_limiter import client_key

app, guard = create_app(
    title="TradAI",
    tool_name="stock_analysis",
    daily_budget_usd=15.0,   # stock analysis is GPT-4 heavy
    rate_limit_rpm=3,
)

_DISCLAIMER = (
    "⚠️ DISCLAIMER: This analysis is AI-generated and for informational purposes only. "
    "It does not constitute financial advice. Past performance is not indicative of "
    "future results. Always consult a qualified financial advisor before investing."
)


class AnalysisRequest(BaseModel):
    stock_symbol: str = Field(..., pattern=r"^[A-Z]{1,5}$",
                              description="Stock ticker symbol (e.g. AAPL, TSLA)")


class AnalysisResponse(BaseModel):
    symbol: str
    report: str
    disclaimer: str
    cost_usd: float
    duration_s: float


@app.post("/run", response_model=AnalysisResponse, tags=["TradAI"])
async def analyse_stock(
    payload: AnalysisRequest,
    api_key: str = Depends(get_api_key),
):
    """
    Generate a detailed stock analysis report including SEC 10-K/10-Q data.

    ⚠️ Not financial advice. See disclaimer in response.
    """
    ck = client_key(api_key)
    allowed, _, _, reset = app.state.rate_limiter.check(ck)
    if not allowed:
        raise HTTPException(429, detail=f"Rate limit. Retry in {reset}s.",
                            headers={"Retry-After": str(reset)})

    start = time.perf_counter()
    try:
        from src.stock_analysis.crew import StockAnalysisCrew  # type: ignore[import]

        crew = StockAnalysisCrew()
        result = crew.crew().kickoff(inputs={"stock_symbol": payload.stock_symbol})
        report = str(result)
        duration = time.perf_counter() - start

        est_tokens = len(report) // 4 + 3000  # SEC docs are large
        cost = guard.check_and_record(ck, "gpt-4o", est_tokens, est_tokens,
                                      tool_name="stock_analysis")

        return AnalysisResponse(
            symbol=payload.stock_symbol,
            report=report,
            disclaimer=_DISCLAIMER,
            cost_usd=cost,
            duration_s=round(duration, 2),
        )

    except BudgetExceededError as e:
        raise HTTPException(402, detail=f"Daily budget ${e.limit:.2f} exhausted.")
    except Exception as e:
        raise HTTPException(500, detail=f"Agent error: {e}")


@app.get("/usage/me", tags=["Billing"])
async def my_usage(api_key: str = Depends(get_api_key)):
    return guard.get_usage(client_key(api_key))
