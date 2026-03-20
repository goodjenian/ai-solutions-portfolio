"""
InboxAI — API wrapper for email_auto_responder_flow.

Run:
    pip install -e ../../_shared
    uvicorn api_server:app --port 8003 --reload

IMPORTANT: Requires Gmail OAuth credentials.json in this directory.
           See README for Gmail API setup.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "_shared"))

from fastapi import BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from goodyseo_security.auth import get_api_key
from goodyseo_security.cost_guard import BudgetExceededError
from goodyseo_security.gateway import create_app
from goodyseo_security.rate_limiter import client_key

app, guard = create_app(
    title="InboxAI",
    tool_name="email_auto_responder",
    daily_budget_usd=3.0,
    rate_limit_rpm=6,
)


class RunResponse(BaseModel):
    status: str
    emails_processed: int
    drafts_created: int
    cost_usd: float
    duration_s: float


@app.post("/run", response_model=RunResponse, tags=["InboxAI"])
async def run_responder(api_key: str = Depends(get_api_key)):
    """
    Trigger one cycle: check for new emails, generate draft replies.

    This is a synchronous single-pass run. For continuous background mode,
    use the background task endpoint or run the original main.py directly.
    """
    ck = client_key(api_key)
    allowed, _, _, reset = app.state.rate_limiter.check(ck)
    if not allowed:
        raise HTTPException(429, detail=f"Rate limit. Retry in {reset}s.",
                            headers={"Retry-After": str(reset)})

    start = time.perf_counter()
    try:
        from src.email_auto_responder_flow.main import EmailAutoResponderFlow  # type: ignore[import]

        flow = EmailAutoResponderFlow()
        # Run one pass (not the continuous loop)
        flow.kickoff()
        duration = time.perf_counter() - start

        # Cost estimation: email flows are lighter than strategy crews
        est_tokens = 2000  # conservative per-run estimate
        cost = guard.check_and_record(ck, "gpt-4o-mini", est_tokens, est_tokens,
                                      tool_name="email_auto_responder")

        return RunResponse(
            status="completed",
            emails_processed=getattr(flow.state, "emails_checked", 0),
            drafts_created=getattr(flow.state, "drafts_created", 0),
            cost_usd=cost,
            duration_s=round(duration, 2),
        )

    except BudgetExceededError as e:
        raise HTTPException(402, detail=f"Daily budget ${e.limit:.2f} exhausted.")
    except Exception as e:
        raise HTTPException(500, detail=f"Flow error: {e}")


@app.get("/usage/me", tags=["Billing"])
async def my_usage(api_key: str = Depends(get_api_key)):
    return guard.get_usage(client_key(api_key))
