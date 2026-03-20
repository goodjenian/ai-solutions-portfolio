# BACKLOG (Omni-Tree, Spec-Driven) — AI Real Estate Assistant (CE, V4)

Generated on 26.01.2026.

## Phase 1 — Architectural Discovery

### Source Documents

- `docs/PRD.MD`
- `docs/ADRs/ADR-0001-tech-stack.md`
- `docs/ADRs/ADR-0002-authentication.md`
- `docs/ADRs/ADR-0003-deployment-free-tiers.md`
- `docs/ADRs/ADR-0004-vector-store.md`

### Pillars (3–4 Main Architectural Pillars)

1. **API Platform & Security** (FastAPI + Auth + Observability + Proxy contract)
2. **Retrieval, Data, and Local RAG** (Ingest → Index → Search → Cite)
3. **Chat & Tool Orchestration** (SSE streaming + tool execution + provider routing)
4. **Frontend UI System** (Next.js pages + state-first UX + typed API client)

### Capability Mapping (MVP-aligned)

- **Auth**: backend protected via `X-API-Key` (MVP), web proxy injects server-side key; optional email OTP UI flow exists but does not replace API-key protection.
- **Search**: hybrid retrieval, filters, geo radius/bbox, sorting, reranking.
- **Chat**: SSE streaming, tool invocations, sources/citations and request correlation.
- **Tools**: mortgage calculator + comparison + basic price/location analysis; Pro-only tools remain safe stubs.
- **Local RAG**: upload documents, ask questions with citations, reset knowledge base.
- **Settings**: notification preferences; model catalog/runtime status; user model preferences.
- **Notifications**: digests + quiet hours + dedupe + scheduler.
- **Exports**: CSV/JSON/Markdown (and existing additional formats) from reproducible inputs.
- **Observability**: structured logs, request IDs, rate limiting, safe error envelopes.
- **Deployment**: free-tier targets and production guards (CORS pinned, proxy restrictions).

### Spartan Audit (MVP vs bloat)

**Keep (MVP):**

- Chat + Search + Tools + Settings + Notifications + Exports + Local RAG
- BYOK providers (OpenAI key) + local runtime (Ollama) support
- Request ID correlation + rate limiting + no client-side secrets

**Cut / Defer (Not required for MVP outcome):**

- Multi-region expansion, multilingual query normalization, FX/currency pipelines beyond existing schema
- Pro-only connectors (CRM deep sync, voice/telephony, proprietary legal/data enrichment services)
- Heavy performance dashboards/telemetry beyond request IDs + basic metrics endpoints

---

## Phase 2 — 3-Level Omni-Tree Decomposition

### [TASK-001]: API Platform & Security

- **Definition**: Provide a secure, observable, versioned API surface where every response is traceable via `X-Request-ID` and secrets never reach the browser.

- **SUBTASK [TASK-001.1]**: Settings and environment wiring
  - **STEP [TASK-001.1.1]**: Normalize API access keys (rotation) and enforce dev/prod defaults.
  - **STEP [TASK-001.1.2]**: Enforce production CORS allowlist and reject unsafe wildcard origins.
  - **STEP [TASK-001.1.3]**: Bound risky inputs via settings (RAG sizes, sources truncation, timeouts).

- **SUBTASK [TASK-001.2]**: Auth middleware and rate limiting
  - **STEP [TASK-001.2.1]**: Validate `X-API-Key` against rotated keys and return 403 with safe detail.
  - **STEP [TASK-001.2.2]**: Apply per-client RPM rate limiting with deterministic client ID derivation.
  - **STEP [TASK-001.2.3]**: Ensure health and docs endpoints behave correctly under auth + rate limits.

- **SUBTASK [TASK-001.3]**: Request correlation and error envelope
  - **STEP [TASK-001.3.1]**: Generate/normalize `X-Request-ID` for every request and response.
  - **STEP [TASK-001.3.2]**: Standardize error responses as `{ detail: string }` with `X-Request-ID`.
  - **STEP [TASK-001.3.3]**: Prevent logging of secrets; redact sensitive headers and tokens.

