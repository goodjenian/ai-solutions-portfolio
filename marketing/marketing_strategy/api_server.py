"""
StrategyAI — API wrapper for marketing_strategy crewAI crew.

Run:
    pip install -e ../../_shared
    uvicorn api_server:app --port 8001 --reload

Auth: X-API-Key header (set API_ACCESS_KEY in .env)
"""

import sys
import time
from pathlib import Path

# Make shared package importable without installing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "_shared"))

from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field

from goodyseo_security.auth import get_api_key
from goodyseo_security.cost_guard import BudgetExceededError
from goodyseo_security.gateway import create_app
from goodyseo_security.rate_limiter import client_key

app, guard = create_app(
    title="StrategyAI",
    tool_name="marketing_strategy",
    daily_budget_usd=10.0,   # $10/day per client — adjust per plan tier
    rate_limit_rpm=5,         # max 5 strategy runs/min
)


class StrategyRequest(BaseModel):
    product_website: str = Field(..., description="URL of the product/brand to analyse")
    extra_details: str = Field("", description="Additional context (target audience, goals, etc.)")


class StrategyResponse(BaseModel):
    ad_copy: str
    image_prompt: str
    cost_usd: float
    duration_s: float


@app.post("/run", response_model=StrategyResponse, tags=["StrategyAI"])
async def run_strategy(
    payload: StrategyRequest,
    api_key: str = Depends(get_api_key),
):
    """
    Generate a full marketing strategy + Instagram ad copy for a product.

    Returns AI-generated copy and a Midjourney image prompt.
    Billed against the client's daily budget.
    """
    ck = client_key(api_key)
    allowed, limit, remaining, reset = app.state.rate_limiter.check(ck)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Retry in {reset}s.",
            headers={"Retry-After": str(reset)},
        )

    start = time.perf_counter()
    try:
        # Lazy import to keep startup fast
        from src.marketing_posts.crew import MarketingPostsCrew  # type: ignore[import]

        crew = MarketingPostsCrew()
        inputs = {
            "customer_domain": payload.product_website,
            "project_description": payload.extra_details,
        }
        result = crew.crew().kickoff(inputs=inputs)
        ad_copy = str(result)
        image_prompt = ""  # crews that return structured output can split here

        duration = time.perf_counter() - start

        # Estimate tokens (crewAI does not expose exact counts yet)
        # Using a rough heuristic: 1 token ≈ 4 chars
        est_tokens = len(ad_copy) // 4
        cost = guard.check_and_record(ck, "gpt-4o", est_tokens, est_tokens,
                                      tool_name="marketing_strategy")

        return StrategyResponse(
            ad_copy=ad_copy,
            image_prompt=image_prompt,
            cost_usd=cost,
            duration_s=round(duration, 2),
        )

    except BudgetExceededError as e:
        raise HTTPException(
            status_code=402,
            detail=f"Daily budget of ${e.limit:.2f} exhausted. "
                   "Upgrade your plan or wait until tomorrow (UTC).",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {e}")


@app.get("/usage/me", tags=["Billing"])
async def my_usage(api_key: str = Depends(get_api_key)):
    """Return the authenticated client's current daily usage."""
    return guard.get_usage(client_key(api_key))
