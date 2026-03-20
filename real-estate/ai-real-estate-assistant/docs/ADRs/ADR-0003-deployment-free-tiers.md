# ADR-0003: Deployment on Free Tiers

## Context
Goal: MVP launch with zero cost using reliable free services.

## Decision
- Frontend: Vercel (Next.js).
- Backend API: Render/Railway (container).
- Database: Neon (Postgres) or Supabase (Postgres+Auth+Storage).
- DNS/SSL: provider defaults; optional Cloudflare.

## Consequences
- Fast setup; limited resources and cold starts.
- Later migration to paid tiers preserves architecture.
