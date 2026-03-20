# Deployment Guide

This guide covers deploying the AI Real Estate Assistant (V4) using Docker or on a VPS/OVH server.

## Overview
- **Frontend**: Next.js 14+ (Port 3000)
- **Backend**: FastAPI (Port 8000)
- **Vector Store**: ChromaDB (local dev) or pgvector (optional)
- **Database**: PostgreSQL (Neon/Supabase) for server‑side preferences and future features

---

## 🚀 Option 1: Docker Deployment (Recommended)

The easiest way to run the full stack (Backend + Frontend + Services).

### Prerequisites
- Docker & Docker Compose installed.
- Valid `.env` file (copy from `.env.example`).
- BYOK for LLM: either `OPENAI_API_KEY` (user‑provided) or local Ollama/Llama 3.

### Steps
1. **Prepare Environment**
   ```powershell
   Copy-Item .env.example .env
   # Edit .env and set OPENAI_API_KEY (or configure OLLAMA base URL), DB settings
   ```

2. **Run with Docker Compose**
   ```powershell
   docker compose up -d --build
   ```

3. **Access Services**
   - Frontend: `http://localhost:3000`
   - Backend API: `http://localhost:8000/docs`
   - Redis (optional): `redis://localhost:6379` (`docker compose up -d redis`)
   - Postgres (optional): provision Neon/Supabase and set env variables

4. **Logs & Maintenance**
   ```powershell
   # View logs
   docker compose logs -f

   # Stop services
   docker compose down
   ```

---

## ⚡ Option 3: Vercel Deployment (Best for Frontend)

**Note:** Do not use "Deploy" from IDE directly to avoid `api-upload-free` limits (too many files). Use Git Integration.

### Steps
1. **Push Code to GitHub**
   ```powershell
   git add .
   git commit -m "chore: ready for deploy"
   git push origin dev
   ```

