# Vercel Deployment Steps

> Follow these steps to deploy AI Real Estate Assistant to Vercel production.

---

## Prerequisites

- [ ] Vercel account (sign up at https://vercel.com)
- [ ] Vercel CLI installed: `npm i -g vercel`
- [ ] Git repository initialized
- [ ] Generated `API_ACCESS_KEY` (see [01-env-setup.md](./01-env-setup.md))

---

## Step 1: Login to Vercel

```powershell
vercel login
```

This opens a browser window for authentication. Complete the login, then return.

**Verify login:**
```powershell
vercel whoami
```

Should show your username/email.

---

## Step 2: Link Project to Vercel

```powershell
cd c:\Projects\ai-real-estate-assistant
vercel link
```

**During the link process, provide these answers:**
- `? Set up and deploy '~/c:/Projects/ai-real-estate-assistant'?` → **Y**es
- `? Which scope do you want to deploy to?` → Select your account
- `? Link to existing project?` → **N**o (create new)
- `? What's your project's name?` → `ai-real-estate-assistant`
- `? In which directory is your code located?` → **.** (current directory)
- `? Want to override the settings?` → **N**o (use existing vercel.json)

---

## Step 3: Configure Environment Variables

**Before deploying**, add your environment variables:

### Via Vercel Dashboard (Recommended)

1. Go to https://vercel.app/dashboard
2. Select your new project `ai-real-estate-assistant`
3. Go to **Settings** → **Environment Variables**
4. Add each variable:

| Key | Value | Environments |
|-----|-------|-------------|
| `API_ACCESS_KEY` | *(your generated key)* | ☑️ Production, Preview, Development |
| `ENVIRONMENT` | `production` | ☑️ Production, Preview, Development |
| `OPENAI_API_KEY` | *(your key from .env)* | ☑️ Production, Preview, Development |
| `ANTHROPIC_API_KEY` | *(your key from .env)* | ☑️ Production, Preview, Development |
| `CORS_ALLOW_ORIGINS` | `https://ai-real-estate-assistant.vercel.app` | ☑️ Production, Preview, Development |

5. Click **Save** for each variable

### Via Vercel CLI

```powershell
# API Access Key (paste your generated key when prompted)
vercel env add API_ACCESS_KEY
# Select: Production, Preview, Development

# Environment
vercel env add ENVIRONMENT
# Select: Production, Preview, Development
# Paste: production

# OpenAI API Key
vercel env add OPENAI_API_KEY
# Select: Production, Preview, Development
# Paste your key from .env

# Anthropic API Key
vercel env add ANTHROPIC_API_KEY
# Select: Production, Preview, Development
# Paste your key from .env
```

---

## Step 4: Preview Deployment

First, deploy to preview to test everything works:

```powershell
vercel
```

This creates a preview deployment with a URL like:
```
https://ai-real-estate-assistant-abc123.vercel.app
```

**Test the preview deployment:**
1. Visit the preview URL
2. Check if the homepage loads
3. Test the API: `curl https://your-preview-url.vercel.app/health`

---

## Step 5: Production Deployment

Once preview is working, deploy to production:

```powershell
vercel --prod
```

This deploys to your production domain:
```
https://ai-real-estate-assistant.vercel.app
```

---

## Step 6: Update CORS Origins

After production deployment, update `CORS_ALLOW_ORIGINS` with your production URL:

1. Go to Vercel Dashboard → Project → Settings → Environment Variables
2. Find `CORS_ALLOW_ORIGINS`
3. Update value to: `https://ai-real-estate-assistant.vercel.app`
4. Redeploy: `vercel --prod`

---

## Step 7: Post-Deployment Validation

Use the [validation checklist](../checklist/validation.md) to verify everything works:

```powershell
# Health check
curl https://ai-real-estate-assistant.vercel.app/health

# Auth verification (replace YOUR_KEY with your generated key)
curl -H "X-API-Key: your-api-key" https://ai-real-estate-assistant.vercel.app/api/v1/verify-auth
```

Expected responses:
- `/health` → `{"status": "healthy"}`
- `/api/v1/verify-auth` → `{"authenticated": true}`

---

## Troubleshooting

### Build Fails
- Check Vercel build logs in the dashboard
- Ensure `apps/web/package.json` has correct scripts
- Verify Node.js version (should be 20)

### API Returns 401
- Verify `API_ACCESS_KEY` is set in Vercel
- Check request includes `X-API-Key` header with your generated key

### CORS Errors
- Update `CORS_ALLOW_ORIGINS` with your Vercel URL
- Redeploy after updating: `vercel --prod`

### Serverless Functions Fail
- Check Vercel function logs
- Verify Python version (3.11)
- Check `vercel.json` route configuration

For more issues, see [troubleshooting.md](./troubleshooting.md).

---

## Success Criteria

✅ Deployment successful when:
- Homepage loads without errors
- `/health` returns 200
- `/api/v1/verify-auth` works with your API key
- At least one search query returns results
- Chat interface responds
- No critical errors in Vercel function logs
