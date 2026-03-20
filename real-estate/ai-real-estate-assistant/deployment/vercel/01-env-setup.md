# Vercel Environment Variables Setup Guide

## Critical Variables (Required for Deployment)

| Variable | Value | Notes |
|----------|-------|-------|
| `API_ACCESS_KEY` | *Generate one below* | **Required for API authentication** |
| `ENVIRONMENT` | `production` | Deployment mode |

### Generate API_ACCESS_KEY

**Choose one method to generate a secure key:**

```bash
# Option 1: Python (recommended)
python -c "import secrets; print(secrets.token_urlsafe(48))"

# Option 2: OpenSSL (if available)
openssl rand -hex 32

# Option 3: PowerShell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | % {[char]$_})
```

**Save the generated key** - you'll need it for the Vercel configuration below.

---

## LLM Provider Keys (At Least One Required)

| Variable | Status | Action |
|----------|--------|--------|
| `OPENAI_API_KEY` | ✅ Already in .env | Copy from local .env |
| `ANTHROPIC_API_KEY` | ✅ Already in .env | Copy from local .env |
| `GOOGLE_API_KEY` | ✅ Already in .env | Copy from local .env |
| `XAI_API_KEY` | - | Optional |
| `DEEPSEEK_API_KEY` | - | Optional |

---

## CORS Configuration

| Variable | Value | Notes |
|----------|-------|-------|
| `CORS_ALLOW_ORIGINS` | `https://your-app.vercel.app` | **Update after deployment** |

---

## Steps to Add Variables in Vercel

### Option 1: Via Vercel Dashboard (Recommended)

1. Go to https://vercel.app/dashboard
2. Select your project (after linking)
3. Go to **Settings** → **Environment Variables**
4. Add each variable:
   - **Key**: Variable name
   - **Value**: The value (paste your generated API_ACCESS_KEY)
   - **Environments**: Select ☑️ Production, Preview, Development
5. Click **Save**

### Option 2: Via Vercel CLI

```bash
# Add API_ACCESS_KEY (paste your generated key when prompted)
vercel env add API_ACCESS_KEY
# Select: Production, Preview, Development

# Add ENVIRONMENT
vercel env add ENVIRONMENT
# Select: Production, Preview, Development
# Paste: production

# Add your LLM keys (get from .env file)
vercel env add OPENAI_API_KEY
# Select: Production, Preview, Development
# Paste your key

vercel env add ANTHROPIC_API_KEY
# Select: Production, Preview, Development
# Paste your key
```

---

## Important Notes

1. **API_ACCESS_KEY**: Generate a unique key for each deployment. Never share it publicly.

2. **CORS_ALLOW_ORIGINS**: After deployment, update this with your actual Vercel URL:
   ```
   https://your-app-name.vercel.app
   ```

3. **LLM Keys**: Copy from your local `.env` file. Never commit these to git!

4. **PYTHON_VERSION**: Already set to `3.11` in `vercel.json` - no action needed.

---

## Post-Deployment Update

After successful deployment, update `CORS_ALLOW_ORIGINS`:
1. Note your deployment URL (e.g., `ai-real-estate-assistant.vercel.app`)
2. Go to Vercel Dashboard → Environment Variables
3. Update `CORS_ALLOW_ORIGINS` to: `https://ai-real-estate-assistant.vercel.app`
4. Redeploy: `vercel --prod`
