# Deployment Guide

This guide covers deploying the AI Real Estate Assistant to production environments.

## Table of Contents

- [Overview](#overview)
- [Pre-Deployment Checklist](#pre-deployment-checklist)
- [Deployment Methods](#deployment-methods)
- [Docker Deployment](#docker-deployment)
- [VPS Deployment](#vps-deployment)
- [Frontend Deployment (Vercel)](#frontend-deployment-vercel)
- [Post-Deployment](#post-deployment)
- [Monitoring](#monitoring)

---

## Overview

The AI Real Estate Assistant consists of:

1. **Backend**: FastAPI application (Python 3.12+)
2. **Frontend**: Next.js application (React 19)
3. **Optional Services**: Redis, Ollama, SearXNG

### Architecture

```
                    ┌─────────────────┐
                    │   Browser       │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Vercel (Front) │  ← HTTPS
                    │  Next.js App    │
                    │  /api/v1/*      │
                    └────────┬────────┘
                             │ Server-side proxy
                    ┌────────▼────────┐
                    │  Backend Host   │  ← HTTPS
                    │  FastAPI        │
                    │  Port 8000      │
                    └─────────────────┘
```

---

## Pre-Deployment Checklist

### 1. Security

- [ ] Generated strong `API_ACCESS_KEY` (`openssl rand -hex 32`)
- [ ] Set `CORS_ALLOW_ORIGINS` to specific domains
- [ ] Configured `ENVIRONMENT=production`
- [ ] No secrets in client-side code
- [ ] Reviewed `.gitignore` for sensitive files

### 2. Code Quality

```bash
# Run full CI locally
make ci

# Security scan
make security
```

### 3. Database

- [ ] Database backup plan in place
- [ ] Migration strategy defined
- [ ] Database connection string configured

### 4. Environment Variables

```bash
# Production .env checklist
ENVIRONMENT=production
API_ACCESS_KEY=<strong-key>
CORS_ALLOW_ORIGINS=https://yourdomain.com
# At least one LLM provider
OPENAI_API_KEY=sk-...
```

### 5. Domain & SSL

- [ ] Domain configured
- [ ] SSL/TLS certificates (Let's Encrypt or cloud provider)
- [ ] DNS records pointing to servers

---

## Deployment Methods

| Method | Backend | Frontend | Difficulty |
|--------|---------|----------|------------|
| Docker Compose (VPS) | Docker | Docker | Medium |
| Render + Vercel | Render | Vercel | Easy |
| Railway + Vercel | Railway | Vercel | Easy |
| Fly.io + Vercel | Fly.io | Vercel | Medium |

---

## Docker Deployment

### Prerequisites

- Server with Docker and Docker Compose installed
- Domain name configured
- SSL certificates (recommend Traefik or Caddy)

### Step 1: Prepare Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh

# Install Docker Compose
sudo apt install docker-compose-plugin -y

# Add user to docker group
sudo usermod -aG docker $USER

# Re-login for group changes to take effect
```

### Step 2: Clone Repository

```bash
# Clone repo
git clone https://github.com/AleksNeStu/ai-real-estate-assistant.git
cd ai-real-estate-assistant

# Create production .env
cp .env.example .env
```

### Step 3: Configure Production

Edit `.env`:

```bash
# Environment
ENVIRONMENT=production

# Security (generate strong keys)
API_ACCESS_KEY=$(openssl rand -hex 32)

# CORS (your actual domain)
CORS_ALLOW_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# LLM Provider
OPENAI_API_KEY=sk-...
# or other provider

# Optional: Redis for caching
REDIS_URL=redis://redis:6379
```

### Step 4: Start Services

```bash
# Start all services
docker compose -f deploy/compose/docker-compose.yml up -d

# View logs
docker compose -f deploy/compose/docker-compose.yml logs -f

# Check status
docker compose ps
```

### Step 5: Configure Reverse Proxy (Recommended)

Using Caddy (automatic HTTPS):

```bash
# Create Caddyfile
cat > Caddyfile << 'EOF'
yourdomain.com {
    reverse_proxy frontend:3000
}

api.yourdomain.com {
    reverse_proxy backend:8000
}
EOF

# Start Caddy
docker run -d --name caddy \
  -p 80:80 -p 443:443 \
  -v $(pwd)/Caddyfile:/etc/caddy/Caddyfile \
  -v caddy_data:/data \
  caddy:latest
```

---

## VPS Deployment

### Server Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| RAM | 2GB | 4GB |
| CPU | 2 cores | 4 cores |
| Storage | 20GB | 40GB SSD |

### Step 1: Systemd Service (Backend)

Create `/etc/systemd/system/ai-backend.service`:

```ini
[Unit]
Description=AI Real Estate Assistant Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/ai-real-estate-assistant
Environment="PATH=/var/www/ai-real-estate-assistant/.venv/bin"
EnvironmentFile=/var/www/ai-real-estate-assistant/.env
ExecStart=/var/www/ai-real-estate-assistant/.venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-backend
sudo systemctl start ai-backend
sudo systemctl status ai-backend
```

### Step 2: Systemd Service (Frontend)

Create `/etc/systemd/system/ai-frontend.service`:

```ini
[Unit]
Description=AI Real Estate Assistant Frontend
After=network.target ai-backend.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/ai-real-estate-assistant/apps/web
Environment="NODE_ENV=production"
EnvironmentFile=/var/www/ai-real-estate-assistant/.env
ExecStart=/usr/bin/npm run start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Step 3: Nginx Configuration

Create `/etc/nginx/sites-available/ai-assistant`:

```nginx
# Frontend
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # API proxy
    location /api/v1 {
        proxy_pass http://localhost:8000/api/v1;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable and restart Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/ai-assistant /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 4: SSL with Certbot

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get certificate
sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com

# Auto-renewal (configured automatically)
sudo certbot renew --dry-run
```

---

## Frontend Deployment (Vercel)

### Step 1: Connect Repository

1. Go to [vercel.com](https://vercel.com)
2. Click "Add New Project"
3. Import your GitHub repository

### Step 2: Configure Project

| Setting | Value |
|---------|-------|
| Root Directory | `apps/web` |
| Framework Preset | Next.js |
| Build Command | `npm run build` |
| Output Directory | `.next` |
| Install Command | `npm ci` |

### Step 3: Environment Variables

Add in Vercel Dashboard:

| Name | Value | Environment |
|------|-------|-------------|
| `BACKEND_API_URL` | Your production backend URL | Production |
| `API_ACCESS_KEY` | Your production API key | Production |
| `NEXT_PUBLIC_API_URL` | `/api/v1` | All |

**Important:** Never use `NEXT_PUBLIC_*` for secrets.

### Step 4: Deploy

Click "Deploy" - Vercel will build and deploy automatically.

### Step 5: Custom Domain (Optional)

1. In Vercel Dashboard → Settings → Domains
2. Add your custom domain
3. Configure DNS records as instructed

---

## Backend Deployment Options

### Option 1: Render

1. Go to [render.com](https://render.com)
2. Click "New" → "Web Service"
3. Connect GitHub repository
4. Configure:

| Setting | Value |
|---------|-------|
| Root Directory | `/` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn api.main:app --host 0.0.0.0 --port $PORT` |
| Python Version | `3.12` |

5. Add environment variables
6. Deploy

### Option 2: Railway

1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select repository
4. Configure environment variables
5. Deploy

### Option 3: Fly.io

```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Launch
fly launch

# Configure fly.toml
cat > fly.toml << 'EOF'
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
EOF

# Set secrets
fly secrets set API_ACCESS_KEY="your-key"
fly secrets set OPENAI_API_KEY="sk-..."
fly secrets set CORS_ALLOW_ORIGINS="https://yourapp.com"

# Deploy
fly deploy
```

---

## Post-Deployment

### Health Checks

```bash
# Backend health
curl https://your-backend.com/health

# Expected response
# {"status":"healthy","version":"4.0.0","timestamp":"...","uptime_seconds":...}
```

### Smoke Tests

```bash
# Test API authentication
curl -X POST https://your-frontend.com/api/v1/verify-auth \
  -H "X-API-Key: $API_KEY"

# Expected response
# {"message":"Authenticated successfully","valid":true}
```

### Performance Checks

```bash
# Response time
curl -w "@curl-format.txt" -o /dev/null -s https://your-backend.com/health

# curl-format.txt
# time_namelookup: %{time_namelookup}\n
# time_connect: %{time_connect}\n
# time_appconnect: %{time_appconnect}\n
# time_pretransfer: %{time_pretransfer}\n
# time_starttransfer: %{time_starttransfer}\n
# time_total: %{time_total}\n
```

---

## Monitoring

### Health Endpoint Monitoring

Set up monitoring to ping `/health` endpoint every minute.

Recommended services:
- UptimeRobot (free)
- Pingdom
- Better Uptime

### Log Management

For Docker:

```bash
# View logs
docker compose logs -f

# Follow specific service
docker compose logs -f backend

# Export logs
docker compose logs > deployment-logs.txt
```

For Systemd:

```bash
# View logs
sudo journalctl -u ai-backend -f

# View last 100 lines
sudo journalctl -u ai-backend -n 100
```

### Metrics

The backend exposes Prometheus metrics at `/metrics` when `METRICS_ENABLED=true`.

---

## Rollback Procedure

### Docker Rollback

```bash
# Stop current deployment
docker compose down

# Pull previous version
git checkout <previous-tag>

# Rebuild and start
docker compose up -d --build
```

### Vercel Rollback

1. Go to Vercel Dashboard → Deployments
2. Find previous successful deployment
3. Click "Promote to Production"

### Render Rollback

```bash
# In Render Dashboard
# Deployments → Select previous deployment → Promote
```

---

## Troubleshooting

### Issue: CORS Errors

**Solution:**
1. Verify `CORS_ALLOW_ORIGINS` includes your frontend URL
2. Check `ENVIRONMENT=production` is set
3. Backend validates CORS in production mode only

### Issue: 502 Bad Gateway

**Possible causes:**
1. Backend not running
2. Wrong port in proxy config
3. Backend crashing

**Solution:**
```bash
# Check backend status
docker compose ps
# or
sudo systemctl status ai-backend

# Check logs
docker compose logs backend
# or
sudo journalctl -u ai-backend -n 50
```

### Issue: High Memory Usage

**Solution:**
1. Add swap space
2. Configure Redis max memory
3. Set `DB_POOL_SIZE` and `DB_MAX_OVERFLOW`

### Issue: Slow Response Times

**Solution:**
1. Enable Redis caching
2. Check LLM provider latency
3. Consider using faster model (e.g., gpt-4o-mini)

---

## Next Steps

- Configure [CI/CD Pipeline](ci-cd.md)
- Review [Monitoring](#monitoring)
- Read [Troubleshooting Guide](troubleshooting.md)
