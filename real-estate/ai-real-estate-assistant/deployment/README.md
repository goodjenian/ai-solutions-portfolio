# Vercel Deployment Guide

> **Status**: Ready for Deployment
> **Date**: 2026-02-07
> **CI Status**: ✅ Frontend PASSED (33/33 tests, 93% coverage), ✅ System PASSED, ✅ Security PASSED
> **Backend**: 1189/1191 tests passed (2 non-blocking meta-test failures)

---

## Quick Start

### Using Deployment Script (Recommended)

```powershell
# Windows
.\scripts\deploy-vercel.ps1

# Linux/Mac
./scripts/deploy-vercel.sh
```

The script will guide you through the entire deployment process.

### Manual Steps

1. **[Environment Setup](./vercel/01-env-setup.md)** - Configure your API keys
2. **[Deployment Steps](./vercel/02-deploy-steps.md)** - Deploy to production
3. **[Validation Checklist](./checklist/validation.md)** - Post-deployment verification

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Vercel Edge Network                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │              Next.js Frontend (apps/web)                 │   │
│   │  - React 19, TypeScript, Tailwind CSS                    │   │
│   │  - Server-Side Rendering (standalone output)              │   │
│   │  - Routes: /, /search, /chat, /settings, etc.             │   │
│   └─────────────────────────────────────────────────────────┘   │
│                          ↓                                          │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │           vercel.json Route Rewriting                     │   │
│   │  - /api/v1/*  → Python Serverless                        │   │
│   │  - /health    → Python Serverless                        │   │
│   │  - /*        → Next.js Frontend                          │   │
│   └─────────────────────────────────────────────────────────┘   │
│                          ↓                                          │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │         FastAPI Backend (apps/api/index.py)              │   │
│   │  - Python 3.11 Serverless Functions                     │   │
│   │  - Routes: /api/v1/verify-auth, /docs, /openapi.json     │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Folder Structure

```
deployment/
├── README.md                    # This file - main guide
├── checklist/
│   └── validation.md             # Post-deployment validation
└── vercel/
    ├── 01-env-setup.md           # Environment variables guide
    ├── 02-deploy-steps.md        # Step-by-step deployment
    └── troubleshooting.md         # Common issues & fixes
```

---

## Pre-Deployment Summary

### ✅ Completed

| Item | Status |
|------|--------|
| CI Verification | ✅ Complete |
| Local Validation | ✅ Frontend CI PASSED (33/33 tests, 93% coverage) |
| System Validation | ✅ PASSED (health, routes, HTTP contract) |
| Security Scans | ✅ PASSED (Gitleaks, Bandit, pip-audit) |
| Environment Guide | ✅ Created |

### ⚠️ Non-Blocking Issues

| Issue | Impact | Action |
|-------|--------|--------|
| 2 meta-test failures | Tests about CI script itself | Accept for deployment |
| mypy type hints | Soft failure (non-blocking) | Matches GitHub CI |
| OpenAPI drift | File doesn't exist yet | Regenerates on deploy |

---

## Required Environment Variables

Copy these to Vercel **before** deploying:

| Variable | Value | Source |
|----------|-------|--------|
| `API_ACCESS_KEY` | See `vercel/01-env-setup.md` | Generate new key |
| `ENVIRONMENT` | `production` | Hardcoded |
| `OPENAI_API_KEY` | From your `.env` | Copy from local |
| `ANTHROPIC_API_KEY` | From your `.env` | Copy from local |
| `CORS_ALLOW_ORIGINS` | Your Vercel URL | Set after deploy |

---

## Deployment Commands

### Option 1: Using Deployment Script (Recommended)

```powershell
# Windows
.\scripts\deploy-vercel.ps1

# Linux/Mac
./scripts/deploy-vercel.sh
```

### Option 2: Manual Commands

```powershell
# 1. Navigate to project
cd c:\Projects\ai-real-estate-assistant

# 2. Login to Vercel (opens browser)
vercel login

# 3. Preview deployment (test first)
vercel

# 4. Production deployment
vercel --prod
```

---

## Support Links

- [Vercel Dashboard](https://vercel.app/dashboard)
- [Environment Setup](./vercel/01-env-setup.md)
- [Deploy Steps](./vercel/02-deploy-steps.md)
- [Validation Checklist](./checklist/validation.md)

---

## Need Help?

1. **Vercel Login Issues**: Ensure you're logged in with `vercel whoami`
2. **Build Failures**: Check Vercel build logs in dashboard
3. **Environment Variables**: Verify all required vars are set
4. **API Errors**: Check `CORS_ALLOW_ORIGINS` includes your domain
