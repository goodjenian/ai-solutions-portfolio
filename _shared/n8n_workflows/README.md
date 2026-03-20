# GoodySEO n8n API Gateway Workflows

Each JSON file is an n8n workflow that acts as the API gateway layer for one commercial product.

## How to Import

1. Open your n8n instance
2. Go to **Workflows** → **Import from File**
3. Select the desired `.json` file
4. Activate the workflow after setting credentials

## Workflow Map

| File | Product | Webhook Path | FastAPI Port | Timeout |
|------|---------|-------------|-------------|---------|
| `strategy_ai.json` | StrategyAI | `POST /strategyai/run` | 8001 | 5 min |
| `content_flow.json` | ContentFlow | `POST /contentflow/run` | 8002 | 3 min |
| `inbox_ai.json` | InboxAI | `POST /inboxai/run` | 8003 | 2 min |
| `meeting_ops.json` | MeetingOps | `POST /meetingops/run` | 8004 | 3 min |
| `trad_ai.json` | TradAI | `POST /tradai/run` | 8005 | 5 min |

## Request Format

All workflows expect:

**Headers:**
```
X-Api-Key: your-api-key
Content-Type: application/json
```

**Body (per product):**

| Product | Required Fields |
|---------|----------------|
| StrategyAI | `url`, `objective` |
| ContentFlow | `topic`, `platform` (instagram/linkedin/twitter/facebook) |
| InboxAI | `email_snippet`, `context` (optional) |
| MeetingOps | `transcript`, `meeting_title` (optional) |
| TradAI | `stock_symbol` (e.g. AAPL) |

## Architecture

```
Client → n8n Webhook → Validate → FastAPI Service → Response
                          ↓ (on error)
                       Handle Error → Error Response
```

The FastAPI service handles:
- API key authentication (`goodyseo_security.auth`)
- Per-client rate limiting (`goodyseo_security.rate_limiter`)
- OpenAI budget enforcement (`goodyseo_security.cost_guard`)
- Audit logging (`goodyseo_security.audit`)

The n8n gateway adds:
- Input validation (field presence, format checks)
- PII pattern detection (InboxAI)
- Payload size enforcement
- Financial disclaimer headers (TradAI)

## Prerequisites

FastAPI services must be running locally:

```bash
cd _shared && pip install -e .
cd marketing/marketing_strategy && uvicorn api_server:app --port 8001 --reload
cd marketing/instagram_post     && uvicorn api_server:app --port 8002 --reload
cd productivity/email_auto_responder_flow && uvicorn api_server:app --port 8003 --reload
cd productivity/meeting_assistant_flow    && uvicorn api_server:app --port 8004 --reload
cd finance/stock_analysis                 && uvicorn api_server:app --port 8005 --reload
```
