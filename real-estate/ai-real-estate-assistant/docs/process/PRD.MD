# Product Requirements Document (PRD): AI Real Estate Assistant — V4

## Overview
Open Core & Walled Garden strategy. Conversational, data‑driven assistant for real estate search, analysis, and notifications. V4 uses Next.js (frontend) and FastAPI (backend). The public Community Edition (CE) focuses on developer utility and local deployment; advanced Hosted Pro features are operated privately and are not part of this repository.

## Personas
- Consumer: renters/buyers searching by budget, location, rooms, amenities.
- Agent: curates listings, compares properties, sends digests to leads.
- Manager: tracks portfolio KPIs, market trends, and team performance.

## Community Edition (Open Source)
- License: AGPLv3
- Chat assistant: intent detection, quick answers, tool invocations.
- Property search: hybrid retrieval (semantic + keyword), filters, geo radius.
- Tools: mortgage calculator, property comparison, price analysis, location analysis.
- Saved settings: notification preferences per user email (client‑side identifier).
- Exports: CSV/JSON/Markdown for search results and comparisons.
- Basic analytics: mortgage widget, simple dashboards.
- Local RAG: upload PDFs/Docs and query them for property‑related answers.
- Prompt templates: realtor copywriting (listing description, emails).
- Local deployment: Docker Compose, BYOK for LLM (OpenAI key or local Ollama/Llama 3).

## Hosted Pro (Private, Operated by Us)
- Not part of public repository; features implemented in private modules/services.
- Multi‑agent orchestration (lead qualification, legal analysis).
- Data enrichment via configured APIs; deep CRM sync; voice mode with telephony.
- Analytics dashboard for dialog efficiency and conversion.
- Fine‑tuned models and higher‑tier providers (operational only on our infrastructure).

## Non‑Functional Requirements
- Security: no client‑exposed secrets; rate limiting; audit logs; CORS pinned in prod.
- Reliability: graceful degradation for providers/vector store; retries.
- Performance: p95 < 2s retrieval; p95 < 8s complex answers.
- Scalability: stateless API; horizontal scaling; versioned endpoints.
- Observability: structured logs, request IDs, metrics; per‑client rate limits.
- Testability: unit/integration/e2e with deterministic stubs; CI gates.

## User Stories
- As a consumer I describe needs and get matching listings with explanations.
- As an agent I compare shortlisted properties and export a shareable report.
- As a manager I review weekly market indices and receive change alerts.
- As a user I configure notification preferences and schedules by my email.

## Features
- Chat: `/api/v1/chat` SSE; provider routing; session correlation via request IDs.
- Search: filters (price, rooms, amenities, listing type), sort (price, price/m²), geo (radius/bounding box).
- Tools: mortgage, compare, price analysis, location analysis.
- Settings: notification preferences, model settings by user email.
- Admin: ingest/reindex/health endpoints.

## Data & Schemas
- Properties: normalized schema (country/region/district/currency, lat/lon).
- Vector store: embeddings persisted (local dev: Chroma; prod: pgvector optional).
- Preferences: simple key‑value per user email; digests generated from saved searches.

## Tech Stack
- Frontend: Next.js 16 (App Router), TypeScript, Tailwind CSS v4, Testing Library/Jest.
- Backend: FastAPI (Python 3.12), Pydantic models, SSE streaming, rate limiting.
- Vector: ChromaDB (dev) with hybrid search; optional pgvector (Neon) for prod.
- Providers: OpenAI, Anthropic, Google, Grok, DeepSeek, Ollama via provider factory.
- Storage (free): Neon (Postgres) or Supabase free tier; object storage optional.

## API Contracts (V4)
- Search: `POST /api/v1/search`
- Chat: `POST /api/v1/chat` (SSE)
- Tools: `POST /api/v1/tools/*`
- Settings: `GET/POST /api/v1/settings/*`
- Admin: `POST /api/v1/admin/*`
- Auth check: `GET /api/v1/verify-auth` with `X-API-Key`

## Deployment (Free)
- Frontend: Vercel free.
- Backend: Render/Railway free container.
- Database: Neon free Postgres (optional pgvector).
- Alternatives: Supabase free (Postgres+Auth+Storage) to unify.

## Risks & Mitigations
- Secrets exposure: never expose API keys via public client env vars; server-side auth only.
- Resource limits: small vector index; cache and model routing to cheaper providers.
- CORS misconfig: restrict to frontend origin in prod via env.
- Rate abuse: per‑client RPM limiting; budgets per provider.

## Success Metrics
- Engagement: avg session > 3 min; 30% return users.
- Relevance: ≥80% user‑rated match accuracy.
- Conversion: ≥15% chat→viewing inquiry.
- Performance: p95 latency targets met for search and chat.

## Roadmap (Public CE)
- MVP launch on free tiers.
- Improve local RAG, prompt templates, docs for 5‑min setup.
- Community issues (e.g., Telegram connector) and contributions.
- Compliance hardening for CE; clear extension points for private plugins.

## Acceptance Criteria (MVP)
- Frontend pages: chat, search, settings, analytics render; tests pass (≥90% frontend unit).
- Accessibility: WCAG 2.1 AA for interactive controls, focus management, labels, error feedback.
- Performance: Lighthouse ≥90 on desktop for search and chat pages.
- Backend endpoints: search/chat/tools/settings/admin respond with rate limits and request IDs.
- Error handling: client surfaces request correlation via `X-Request-ID`.
- CI/CD: GitHub Actions run lint, typecheck, unit/integration tests on PR; green required.
- No secrets in client; CORS pinned in prod; health checks green.
