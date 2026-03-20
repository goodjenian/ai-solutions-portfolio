# ADR-0001: Web Stack — Next.js + FastAPI

## Context
V4 targets a modern web experience with chat, search, tools, and dashboards. Existing V3 Streamlit app limits UX and routing.

## Decision
- Frontend: Next.js 16 (App Router), TypeScript, Tailwind CSS v4.
- Backend: FastAPI (Python 3.12), SSE streaming, provider factory.
- Testing: Jest/Testing Library (frontend), Pytest + mypy + ruff (backend).

## Consequences
- Better SSR/ISR and routing for web UI.
- Clear API contracts and scalability.
- Separate deploy paths (Vercel web, container API).
