# Definition of Done (DoD) — MVP V4

## Backend (FastAPI)
- Endpoints implemented: search, chat (SSE), tools, settings, admin, health.
- Rate limiting enabled with response headers; request IDs returned.
- No secrets logged; `.env.example` present; config via env only.
- CORS restricted in production to configured origins.
- Unit/integration tests pass (coverage thresholds met); mypy+ruff clean.
- OpenAPI and API reference drift checks pass.

## Frontend (Next.js)
- Pages: `/chat`, `/search`, `/settings`, `/analytics` render without errors.
- API client uses `NEXT_PUBLIC_API_URL` (defaults to `/api/v1`) via the Next.js proxy; no client‑exposed secrets in prod.
- UI tests (Jest/Testing Library) pass with ≥90% unit coverage for critical UI.
- Accessibility basics checked (labels, roles) and responsive layout verified.
 - Lint and coverage summary steps succeed in CI.

## Documentation
- Updated PRD aligned to V4 MVP and paid roadmap.
- ADRs created for stack, auth, deployment, vector store.
- Deployment guide covers Vercel (web) + Render/Railway (API) + Neon/Supabase.
- Testing guide and architecture documents referenced and consistent.

## Security
- Secrets only via env; dev default key blocked in prod.
- API rate limits configured; CORS pinned; error messages generic.
- Vulnerability review completed; actions documented.

## Operations
- Health checks green; logs structured; basic monitoring notes included.
- Free‑tier deployment verified; cold‑start impact noted.
 - All CI jobs green after push; any post-push failure is fixed and rechecked locally before marking done.
