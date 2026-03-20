"""
ContentFlow — API wrapper for instagram_post crewAI crew.

Run:
    pip install -e ../../_shared
    uvicorn api_server:app --port 8002 --reload
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
    title="ContentFlow",
    tool_name="instagram_post",
    daily_budget_usd=8.0,
    rate_limit_rpm=10,
)


class PostRequest(BaseModel):
    product_website: str = Field(..., description="Product/brand URL")
    extra_details: str = Field("", description="Style, tone, target audience, campaign theme")


class PostResponse(BaseModel):
    copy: str
    image_prompt: str
    cost_usd: float
    duration_s: float


@app.post("/run", response_model=PostResponse, tags=["ContentFlow"])
async def create_post(
    payload: PostRequest,
    api_key: str = Depends(get_api_key),
):
    """
    Generate an Instagram post (copy + Midjourney image prompt) for a product.
    """
    ck = client_key(api_key)
    allowed, _, _, reset = app.state.rate_limiter.check(ck)
    if not allowed:
        raise HTTPException(429, detail=f"Rate limit. Retry in {reset}s.",
                            headers={"Retry-After": str(reset)})

    start = time.perf_counter()
    try:
        from agents import MarketingAnalysisAgents  # type: ignore[import]
        from tasks import MarketingAnalysisTasks   # type: ignore[import]
        from crewai import Crew

        agents = MarketingAnalysisAgents()
        tasks = MarketingAnalysisTasks()

        product_competitor_agent = agents.product_competitor_agent()
        strategy_planner_agent = agents.strategy_planner_agent()
        creative_agent = agents.creative_content_creator_agent()

        website_analysis = tasks.product_analysis(
            product_competitor_agent, payload.product_website, payload.extra_details)
        market_analysis = tasks.competitor_analysis(
            product_competitor_agent, payload.product_website, payload.extra_details)
        campaign_dev = tasks.campaign_development(
            strategy_planner_agent, payload.product_website, payload.extra_details)
        write_copy = tasks.instagram_ad_copy(creative_agent)

        copy_crew = Crew(
            agents=[product_competitor_agent, strategy_planner_agent, creative_agent],
            tasks=[website_analysis, market_analysis, campaign_dev, write_copy],
            verbose=False,
        )
        ad_copy = copy_crew.kickoff()

        senior_photographer = agents.senior_photographer_agent()
        chief_director = agents.chief_creative_diretor_agent()
        take_photo = tasks.take_photograph_task(
            senior_photographer, ad_copy, payload.product_website, payload.extra_details)
        approve_photo = tasks.review_photo(
            chief_director, payload.product_website, payload.extra_details)

        image_crew = Crew(
            agents=[senior_photographer, chief_director],
            tasks=[take_photo, approve_photo],
            verbose=False,
        )
        image = image_crew.kickoff()
        duration = time.perf_counter() - start

        combined = str(ad_copy) + str(image)
        est_tokens = len(combined) // 4
        cost = guard.check_and_record(ck, "gpt-4o", est_tokens, est_tokens,
                                      tool_name="instagram_post")

        return PostResponse(
            copy=str(ad_copy),
            image_prompt=str(image),
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