2. **Connect Vercel to GitHub**
   - Go to [Vercel Dashboard](https://vercel.com/dashboard) → **Add New...** → **Project**.
   - Select **Import Git Repository**.
   - Choose `ai-real-estate-assistant`.

3. **Configure Build**
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend` (Edit → Select `frontend` folder).
   - **Environment Variables**: Add keys from `.env` (e.g., `OPENAI_API_KEY`, `API_ACCESS_KEY`).

4. **Deploy**
   - Click **Deploy**. Vercel will create preview deployments from `dev` and production deployments from `main`.

---

## ☁️ Option 2: VPS / OVH Cloud Deployment

For deploying on a Linux server (Ubuntu/Debian recommended).

### 1. Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker & Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# (Log out and back in)
```

### 2. Application Setup
```bash
# Clone repository
git clone https://github.com/AleksNeStu/ai-real-estate-assistant.git
cd ai-real-estate-assistant

# Configuration
cp .env.example .env
nano .env
```

### 3. Nginx Reverse Proxy (Optional)
To serve on a domain (e.g., `realestate.ai`) with SSL.

1. **Install Nginx**
   ```bash
   sudo apt install nginx certbot python3-certbot-nginx -y
   ```

2. **Configure Nginx**
   Create `/etc/nginx/sites-available/ai-real-estate` with:
   ```nginx
   server {
       server_name your-domain.com;

       # Frontend
       location / {
           proxy_pass http://localhost:3000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
       }

       # Backend API
       location /api/ {
           proxy_pass http://localhost:8000;
           proxy_http_version 1.1;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

3. **Enable & Secure**
   ```bash
   sudo ln -s /etc/nginx/sites-available/ai-real-estate /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx

   # Setup SSL
   sudo certbot --nginx -d your-domain.com
   ```

---

## ☁️ Option 3: Serverless (Vercel + Railway/Render)

### Frontend (Vercel)
1. Import `frontend/` directory to Vercel.
2. Set Environment Variables:
   - `NEXT_PUBLIC_API_URL`: `/api/v1` (default; keep API calls going through the Next.js proxy)
   - `BACKEND_API_URL`: backend base URL including `/api/v1` (e.g., `https://your-backend.onrender.com/api/v1`)
   - `API_ACCESS_KEY` or `API_ACCESS_KEYS`: used server-side by the proxy to inject `X-API-Key` (never `NEXT_PUBLIC_*`)

### Backend (Railway/Render)
1. Connect repository.
2. Root directory: `.` (Project Root).
3. Build Command: `pip install -r requirements.txt`.
4. Start Command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`.
5. Set Environment Variables from `.env`.
   - Production note: set `ENVIRONMENT=production` and pin `CORS_ALLOW_ORIGINS` to your frontend URL.
   - Render blueprint (optional): `render.yaml` provides a ready-to-import service definition.

### BYOK Notes
- Never expose secrets in frontend. All keys are server‑side env variables.
- For local models, configure Ollama (`OLLAMA_BASE_URL`) and select model (e.g., `llama3`).
- Feature flags choose providers; Community Edition publishes only safe toggles.

---

## 📋 Production Deployment Checklist

Use this checklist to verify your deployment is production-ready and secure.

### Pre-Deployment Checklist

#### Environment Configuration
- [ ] `.env` file created from `.env.example`
- [ ] `ENVIRONMENT=production` set
- [ ] At least one LLM provider API key configured (OpenAI, Anthropic, or Google)
- [ ] `API_ACCESS_KEYS` set with strong, unique key(s)
- [ ] `dev-secret-key` NOT in `API_ACCESS_KEYS` for production
- [ ] `CORS_ALLOW_ORIGINS` set to your production domain only
- [ ] `NEXT_PUBLIC_API_URL` set correctly for frontend

#### Security Configuration
- [ ] HTTPS enabled with valid SSL certificate
- [ ] HSTS preloaded domain (if using custom domain)
- [ ] `API_RATE_LIMIT_ENABLED=true`
- [ ] `API_RATE_LIMIT_RPM` set appropriately (default: 600)
- [ ] `REQUEST_MAX_BODY_SIZE_MB` configured (default: 10)
- [ ] `REQUEST_MAX_UPLOAD_SIZE_MB` configured (default: 25)
- [ ] `SHUTDOWN_DRAIN_SECONDS` configured (default: 30)

#### Services & Dependencies
- [ ] Vector store (ChromaDB) initialized with data
- [ ] Redis configured if using distributed rate limiting (`REDIS_URL`)
- [ ] Database (PostgreSQL) configured for production if using pgvector
- [ ] Log aggregation configured (e.g., CloudWatch, Datadog, etc.)
- [ ] Monitoring/alerting configured (e.g., Uptime Monitor enabled)

### Post-Deployment Verification

#### Health & Connectivity
- [ ] `GET /health` returns 200 with `status: "healthy"`
- [ ] `GET /health?include_dependencies=true` shows all dependencies healthy
- [ ] `GET /api/v1/verify-auth` with valid API key returns 200
- [ ] Invalid API key returns 401/403
- [ ] `dev-secret-key` returns 403 in production

#### Security Headers Verification
- [ ] Check security headers: `curl -I https://your-domain.com/health`
- [ ] Verify `X-Content-Type-Options: nosniff` present
- [ ] Verify `X-Frame-Options: DENY` present
- [ ] Verify `X-XSS-Protection: 1; mode=block` present
- [ ] Verify `Strict-Transport-Security` present (HTTPS only)
- [ ] Verify `Content-Security-Policy` present

#### CSP Verification (Frontend)
1. Open browser DevTools Console
2. Navigate to your production site
3. Check for CSP violations
4. Verify no inline scripts are blocked (unless expected)

#### Rate Limiting Verification
1. Send 600 requests (within your RPM limit) - should all succeed
2. Send 1 more request - should return 429
3. Verify response headers:
   - `X-RateLimit-Limit`
   - `X-RateLimit-Remaining`
   - `X-RateLimit-Reset`
   - `Retry-After` (on 429)

#### Request ID Correlation
1. Make any API request with valid API key
2. Verify `X-Request-ID` header is present in response
3. Check logs - request ID should be logged

#### Input Sanitization
1. Test search with control characters: `search?query=test%00%01`
2. Test chat with HTML tags: `<script>alert('xss')</script>`
3. Both should return 400 with appropriate error

#### Graceful Shutdown
1. Send SIGTERM to backend process
2. Verify logs show "Graceful shutdown initiated"
3. Verify logs show "Waiting Xs drain period"
4. Verify in-flight requests complete during drain
5. Verify all services stop cleanly

#### Error Handling
1. Make request with oversized payload (>10MB)
2. Verify returns 413 (Payload Too Large)
3. Check error includes request_id

#### Functionality Tests
- [ ] Search works: `POST /api/v1/search`
- [ ] Chat works (non-streaming): `POST /api/v1/search`
- [ ] Chat works (streaming): `POST /api/v1/search` with `stream=true`
- [ ] Settings endpoints work
- [ ] Tools endpoints work (mortgage calculator, comparison, etc.)

### Monitoring & Alerting Setup

#### Metrics to Monitor
- [ ] Request rate (RPM)
- [ ] Error rate (4xx, 5xx)
- [ ] Response time (p50, p95, p99)
- [ ] Rate limit 429 rate
- [ ] LLM provider error rate
- [ ] Circuit breaker state (if using)
- [ ] Vector store latency
- [ ] Redis connection status (if using)

#### Alerts to Configure
- [ ] Error rate > 1%
- [ ] Response time p95 > 2s
- [ ] Rate limit 429 rate > 5%
- [ ] Health check returns 503
- [ ] LLM provider circuit breaker opens
- [ ] Vector store unavailable

### Backup & Recovery

#### Backups
- [ ] Vector store data backup automated
- [ ] Database backup automated (if using PostgreSQL)
- [ ] Backup retention policy configured (30+ days)
- [ ] Backup restoration tested

#### Disaster Recovery
- [ ] Redundancy configured (multi-region if available)
- [ ] Failover procedure documented
- [ ] Recovery time objective (RTO) defined
- [ ] Recovery point objective (RPO) defined

### Documentation Updates

- [ ] Architecture diagrams updated
- [ ] Runbooks documented
- [ ] On-call rotation established
- [ ] Escalation paths defined
- [ ] Security contacts documented

---

## 🔄 Rollback Procedure

If a deployment causes issues:

### Quick Rollback (Docker)
```bash
# Previous version tag
git checkout <previous-tag>
docker compose down
docker compose up -d --build
```

### Quick Rollback (Vercel)
1. Go to Vercel Dashboard
2. Select your project
3. Go to Deployments
4. Find previous successful deployment
5. Click "Promote to Production"

### Database Rollback (if needed)
```bash
# Restore from backup (procedure varies by provider)
# For PostgreSQL:
pg_restore -d database_name backup.dump
```

---

## 📞 Support & Troubleshooting

### Common Issues

**Issue:** Health check returns 503
- **Cause:** Vector store or other dependency unavailable
- **Fix:** Check `GET /health?include_dependencies=true` for details

**Issue:** Rate limiting too aggressive
- **Fix:** Increase `API_RATE_LIMIT_RPM` or add `X-Forwarded-For` header configuration

**Issue:** CORS errors in browser
- **Fix:** Verify `CORS_ALLOW_ORIGINS` includes your frontend domain

**Issue:** CSP violations in console
- **Fix:** Update `next.config.ts` CSP directives or review loaded resources

**Issue:** API key rejected
- **Fix:** Verify key is in `API_ACCESS_KEYS` (comma-separated) and not `dev-secret-key`

### Getting Help

- **Documentation:** [docs/](./)
- **Issues:** [GitHub Issues](https://github.com/AleksNeStu/ai-real-estate-assistant/issues)
- **Security Issues:** See [SECURITY.md](./SECURITY.md) for responsible disclosure

---

**Last Updated:** 2026-01-26
**Version:** 4.0
