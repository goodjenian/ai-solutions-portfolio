# Deployment Guide

This guide covers deploying the AI Real Estate Assistant to production.

## Prerequisites

Before deploying, ensure you have:

- A GitHub repository with the code
- Generated `API_ACCESS_KEY` (run: `openssl rand -hex 32`)
- Backend hosting account (Render, Railway, Fly.io, etc.)
- Vercel account for frontend deployment

---

## Architecture Overview

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   Browser       │──────│  Vercel (Front) │──────│  Backend Host   │
│                 │      │  Next.js App    │      │  (FastAPI)      │
└─────────────────┘      │  /api/v1/*      │      │                 │
                         │  → Proxy to     │      │  Port 8000      │
                         │  Backend        │      └─────────────────┘
                         └─────────────────┘
```

**Key Design:**
- Frontend uses Next.js API proxy (`/api/v1/*`) to call backend
- `API_ACCESS_KEY` is injected server-side, never exposed to browser
- `NEXT_PUBLIC_API_URL` stays as `/api/v1` in all environments

---

## Environment Variables Reference

### Required (All Environments)

| Variable | Description | Where to Set |
|----------|-------------|--------------|
| `API_ACCESS_KEY` | Backend authentication key | Backend host + Vercel |
| `BACKEND_API_URL` | Backend endpoint URL | Vercel only (server-side) |

### Required (Production)

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `ENVIRONMENT` | Environment mode | `production` |
| `CORS_ALLOW_ORIGINS` | Allowed frontend origins | `https://yourapp.com` |

### Optional (LLM Providers)

At least one provider is required:

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `GOOGLE_API_KEY` | Google API key |
| `XAI_API_KEY` | Grok (xAI) API key |
| `DEEPSEEK_API_KEY` | DeepSeek API key |

### Optional (Features)

| Variable | Description | Default |
|----------|-------------|---------|
| `SMTP_USERNAME` | Email username | - |
| `SMTP_PASSWORD` | Email password | - |
| `SMTP_PROVIDER` | Email provider | `gmail` |
| `REDIS_URL` | Redis connection URL | - |

---

## Frontend Deployment (Vercel)

### Step 1: Connect Repository to Vercel

1. Go to [vercel.com](https://vercel.com)
2. Click "Add New Project"
3. Import your GitHub repository
4. Configure the project:

| Setting | Value |
|---------|-------|
| **Root Directory** | `frontend` |
| **Framework Preset** | Next.js (auto-detected) |
| **Build Command** | `npm run build` (default) |
| **Output Directory** | `.next` (auto-detected) |
| **Install Command** | `npm ci` (default) |

### Step 2: Configure Environment Variables

In Vercel Dashboard → Project → Settings → Environment Variables:

**For both Preview & Production:**

| Name | Value | Environment |
|------|-------|-------------|
| `BACKEND_API_URL` | Your deployed backend URL | Preview + Production |
| `API_ACCESS_KEY` | Your generated API key | Preview + Production |

**Important:** Do NOT set `NEXT_PUBLIC_API_URL` - the default `/api/v1` is correct.

### Step 3: Deploy

Click "Deploy" - Vercel will build and deploy your frontend.

---

## Backend Deployment Options

### Option 1: Render (Recommended)

#### Create Web Service

1. Go to [render.com](https://render.com)
2. Click "New" → "Web Service"
3. Connect your GitHub repository
4. Configure:

| Setting | Value |
|---------|-------|
| **Root Directory** | `/` (project root) |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python -m uvicorn api.main:app --host 0.0.0.0 --port $PORT` |
| **Python Version** | `3.12` |

#### Environment Variables

Add these in Render Dashboard:

```
ENVIRONMENT=production
API_ACCESS_KEY=your-generated-key-here
CORS_ALLOW_ORIGINS=https://your-frontend.vercel.app
OPENAI_API_KEY=sk-... (or other provider)
```

### Option 2: Railway

1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Configure:
   - Root Directory: `/`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python -m uvicorn api.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables

### Option 3: Fly.io

1. Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. Run: `fly launch`
3. Configure your `fly.toml`:

```toml
[build]
  builder = "paketobuildpacks/builder:base"

[env]
  PORT = "8000"
  ENVIRONMENT = "production"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0
  processes = ["app"]
```

4. Set secrets:

```bash
fly secrets set API_ACCESS_KEY="your-key"
fly secrets set OPENAI_API_KEY="sk-..."
fly secrets set CORS_ALLOW_ORIGINS="https://your-frontend.vercel.app"
```

5. Deploy: `fly deploy`

---

## Post-Deployment Verification

### Backend Health Check

```bash
curl https://your-backend.com/health
```

Expected response:

```json
{
  "status": "healthy",
  "version": "3.0.0",
  "timestamp": "2026-02-05T12:00:00Z",
  "uptime_seconds": 123.45
}
```

### Frontend Verification

1. Open your deployed frontend URL
2. Open browser DevTools → Network tab
3. Send a chat message
4. Verify:
   - Request goes to `/api/v1/chat` (same-origin)
   - No API keys visible in client-side JavaScript
   - Response is successful

### API Proxy Test

```bash
curl -X POST https://your-frontend.vercel.app/api/v1/verify-auth \
  -H "X-API-Key: $API_KEY"
```

Expected response:

```json
{
  "message": "Authenticated successfully",
  "valid": true
}
```

---

## Troubleshooting

### Issue: CORS Errors

**Symptom:** Browser shows CORS policy errors

**Solution:**
1. Check backend `CORS_ALLOW_ORIGINS` includes your frontend URL
2. Verify `ENVIRONMENT=production` is set on backend
3. Backend validates CORS in production mode only

### Issue: API Returns 401 Unauthorized

**Symptom:** `/api/v1/verify-auth` returns 401

**Solution:**
1. Verify `API_ACCESS_KEY` matches between backend and Vercel
2. Check Vercel environment variables are set for correct environment (Preview/Production)
3. Regenerate key and update both places

### Issue: Frontend Build Fails

**Symptom:** Vercel build fails

**Solution:**
1. Check build logs for specific error
2. Verify `frontend/package.json` has correct scripts
3. Ensure Node version is compatible (uses 20 in CI)

### Issue: Backend Build Fails

**Symptom:** Backend deployment fails to start

**Solution:**
1. Check that Python 3.12 is available
2. Verify `requirements.txt` installs correctly
3. Check port binding (must use `$PORT` environment variable)

---

## Security Checklist

- [ ] `API_ACCESS_KEY` is strong (32+ hex characters)
- [ ] `CORS_ALLOW_ORIGINS` specifies exact domains (no wildcard)
- [ ] No API keys in client-side code
- [ ] `NEXT_PUBLIC_*` variables contain no secrets
- [ ] Backend uses `https://` in production
- [ ] Firewall/proxy configured if needed

---

## Monitoring and Maintenance

### Health Checks

Backend exposes `/health` endpoint - configure monitoring to ping this endpoint.

### Logs

- **Vercel:** Dashboard → Deployments → View Logs
- **Backend:** Check your hosting platform's logs

### Updates

To update production:

1. Merge changes to `main` (from `dev`)
2. Vercel auto-deploys on push
3. Backend hosting may require manual trigger or auto-deploys on push

---

## Additional Resources

- [Vercel Monorepo Docs](https://vercel.com/docs/monorepos)
- [Next.js Deployment Docs](https://nextjs.org/docs/deployment)
- [Render Python Docs](https://render.com/docs/deploy-python)
- [Railway Python Guide](https://docs.railway.app/guides/python)