- **SUBTASK [TASK-001.4]**: Next.js server proxy contract for `/api/v1/*`
  - **STEP [TASK-001.4.1]**: Proxy requests to backend and inject server-side `X-API-Key`.
  - **STEP [TASK-001.4.2]**: Strip client-supplied `X-API-Key` and cookies; forward only allowlisted headers.
  - **STEP [TASK-001.4.3]**: Propagate `X-Request-ID` and preserve SSE streaming bodies end-to-end.

- **Dependencies**: None

### [TASK-002]: Retrieval, Data, and Local RAG

- **Definition**: Enable ingest/index/search of property and document data with deterministic results, bounded resource usage, and reliable citations.

- **SUBTASK [TASK-002.1]**: Property data ingestion and normalization
  - **STEP [TASK-002.1.1]**: Validate and normalize property schema (geo fields, currency, listing type).
  - **STEP [TASK-002.1.2]**: Deduplicate records deterministically and enforce maximum dataset size.
  - **STEP [TASK-002.1.3]**: Run ingest/reindex via admin endpoints with safe operational feedback.

- **SUBTASK [TASK-002.2]**: Vector store abstraction and indexing
  - **STEP [TASK-002.2.1]**: Index properties into Chroma with hybrid fields and metadata filters.
  - **STEP [TASK-002.2.2]**: Provide managed option wiring (pgvector) without changing API contract.
  - **STEP [TASK-002.2.3]**: Degrade gracefully when vector store is unavailable (predictable errors).

- **SUBTASK [TASK-002.3]**: Search endpoint behavior (hybrid + geo + sort)
  - **STEP [TASK-002.3.1]**: Implement `POST /api/v1/search` request/response models and validation.
  - **STEP [TASK-002.3.2]**: Implement filters + geo (radius/bbox) + stable sort with clear tie-breakers.
  - **STEP [TASK-002.3.3]**: Return explainability fields (match signals) without leaking prompts.

- **SUBTASK [TASK-002.4]**: Local RAG knowledge base
  - **STEP [TASK-002.4.1]**: Upload documents with per-file and total byte bounds.
  - **STEP [TASK-002.4.2]**: Answer questions with citations and bounded `top_k`.
  - **STEP [TASK-002.4.3]**: Reset knowledge base safely and idempotently.

- **Dependencies**: [TASK-001]

### [TASK-003]: Chat & Tool Orchestration

- **Definition**: Provide a streaming chat experience backed by tools and retrieval, with deterministic testing and safe fallbacks across LLM providers.

- **SUBTASK [TASK-003.1]**: SSE chat contract and streaming reliability
  - **STEP [TASK-003.1.1]**: Define typed SSE events and finalize response meta payload (sources, truncation flags).
  - **STEP [TASK-003.1.2]**: Implement server-side streaming with timeouts and safe termination behavior.
  - **STEP [TASK-003.1.3]**: Ensure the client can recover from stream errors with request correlation.

- **SUBTASK [TASK-003.2]**: Tool registry and execution safety
  - **STEP [TASK-003.2.1]**: Validate tool inputs and outputs with strict schemas (Python/Pydantic).
  - **STEP [TASK-003.2.2]**: Stream intermediate tool steps without leaking sensitive data.
  - **STEP [TASK-003.2.3]**: Implement deterministic tool stubs for Pro-only integrations.

- **SUBTASK [TASK-003.3]**: Provider routing and per-user preferences
  - **STEP [TASK-003.3.1]**: Route providers via provider factory with consistent config defaults.
  - **STEP [TASK-003.3.2]**: Implement per-user model preferences and apply during chat/tool execution.
  - **STEP [TASK-003.3.3]**: Surface local runtime availability and runtime errors safely.

- **Dependencies**: [TASK-001], [TASK-002]

