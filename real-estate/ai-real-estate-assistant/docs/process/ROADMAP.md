# Global Roadmap: Poland, EU, CIS (incl. Russia), Turkey, Africa, USA

## Goals
- Unified platform for real‑estate search and analytics across regions
- Consumer mode (simple search, map, comparisons, calculators)
- Expert mode (indices, comparables, yield, risk, export)

## Data Architecture
- Extend `Property` and metadata:
  - `country`, `region`, `city`, `district`, `lat`, `lon`
  - `currency`, `price_original`, `price_converted`, `price_per_sqm`
  - `listing_type` (rent/sale), `transaction_type`, `property_type`
  - optional: `year_built`, `energy_cert`, `floor`, `amenities`
- FX normalization: PLN/EUR/USD/TRY/RUB/ZAR/…
  - Providers: ECB/NBP/Fed/…; daily cache
- Geocoding: batch via OpenStreetMap/Nominatim (rate‑limited), store lat/lon
- Storage: separate Chroma collections per region, naming `properties_<country>`

## Data Integrations
- Sources: CSV files, open datasets (HuggingFace, government stats), manual import
- Aggregation by city/district, validation/cleaning, deduplication
- Scheduler: incremental loads and reindexing on schedule

## Search & Retrieval
- Geospatial filters: bounding box, distance from point
- Facets: `country/city/type/rooms/price_per_sqm`, etc.
- Multilingual query normalization (synonyms, transliteration)
- Reranker: user priorities (family/investor), location/price/area signals

## Analytics & Indices
- City/country price indices (median, average, YoY/YoM)
- Rental yield (gross/net), ROI, payback period
- Comparables: similar properties + fair‑price adjustments
- Risk metrics: volatility, liquidity, vacancy (where available)
- Time series: smoothing, trends, anomalies

## Map & Visualization
- World map: center by selected country/city, data layers
- Heatmaps for price and yield, clustered points
- Map filters: price/m², rooms, type, year, energy

## UX/UI
- Quick presets (family/investor/office)
- Expert mode: index panels, comparables, export to PDF/CSV
- Locale/currency: choose language (EN/PL/RU/TR/AR/FR/DE/ES/IT/PT) and currency
- Accessibility: contrast, keyboard navigation, neutral states

## Notifications & Subscriptions
- Consumer digest: new listings, price drops, top‑5 picks
- Expert digest: indices, trends, top locations by yield
- Channels: Email (existing), extend templates and criteria

## DevOps & Quality
- Data validators: schemas/ranges/coordinate validity
- Tests: unit for analytics, integration for retriever, e2e UI
- Quality gates: ruff/mypy/bandit (enabled in CI)

---

## V4 (Next.js + ElevenLabs + Vercel) Roadmap

### Goal
- Ship a production-grade web application (V4) while keeping V3 as reference implementation.

### Backend: 10 Functional Requirements
- [STARTED] Provide authenticated API for search, chat, and tools
  - [DONE] Foundation: FastAPI setup, Auth middleware, Health check
  - [DONE] Search endpoint with vector store integration
  - [DONE] Chat endpoint with hybrid agent integration
  - [DONE] Tools endpoints (mortgage, compare, price analysis, location analysis)
  - [DONE] Streaming support
- [DONE] Support hybrid retrieval (semantic + keyword) with metadata filters
- [DONE] Support geospatial filters (radius) and sorting (price, price/m²)
- [DONE] Support multi-provider LLM execution with consistent configuration
- [DONE] Support conversation sessions with persisted history and replay
- [DONE] Support streaming responses (SSE/WebSocket) for chat and tool progress
- [DONE] Support tool actions (mortgage, comparison, price analysis, location analysis)
- [DONE] Support exports (CSV/Excel/JSON/Markdown/PDF) with reproducible inputs
- [DONE] Support notifications pipeline (alerts, digests) with user preferences
  - [DONE] Scope `/api/v1/settings/notifications` by user email
- [DONE] Provide admin endpoints for ingestion/reindexing and health checks

