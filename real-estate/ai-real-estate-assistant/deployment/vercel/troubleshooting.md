# Vercel Deployment Troubleshooting Guide

> Common issues and solutions for deploying AI Real Estate Assistant to Vercel

---

## Table of Contents

1. [Login Issues](#1-login-issues)
2. [Build Failures](#2-build-failures)
3. [Environment Variables](#3-environment-variables)
4. [API Errors](#4-api-errors)
5. [CORS Issues](#5-cors-issues)
6. [Serverless Functions](#6-serverless-functions)
7. [Performance](#7-performance)

---

## 1. Login Issues

### Error: "No existing credentials found"
**Solution**:
```powershell
vercel login
```
This opens a browser for authentication. Complete the login, then return.

### Error: "Team not found"
**Solution**:
```powershell
vercel switch
```
Select your team or account from the list.

### Check Login Status
```powershell
vercel whoami
```
Should show your username/email.

---

## 2. Build Failures

### Frontend Build Fails

**Common causes**:
- Missing dependencies in `package.json`
- TypeScript compilation errors
- ESLint failures

**Solutions**:
```powershell
# Test build locally first
cd apps/web
npm install
npm run build
```

**If build fails locally**: Fix errors before deploying
**If build succeeds locally but fails on Vercel**: Check Node version (should be 20)

### Backend Build Fails

**Common causes**:
- Missing dependencies in `requirements.txt`
- Python version mismatch (should be 3.11)
- Import path errors

**Solutions**:
```powershell
# Test Python imports locally
cd apps/api
python -c "from api.main import app; print('OK')"
```

---

## 3. Environment Variables

### Error: "API_ACCESS_KEY not set"

**Solution**:
1. Go to Vercel Dashboard → Your Project → Settings → Environment Variables
2. Add `API_ACCESS_KEY` with generated value
3. Select ☑️ Production, Preview, Development
4. Redeploy

### Error: "Module not found" (LLM providers)

**Solution**:
Add required LLM provider keys:
- `OPENAI_API_KEY` (from local .env)
- `ANTHROPIC_API_KEY` (from local .env)
- `GOOGLE_API_KEY` (from local .env)

### Verify Environment Variables

```bash
# Via CLI
vercel env ls

# Via Dashboard
# Dashboard → Project → Settings → Environment Variables
```

---

## 4. API Errors

### Error: 401 Unauthorized on `/api/v1/verify-auth`

**Cause**: Missing or invalid `API_ACCESS_KEY`

**Solutions**:
1. Verify `API_ACCESS_KEY` is set in Vercel
2. Check request includes `X-API-Key` header:
   ```bash
   curl -H "X-API-Key: your-api-key" https://your-app.vercel.app/api/v1/verify-auth
   ```

### Error: 500 Internal Server Error

**Diagnosis**:
1. Check Vercel Function Logs
2. Look for Python tracebacks
3. Check for missing dependencies

**Common fixes**:
- Missing environment variable
- Import error (check Python path)
- Database/vector store connection issue

---

## 5. CORS Issues

### Error: "CORS policy blocked"

**Cause**: `CORS_ALLOW_ORIGINS` doesn't include your domain

**Solution**:
1. Update `CORS_ALLOW_ORIGINS` in Vercel:
   ```
   https://your-app-name.vercel.app
   ```

2. Redeploy:
   ```powershell
   vercel env add CORS_ALLOW_ORIGINS production
   # Enter: https://your-app-name.vercel.app
   vercel --prod
   ```

### Check CORS Headers

```bash
curl -I https://your-app.vercel.app
```

Look for:
- `Access-Control-Allow-Origin: https://your-app-name.vercel.app`
- `Access-Control-Allow-Methods: GET, POST, OPTIONS`

---

## 6. Serverless Functions

### Error: "Function not found"

**Cause**: Route configuration issue in `vercel.json`

**Check**:
1. Verify `vercel.json` routes configuration
2. Ensure `apps/api/index.py` exists
3. Check function logs for errors

### Error: "Function timeout"

**Cause**: Function execution exceeds Vercel timeout limits
- Hobby: 10 seconds
- Pro: 60 seconds

**Solutions**:
- Optimize slow operations
- Use background jobs for long tasks
- Upgrade to Pro plan for longer timeouts

### Check Function Logs

1. Go to Vercel Dashboard
2. Select your project
3. Go to **Functions** tab
4. Click on function to see logs

---

## 7. Performance

### Slow Cold Starts

**Cause**: Python cold start in serverless

**Solutions**:
- Keep functions small
- Use Vercel's Edge Network caching
- Consider upgrading to Pro for better performance

### High Memory Usage

**Check**: Vercel Dashboard → Functions → Metrics

**Solutions**:
- Optimize imports
- Lazy load heavy dependencies
- Reduce memory footprint

---

## Quick Diagnostics

### Test All Endpoints

```bash
# Health check
curl https://your-app.vercel.app/health

# OpenAPI schema
curl https://your-app.vercel.app/openapi.json

# API docs
curl https://your-app.vercel.app/docs

# Verify auth (without key - should fail)
curl https://your-app.vercel.app/api/v1/verify-auth

# Verify auth (with key - should pass)
curl -H "X-API-Key: your-api-key" https://your-app.vercel.app/api/v1/verify-auth
```

### Check Deployment Status

```powershell
# List recent deployments
vercel ls

# Get deployment info
vercel inspect [deployment-url]
```

---

## Rollback Procedure

If deployment is broken:

```powershell
# Rollback to previous deployment
vercel rollback

# Or rollback to specific deployment
vercel rollback [deployment-url]
```

Then:
1. Fix the issue
2. Test locally
3. Deploy again

---

## Support Resources

- **Vercel Docs**: https://vercel.com/docs
- **Vercel Dashboard**: https://vercel.app/dashboard
- **Project Status**: `trae_ai_real_estate_assistant_8do4`
- **Local CI Report**: `../../artifacts/validation_report.md`

---

## Still Stuck?

1. **Check local CI**: Run `.\scripts\dev\run-ci-full.ps1`
2. **Review logs**: Check `artifacts/logs/` directory
3. **Compare environments**: Local vs Vercel env vars
4. **Re-deploy from clean**: `vercel --force`
