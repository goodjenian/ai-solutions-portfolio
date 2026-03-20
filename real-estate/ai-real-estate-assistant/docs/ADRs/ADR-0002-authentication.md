# ADR-0002: Authentication — API Key (MVP) → Accounts (Paid)

## Context
MVP uses a single API key to protect `/api/v1/*`. The web app proxies API calls server-side and injects `X-API-Key` from server env (no browser-exposed API key).

## Decision
- MVP: keep API key header `X-API-Key` for backend access; inject it server-side in the web app; never use `NEXT_PUBLIC_*` for secrets.
- Future paid: user accounts (email/OAuth), server-side sessions, per-user quotas/roles.

## Consequences
- Simple free-tier protection with rate limiting.
- Migration path to proper auth without breaking API surface.