### Platform: 10 Non-Functional Requirements
- Security: API keys never exposed to clients; least-privilege secrets management
- Reliability: graceful degradation when providers/vector store are unavailable
- Performance: p95 < 2s for retrieval; p95 < 8s for hybrid answers (typical)
- Scalability: stateless API where possible; horizontal scaling ready
- Observability: structured logs, traces, metrics, request IDs, audit events
- Cost controls: provider rate limits, budgets, caching, model routing policies
- Testability: unit/integration/e2e coverage with deterministic stubs
- Maintainability: clear module boundaries; versioned API contracts
- Compatibility: works on Vercel for web, container for API; local dev parity
- Compliance: data minimization, retention rules, and redaction for sensitive fields

### Epics (split for implementation)
- [STARTED] Frontend (Next.js): UI shell, auth UI, chat, search, expert dashboards
  - [DONE] Initialize Next.js project with TypeScript, Tailwind CSS, and ESLint
  - [DONE] Setup UI Shell (Layout, Navbar, Theming)
  - [DONE] Configure API Proxy to Backend
  - [DONE] Create Auth Pages (Login/Register)
  - [DONE] Create Chat Page (UI + Integration)
  - [DONE] Create Search Page (UI + Integration)
  - [DONE] Implement Search Filters (price range, rooms, property type)
  - [DONE] Implement Sorting Controls (relevance, price, price/m², area, year)
  - [DONE] Setup API Client & Type Definitions
  - [DONE] Create Analytics Page (Mortgage Calculator Integration)
  - [DONE] Create Settings Page (Notification Preferences)
  - [DONE] Show local runtime availability and setup guidance in settings
  - [DONE] Implement Frontend Unit & Integration Tests (Coverage ≥ 90%)
  - [DONE] Implement Export UI (CSV/Excel/JSON/Markdown/PDF)
- [DONE] API (Python): endpoints, streaming, session persistence, tool execution
- Retrieval: vector store service + indexing + geo filters + reranking
  - [DONE] Add bounding box geo filters to V4 `/api/v1/search`
- Analytics: indices, trends, anomaly detection, export endpoints
- [DONE] Notifications: digests, schedules, templates, preference management
- DevOps: CI gates, environments, secrets, deploy pipelines, monitoring

### Community Edition Roadmap (Open Core)
- Publish repository with AGPLv3 and clear contribution guidelines.
- Documentation: “Run your AI realtor in 5 minutes” (local Docker Compose, BYOK).
- Community Issues: create “Telegram connector” issue for community contribution.
- Metrics: ≥100 GitHub stars, first external PRs merged, doc site visits growth.

## Sprints
- Sprint 1 (1–2 weeks)
  - [DONE] Schema extension (country/region/district/currency, lat/lon)
  - [DONE] Geospatial filters (radius) and base city price indices
  - [DONE] Monthly price index with YoY (Expert Panel)
  - [DONE] Moving average smoothing and anomaly detection (z-score)
  - [DONE] Map picker (click to set radius center) wired to retriever
  - [DONE] Chat retrieval price range filters and sorting controls
  - [DONE] Multi-city YoY latest with UI table and leaders
  - [DONE] Deterministic lat/lon fill at ingestion for known cities
  - [DONE] Map with filters, neutral UI states (est: 2–3 days)
  - [DONE] Visual property comparison UI (radar charts, price trends)
  - [DONE] Base digest (consumer/expert) (est: 2–4 days)
- Sprint 2 (2–3 weeks)
  - [DONE] Indices and comparables for CIS/Russia/Turkey/USA/Africa
  - [DONE] Yield/ROI, rate/expense scenarios
  - [DONE] PRO filters (energy/year/elevator/parking), multilingual texts
- Sprint 3 (3–4 weeks)
  - [DONE] Hedonic fair‑price model and strategic reranker
  - [DONE] Historical map layers
  - [DONE] Price heatmap mode (map view)
  - [DONE] City overview map with aggregate statistics
  - [DONE] Points of interest, report export
  - [DONE] Performance/cache/parallel ingestion
- Sprint 4 (2 weeks)
  - [DONE] Notifications/scheduling/advanced templates
  - Full e2e tests, static checks, stabilization

## Success Metrics
- CTR for comparables, saved‑search conversions, digest opens
- Fair‑price accuracy (±%), map engagement, session duration