### [TASK-004]: Frontend UI System (State-First)

- **Definition**: Deliver a resilient Next.js UI that never blocks on missing data, always communicates loading, and provides recovery paths with request IDs.

- **SUBTASK [TASK-004.1]**: Typed API client + uniform error handling
  - **STEP [TASK-004.1.1]**: Keep TypeScript API contracts centralized and consistent across features.
  - **STEP [TASK-004.1.2]**: Attach `request_id` to thrown errors when `X-Request-ID` exists.
  - **STEP [TASK-004.1.3]**: Add unit tests for error parsing and header behavior.

- **SUBTASK [TASK-004.2]**: Search page UI (4 mandated states)
  - **STEP [TASK-004.2.1]**: Empty state (zero-data): onboarding copy + example queries + disabled export.
  - **STEP [TASK-004.2.2]**: Loading state: skeleton results + disabled controls + map placeholder.
  - **STEP [TASK-004.2.3]**: Error state: retry action + human-readable error + `request_id=...`.
  - **STEP [TASK-004.2.4]**: Populated state: results list + filters + sorting + map clustering.

- **SUBTASK [TASK-004.3]**: Chat page UI (4 mandated states)
  - **STEP [TASK-004.3.1]**: Empty state (zero-data): suggested prompts and explanation of tools/sources.
  - **STEP [TASK-004.3.2]**: Loading state: streaming placeholder + "thinking" indicator.
  - **STEP [TASK-004.3.3]**: Error state: inline assistant apology + retry + `request_id=...`.
  - **STEP [TASK-004.3.4]**: Populated state: message list + sources display + intermediate steps toggle.

- **SUBTASK [TASK-004.4]**: Settings, Knowledge, and Analytics pages (4 mandated states)
  - **STEP [TASK-004.4.1]**: Empty state: clear guidance when settings/models/knowledge are absent.
  - **STEP [TASK-004.4.2]**: Loading state: skeleton sections for model catalog and network calls.
  - **STEP [TASK-004.4.3]**: Error state: retry actions + readable feedback + `request_id=...`.
  - **STEP [TASK-004.4.4]**: Populated state: editable preferences + runtime info + knowledge citations.

- **Dependencies**: [TASK-001], [TASK-002], [TASK-003]

---

## Phase 4 — Execution Handover (Boris Protocol)

### Completed Tasks (MVP V4)

- [TASK-001] API Platform & Security ✅
- [TASK-002] Retrieval, Data, and Local RAG ✅
- [TASK-003] Chat & Tool Orchestration ✅
- [TASK-004] Frontend UI System (State-First) ✅

---

## Phase 5 — Roadmap Tasks (Post-MVP)

### High Priority Tasks

#### [TASK-005] Excel Data Loader Integration

- **Definition**: Extend CSV loader to support .xlsx, .xls, .ods files
- **Dependencies**: TASK-002
- **Subtasks**: Excel Loader Implementation, Frontend File Upload UI, Source Tagging and Persistence

#### [TASK-006] Portal/API Integration Framework

- **Definition**: Create adapter system for external real estate portals
- **Dependencies**: TASK-002
- **Subtasks**: External Source Adapter Interface, UI Portal Configuration, First Real Portal Adapter, Security and Secrets Management

#### [TASK-017] Production Deployment Optimization

- **Definition**: Optimize for production with caching, monitoring, and performance tuning
- **Dependencies**: TASK-001, TASK-002, TASK-003, TASK-004
- **Subtasks**: Caching Strategy, Performance Monitoring, Database Optimization, Auto-scaling Configuration

#### [TASK-018] Security Hardening

- **Definition**: Comprehensive security measures including audit logging and compliance
- **Dependencies**: TASK-001
- **Subtasks**: Audit Logging, Security Scanning, Data Protection, Access Control

### Medium Priority Tasks

#### [TASK-007] Geographic Mapping Enhancement

