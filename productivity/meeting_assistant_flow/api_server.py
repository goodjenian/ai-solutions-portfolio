"""
MeetingOps — API wrapper for meeting_assistant_flow.

Run:
    pip install -e ../../_shared
    uvicorn api_server:app --port 8004 --reload
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
    title="MeetingOps",
    tool_name="meeting_assistant",
    daily_budget_usd=3.0,
    rate_limit_rpm=5,
)


class MeetingRequest(BaseModel):
    meeting_notes: str = Field(
        ...,
        max_length=20_000,  # hard cap — prevents accidental huge inputs
        description="Raw meeting transcript or notes (max 20,000 chars)",
    )
    push_to_trello: bool = Field(True, description="Create Trello cards for action items")
    notify_slack: bool = Field(True, description="Send summary to Slack channel")


class MeetingResponse(BaseModel):
    summary: str
    tasks_created: int
    slack_notified: bool
    cost_usd: float
    duration_s: float


@app.post("/run", response_model=MeetingResponse, tags=["MeetingOps"])
async def process_meeting(
    payload: MeetingRequest,
    api_key: str = Depends(get_api_key),
):
    """
    Process meeting notes: extract action items, create Trello cards, notify Slack.

    ⚠️ Meeting content is sent to OpenAI for processing.
    Do not submit privileged or confidential information.
    """
    ck = client_key(api_key)
    allowed, _, _, reset = app.state.rate_limiter.check(ck)
    if not allowed:
        raise HTTPException(429, detail=f"Rate limit. Retry in {reset}s.",
                            headers={"Retry-After": str(reset)})

    start = time.perf_counter()
    try:
        # Write notes to temp file (flow reads from filesystem)
        notes_path = Path(__file__).parent / "meeting_notes.txt"
        notes_path.write_text(payload.meeting_notes, encoding="utf-8")

        from src.meeting_assistant_flow.main import MeetingFlow  # type: ignore[import]

        flow = MeetingFlow()
        flow.kickoff()
        duration = time.perf_counter() - start

        # Clean up runtime notes file immediately after use
        if notes_path.exists():
            notes_path.unlink()

        est_tokens = len(payload.meeting_notes) // 4 + 1000
        cost = guard.check_and_record(ck, "gpt-4o-mini", est_tokens, est_tokens,
                                      tool_name="meeting_assistant")

        return MeetingResponse(
            summary=getattr(flow.state, "summary", "Meeting processed."),
            tasks_created=len(getattr(flow.state, "tasks", [])),
            slack_notified=payload.notify_slack,
            cost_usd=cost,
            duration_s=round(duration, 2),
        )

    except BudgetExceededError as e:
        raise HTTPException(402, detail=f"Daily budget ${e.limit:.2f} exhausted.")
    except Exception as e:
        raise HTTPException(500, detail=f"Flow error: {e}")
    finally:
        # Ensure cleanup even on error
        cleanup = Path(__file__).parent / "meeting_notes.txt"
        if cleanup.exists():
            cleanup.unlink()


@app.get("/usage/me", tags=["Billing"])
async def my_usage(api_key: str = Depends(get_api_key)):
    return guard.get_usage(client_key(api_key))
