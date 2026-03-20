"""
FastAPI app factory — creates a production-ready API wrapper for any crewAI tool.

Usage:
    from goodyseo_security.gateway import create_app, get_api_key
    from goodyseo_security.cost_guard import CostGuard, BudgetExceededError
    from goodyseo_security.rate_limiter import build_rate_limiter, client_key

    app, guard = create_app(title="StrategyAI", tool_name="marketing_strategy",
                            daily_budget_usd=5.0, rate_limit_rpm=10)

    @app.post("/run")
    async def run(payload: MyRequest, api_key: str = Depends(get_api_key)):
        ck = client_key(api_key)
        allowed, limit, remaining, reset = app.state.rate_limiter.check(ck)
        if not allowed:
            raise HTTPException(429, detail=f"Rate limit. Retry in {reset}s.")
        # ... run crew, get token counts ...
        guard.check_and_record(ck, "gpt-4o", input_tokens, output_tokens, tool_name)
        return result
"""

import logging
import os
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth import get_api_key  # re-export for convenience
from .cost_guard import CostGuard
from .middleware import apply_all
from .rate_limiter import build_rate_limiter

logger = logging.getLogger("goodyseo.gateway")

__all__ = ["create_app", "get_api_key"]


def create_app(
    title: str,
    tool_name: str,
    version: str = "1.0.0",
    daily_budget_usd: float = 5.0,
    rate_limit_rpm: Optional[int] = None,
    cors_origins: Optional[list[str]] = None,
) -> tuple[FastAPI, CostGuard]:
    """
    Create a hardened FastAPI application for a GoodySEO AI tool.

    Returns:
        (app, cost_guard) — wire up your routes on app, use cost_guard
        inside route handlers to track and enforce OpenAI spend.
    """
    description = f"""
## {title}

**GoodySEO AI Product** — `{tool_name}`

### Authentication
Every request requires `X-API-Key` header.

### Rate Limiting
Responses include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`.

### Cost Budget
Daily budget: **${daily_budget_usd:.2f} USD per client**.
Budget usage available at `GET /usage`.
"""

    app = FastAPI(
        title=title,
        version=version,
        description=description,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── CORS ─────────────────────────────────────────────────────────────────
    allowed_origins = cors_origins or os.getenv(
        "CORS_ORIGINS", "http://localhost:3000"
    ).split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in allowed_origins],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-RateLimit-Limit",
                        "X-RateLimit-Remaining", "X-RateLimit-Reset"],
    )

    # ── Security + observability middleware ───────────────────────────────────
    apply_all(app)

    # ── Rate limiter ──────────────────────────────────────────────────────────
    limiter = build_rate_limiter(max_requests=rate_limit_rpm)
    app.state.rate_limiter = limiter

    # ── Cost guard ────────────────────────────────────────────────────────────
    guard = CostGuard(daily_budget_usd=daily_budget_usd)
    app.state.cost_guard = guard

    # ── Built-in routes ───────────────────────────────────────────────────────

    @app.get("/health", tags=["System"], include_in_schema=False)
    async def health():
        return {"status": "ok", "tool": tool_name, "version": version}

    @app.get("/usage", tags=["Billing"])
    async def usage_all():
        """All clients' daily usage (admin only — protect with API key in production)."""
        return guard.all_usage()

    logger.info("GoodySEO gateway created: %s (budget=$%.2f/day, rpm=%s)",
                title, daily_budget_usd, rate_limit_rpm or "env")

    return app, guard
