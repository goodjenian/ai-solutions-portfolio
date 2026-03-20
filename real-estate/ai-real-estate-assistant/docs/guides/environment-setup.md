# Environment Setup Guide

This guide covers configuring environment variables for the AI Real Estate Assistant project.

## Table of Contents

- [Quick Setup](#quick-setup)
- [Environment Variables Reference](#environment-variables-reference)
- [LLM Provider Configuration](#llm-provider-configuration)
- [Security Best Practices](#security-best-practices)
- [Validation](#validation)

---

## Quick Setup

### Step 1: Create Environment File

```bash
# From project root
cp .env.example .env
```

### Step 2: Minimum Required Configuration

Edit `.env` and set these variables:

```bash
# Environment
ENVIRONMENT=development

# Required: API access key (generate a strong key)
API_ACCESS_KEY=$(openssl rand -hex 32)

# Required: At least one LLM provider
OPENAI_API_KEY=sk-...
# OR
ANTHROPIC_API_KEY=sk-ant-...
# OR
GOOGLE_API_KEY=...
```

### Step 3: Restart Services

```bash
# If using Docker
make docker-down
make docker-up

# If running locally
# Restart your development servers
```

---

## Environment Variables Reference

### Required Variables

| Variable | Type | Example | Description |
|----------|------|---------|-------------|
| `ENVIRONMENT` | string | `development` | Environment mode (`development`, `production`) |
| `API_ACCESS_KEY` | string | Random hex | Backend API authentication key |

### LLM Provider Variables (At Least One Required)

| Variable | Provider | Example |
|----------|----------|---------|
| `OPENAI_API_KEY` | OpenAI | `sk-...` |
| `ANTHROPIC_API_KEY` | Anthropic | `sk-ant-...` |
| `GOOGLE_API_KEY` | Google AI | `AI...` |
| `XAI_API_KEY` | xAI (Grok) | `xai-...` |
| `DEEPSEEK_API_KEY` | DeepSeek | `sk-...` |
| `OLLAMA_API_BASE` | Ollama (local) | `http://localhost:11434` |

### Optional Configuration

#### LLM Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `DEFAULT_PROVIDER` | `openai` | Default LLM provider to use |
| `LLM_REQUEST_TIMEOUT_SECONDS` | `120` | LLM request timeout |
| `LLM_CONNECT_TIMEOUT_SECONDS` | `30` | LLM connection timeout |

#### CORS Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `CORS_ALLOW_ORIGINS` | `*` (dev only) | Comma-separated allowed origins |

**Important:** In production (`ENVIRONMENT=production`), you must set `CORS_ALLOW_ORIGINS` to specific domains.

#### Rate Limiting

| Variable | Default | Description |
|----------|---------|-------------|
| `API_RATE_LIMIT_ENABLED` | `true` | Enable rate limiting |
| `API_RATE_LIMIT_RPM` | `600` | Requests per minute limit |

#### JWT Authentication (Optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTH_JWT_ENABLED` | `false` | Enable JWT-based auth |
| `JWT_SECRET_KEY` | (required) | JWT signing secret |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Access token lifetime |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime |

#### OAuth Providers (Optional)

**Google OAuth:**

| Variable | Description |
|----------|-------------|
| `AUTH_OAUTH_GOOGLE_ENABLED` | Enable Google OAuth (`true`/`false`) |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `GOOGLE_REDIRECT_URI` | OAuth redirect URI |

**Apple Sign-In:**

| Variable | Description |
|----------|-------------|
| `AUTH_OAUTH_APPLE_ENABLED` | Enable Apple Sign-In |
| `APPLE_CLIENT_ID` | Apple client ID |
| `APPLE_TEAM_ID` | Apple team ID |
| `APPLE_KEY_ID` | Apple key ID |
| `APPLE_PRIVATE_KEY_PATH` | Path to private key file |

#### Features (Optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_ROUTES_API_KEY` | - | Google Routes API for commute analysis |
| `GOOGLE_ROUTES_ENABLED` | `false` | Enable commute time features |
| `REDIS_URL` | - | Redis connection URL |
| `SMTP_USERNAME` | - | Email notification username |
| `SMTP_PASSWORD` | - | Email notification password |
| `SMTP_PROVIDER` | `gmail` | Email provider |

#### Vector Store (Optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `CHROMA_PERSIST_DIR` | `./vector_store/chroma` | ChromaDB persistence directory |

---

## LLM Provider Configuration

### OpenAI

```bash
# Get API key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-proj-...

# Available models (configured in app)
# - gpt-4o
# - gpt-4o-mini
# - gpt-3.5-turbo
```

### Anthropic (Claude)

```bash
# Get API key from: https://console.anthropic.com/
ANTHROPIC_API_KEY=sk-ant-...

# Available models
# - claude-sonnet-4-20250514
# - claude-haiku-4-20250514
```

### Google AI

```bash
# Get API key from: https://makersuite.google.com/app/apikey
GOOGLE_API_KEY=AI...

# Available models
# - gemini-2.0-flash-exp
# - gemini-exp-1206
```

### xAI (Grok)

```bash
# Get API key from: https://x.ai/
XAI_API_KEY=xai-...

# Available models
# - grok-beta
```

### DeepSeek

```bash
# Get API key from: https://platform.deepseek.com/
DEEPSEEK_API_KEY=sk-...

# Available models
# - deepseek-chat
```

### Ollama (Local)

```bash
# Install Ollama: https://ollama.com/download
# Pull a model: ollama pull llama3.2:3b

# Configure
OLLAMA_API_BASE=http://localhost:11434
OLLAMA_DEFAULT_MODEL=llama3.2:3b
```

**Docker with Ollama:**

```bash
# Start Ollama container
docker compose -f deploy/compose/docker-compose.yml --profile local-llm up

# For GPU support
docker compose -f deploy/compose/docker-compose.yml --profile local-llm --profile gpu up
```

---

## Security Best Practices

### Generate Strong Keys

```bash
# Generate API_ACCESS_KEY
openssl rand -hex 32

# Generate JWT_SECRET_KEY
openssl rand -hex 32
```

### Never Commit Secrets

Ensure `.env` is in `.gitignore`:

```bash
# Verify
git check-ignore .env
```

### Use Different Keys per Environment

```bash
# Development .env
API_ACCESS_KEY=dev-key-not-for-production

# Production .env
API_ACCESS_KEY=<strong-production-key>
```

### Rotate Keys Regularly

1. Generate new key
2. Add to `API_ACCESS_KEYS` (supports rotation):
   ```bash
   API_ACCESS_KEYS=new-key,old-key
   ```
3. Update consumers
4. Remove old key after verification

---

## Frontend Environment

### Frontend-Specific Variables

Create `apps/web/.env.local`:

```bash
# API Configuration
NEXT_PUBLIC_API_URL=/api/v1
BACKEND_API_URL=http://localhost:8000/api/v1

# App URL
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

**Important:** `NEXT_PUBLIC_*` variables are exposed to the browser. Never put secrets here.

### Production Frontend (Vercel)

Set these in Vercel Dashboard:

| Variable | Value | Environment |
|----------|-------|-------------|
| `BACKEND_API_URL` | Your production backend URL | Production |
| `API_ACCESS_KEY` | Your production API key | Production |
| `NEXT_PUBLIC_API_URL` | `/api/v1` | All |

---

## Validation

### Verify Backend Configuration

```bash
# Health check
curl http://localhost:8000/health

# Verify auth
curl -H "X-API-Key: $API_KEY" http://localhost:8000/api/v1/verify-auth
```

### Verify LLM Provider

```bash
# In the app, navigate to Settings > Models
# Check that "runtime_available" is true for your provider
```

### Verify CORS

```bash
# Development: Should allow all origins
curl -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -X OPTIONS http://localhost:8000/api/v1/chat

# Check response headers include "Access-Control-Allow-Origin: *"
```

### Debug Mode

Enable verbose logging:

```bash
# In .env
ENVIRONMENT=development
LOG_LEVEL=debug
```

---

## Example Configuration Files

### Development (.env)

```bash
# Environment
ENVIRONMENT=development
NODE_ENV=development

# API Security
API_ACCESS_KEY=dev-secret-key-for-local-only

# LLM Provider
OPENAI_API_KEY=sk-proj-...
DEFAULT_PROVIDER=openai

# CORS (development allows all)
# CORS_ALLOW_ORIGINS not needed in development

# Optional Features
REDIS_URL=redis://localhost:6379
```

### Production (.env.production)

```bash
# Environment
ENVIRONMENT=production
NODE_ENV=production

# API Security (generate strong key)
API_ACCESS_KEY=<32-character-hex-key>

# LLM Provider (at least one required)
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...

# CORS (must specify origins)
CORS_ALLOW_ORIGINS=https://yourapp.com,https://www.yourapp.com

# Rate Limiting
API_RATE_LIMIT_ENABLED=true
API_RATE_LIMIT_RPM=600

# Optional: JWT Auth
AUTH_JWT_ENABLED=true
JWT_SECRET_KEY=<strong-secret>
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15

# Optional: Email
SMTP_USERNAME=alerts@yourapp.com
SMTP_PASSWORD=<app-specific-password>
SMTP_PROVIDER=gmail
```

---

## Troubleshooting

### Issue: "API key not recognized"

**Solution:**
- Ensure `.env` exists in project root
- Check variable name matches exactly (`API_ACCESS_KEY`)
- Restart services after editing `.env`

### Issue: "CORS error in browser"

**Solution:**
- Development: Ensure `ENVIRONMENT=development`
- Production: Set `CORS_ALLOW_ORIGINS` to your frontend URL

### Issue: "LLM provider not available"

**Solution:**
- Verify API key is correct
- Check LLM provider service status
- Verify network connectivity
- Check provider billing/quota

### Issue: "Ollama not detected"

**Solution:**
- Ensure Ollama is running: `ollama list`
- Verify `OLLAMA_API_BASE` is correct
- If using Docker, check container logs: `docker compose logs ollama`

---

## Next Steps

- Set up [Local Development](local-development.md)
- Configure [Testing](testing.md)
- Prepare for [Deployment](deployment.md)