- **Definition**: Integrate Mapbox for heatmaps, clustering, and interactive filters
- **Dependencies**: TASK-004, TASK-002
- **Subtasks**: Mapbox Integration Setup, Heatmap Visualization, Map Filters and Interactions, City Overview Map

#### [TASK-008] Neighborhood Quality Index

- **Definition**: Composite scores for safety, green space, schools, and services
- **Dependencies**: TASK-002
- **Subtasks**: Data Collection, Index Scoring Algorithm, API Endpoint, UI Display

#### [TASK-009] Commute Time Analysis

- **Definition**: Calculate and visualize commute times with multiple transport modes
- **Dependencies**: TASK-007, TASK-002
- **Subtasks**: Routing Integration, Isochrone Generation, User Inputs, Results Ranking

#### [TASK-010] Total Cost of Ownership Calculator

- **Definition**: Extend mortgage calculator with utilities, parking, taxes, insurance
- **Dependencies**: None
- **Subtasks**: Cost Categories, Input Form, Calculation Logic, Comparison Mode

### Low Priority Tasks (Feature Growth)

#### [TASK-011] Property Description Generator

- **Definition**: Use LLM to generate descriptions, headlines, and social media summaries
- **Dependencies**: TASK-003, TASK-001

#### [TASK-012] Lead Scoring System

- **Definition**: Score leads by likelihood to close, budget fit, and urgency
- **Dependencies**: TASK-004, TASK-001

#### [TASK-014] Agent Performance Analytics

- **Definition**: Track and visualize per-agent metrics
- **Dependencies**: TASK-012

#### [TASK-015] Market Anomaly Detection

- **Definition**: Detect and alert on unusual market conditions
- **Dependencies**: TASK-002

### Low Priority Tasks (Expansion)

#### [TASK-013] International Market Support

- **Definition**: Currency conversion, multilingual UI, regional data sources
- **Dependencies**: TASK-006

#### [TASK-016] E-Signature Integration

- **Definition**: Document generation and e-signature workflow
- **Dependencies**: TASK-001, TASK-004

---

## Phase 6 — Execution Handover (Boris Protocol)

### [TASK-001] Technical Contract

#### Impacted Files (edit/create)

- Backend
  - `api/auth.py`
  - `api/observability.py`
  - `api/main.py`
  - `config/settings.py`
  - `tests/unit/api/test_api_auth.py`
  - `tests/unit/test_settings_api_access_keys.py`
  - `tests/integration/api/test_*` (request-id, auth, rate limit assertions)
- Frontend
  - `frontend/src/app/api/v1/[...path]/route.ts`
  - `frontend/src/app/api/v1/__tests__/proxy.route.test.ts`
  - `frontend/src/lib/api.ts`
  - `frontend/src/lib/types.ts`

#### Inputs / Outputs (TypeScript + HTTP contract)

- **HTTP Inputs**
  - Request headers:
    - `X-User-Email?: string` (user-scoped settings and preferences)
    - `X-API-Key?: string` (server-side only; must be ignored if client-supplied)
  - Proxy env inputs:
    - `BACKEND_API_URL: string`
    - `API_ACCESS_KEY` or `API_ACCESS_KEYS` (rotated)

- **HTTP Outputs**
  - Response headers:
    - `X-Request-ID: string` (always present)
  - Error JSON (minimum contract):
    - `{ "detail": string }`

- **TypeScript Contracts (existing)**
  - `SearchRequest`, `SearchResponse`
  - `ChatRequest`, `ChatResponse`
  - `NotificationSettings`
  - `ModelProviderCatalog`, `ModelPreferences`
  - `RagUploadResponse`, `RagQaResponse`, `RagResetResponse`

#### Verification Plan (must pass)

- Backend:
  - `python -m ruff check .`
  - `python -m mypy`
  - `python -m pytest -q tests/unit`
  - `python -m pytest -q tests/integration`
- Frontend:
  - `cd frontend` then `npm ci`
  - `npm run lint`
  - `npm run test -- --ci --coverage`
