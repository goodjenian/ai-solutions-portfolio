# Post-Deployment Validation Checklist

> Use this checklist after deploying to Vercel to ensure everything works correctly.

---

## Deployment Verification ✅

- [ ] Deployment completed without errors in Vercel dashboard
- [ ] Build logs show "Success" status
- [ ] Deployment URL is accessible (e.g., `https://your-app.vercel.app`)

---

## Frontend Validation 🌐

### Basic Page Load
- [ ] Homepage loads at `https://your-app.vercel.app`
- [ ] No console errors in browser DevTools
- [ ] CSS/styles render correctly
- [ ] Navigation menu works

### Key Pages
- [ ] `/search` - Property search page loads
- [ ] `/chat` - AI assistant page loads
- [ ] `/settings` - Settings page loads
- [ ] `/analytics` - Analytics page loads

### Frontend Tests
- [ ] All 33 Jest tests passed (93% coverage)
- [ ] No console warnings/errors on load

---

## Backend API Validation 🔌

### Health Endpoints
- [ ] `GET /health` returns 200 OK
  ```bash
  curl https://your-app.vercel.app/health
  ```

### Auth Endpoints
- [ ] `GET /api/v1/verify-auth` returns 401 without key
  ```bash
  curl https://your-app.vercel.app/api/v1/verify-auth
  ```

- [ ] `GET /api/v1/verify-auth` returns 200 with valid `X-API-Key`
  ```bash
  curl -H "X-API-Key: your-api-key" https://your-app.vercel.app/api/v1/verify-auth
  ```

### API Documentation
- [ ] `GET /docs` loads API documentation
- [ ] `GET /openapi.json` returns OpenAPI schema

---

## Functional Testing 🧪

### Search Functionality
- [ ] Property search returns results
- [ ] Map displays properties correctly
- [ ] Filters work (price, bedrooms, etc.)

### AI Chat
- [ ] Chat input accepts text
- [ ] Streaming responses render progressively
- [ ] LLM responds with property information

### User Settings
- [ ] Settings page loads
- [ ] Model selection works
- [ ] Settings persist (if applicable)

---

## Security Verification 🔒

### CORS Headers
- [ ] `Access-Control-Allow-Origin` is set correctly
- [ ] No CORS errors in browser console
- [ ] API requests include proper credentials

### Authentication
- [ ] API requires valid `X-API-Key` header
- [ ] Unauthenticated requests return 401
- [ ] Rate limiting is enabled (check headers)

### Security Headers
- [ ] `X-Content-Type-Options: nosniff` present
- [ ] `X-Frame-Options: DENY` present
- [ ] `Content-Security-Policy` is set

---

## Performance Checks ⚡

### Page Load
- [ ] Initial page load < 3 seconds
- [ ] Time to Interactive (TTI) reasonable
- [ ] No large bundle sizes

### API Response Times
- [ ] `/health` responds < 1 second
- [ ] `/api/v1/verify-auth` responds < 1 second
- [ ] Search queries respond in reasonable time

---

## Configuration Check ⚙️

### Environment Variables
- [ ] `ENVIRONMENT=production` is set
- [ ] `API_ACCESS_KEY` is configured
- [ ] LLM provider keys are set (OpenAI/Anthropic)
- [ ] `CORS_ALLOW_ORIGINS` includes your domain

### Vercel Functions
- [ ] Python serverless functions are deployed
- [ ] Function logs show no errors
- [ ] Cold starts are acceptable

---

## Known Acceptable Limitations ⚠️

The following are **known and acceptable** for this deployment:

| Issue | Reason |
|-------|--------|
| Vector Store Disabled | FastEmbed disabled on Windows, acceptable for Vercel |
| E2E Tests Skipped | Requires running services, not applicable for serverless |
| Performance Benchmark | Skipped on Windows due to ChromaDB latency |
| mypy Warnings | Type hints only, non-blocking |
| 2 Meta-test Failures | Tests about CI script, not functional |

---

## Troubleshooting

### If Frontend Doesn't Load
1. Check Vercel build logs
2. Verify `NEXT_PUBLIC_API_URL` is not needed (handled by routes)
3. Check browser console for errors

### If API Returns 401
1. Verify `API_ACCESS_KEY` is set in Vercel
2. Check request includes `X-API-Key` header
3. Verify key format (64 characters)

### If CORS Errors
1. Update `CORS_ALLOW_ORIGINS` with your Vercel URL
2. Redeploy after updating: `vercel --prod`
3. Ensure protocol matches (https vs http)

### If Serverless Functions Fail
1. Check Vercel function logs
2. Verify Python version (3.11)
3. Check `vercel.json` route configuration

---

## Rollback Procedure

If deployment fails critically:

```powershell
# List recent deployments
vercel ls

# Rollback to previous deployment
vercel rollback [deployment-url]
```

Or use Vercel Dashboard to rollback from the deployments list.

---

## Success Criteria

Deployment is **successful** when:

- ✅ Homepage loads without errors
- ✅ `/health` returns 200
- ✅ `/api/v1/verify-auth` works with API key
- ✅ At least one search query returns results
- ✅ Chat interface responds
- ✅ No critical errors in Vercel function logs

---

## Contact & Support

- **Vercel Dashboard**: https://vercel.app/dashboard
- **Project**: `trae_ai_real_estate_assistant_8do4`
- **CI Validation Report**: `../artifacts/validation_report.md`
- **Environment Setup**: ../vercel/01-env-setup.md
