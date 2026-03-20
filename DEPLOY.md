# GoodySEO AI Products — Guia de Deploy

## Visão Geral

```
Internet / n8n
     │
     ▼
[n8n Webhook] ──► [FastAPI Service] ──► [OpenAI / Serper / SEC / Slack / Trello]
     │                  │
     │            (auth + rate limit + budget + audit)
     ▼
  Resposta
```

---

## Pré-requisitos

- **Docker** e **Docker Compose** instalados
- **Python 3.11+** (para o script de OAuth do Gmail)
- **Conta OpenAI** com saldo
- **n8n** rodando (cloud ou self-hosted)

---

## Passo 1 — Clonar o repositório

```bash
git clone https://github.com/goodjenian/ai-solutions-portfolio.git
cd ai-solutions-portfolio
```

---

## Passo 2 — Criar as chaves de API

Gere uma chave para uso interno e uma por cliente:

```bash
# Gerar chaves seguras
python3 -c "import secrets; print('INTERNA:', secrets.token_urlsafe(32))"
python3 -c "import secrets; print('CLIENTE-1:', secrets.token_urlsafe(32))"
python3 -c "import secrets; print('CLIENTE-2:', secrets.token_urlsafe(32))"
```

Guarde esses valores — você vai precisar deles no Passo 3.

---

## Passo 3 — Configurar o .env

```bash
cp .env.template .env
```

Abra `.env` e preencha todos os campos. Checklist mínimo para começar:

| Variável | Onde obter | Necessário para |
|----------|-----------|----------------|
| `GOODYSEO_API_KEYS` | Gerado no Passo 2 | Todos |
| `OPENAI_API_KEY` | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) | Todos |
| `SERPER_API_KEY` | [serper.dev](https://serper.dev/) — free tier | StrategyAI, ContentFlow, InboxAI |
| `BROWSERLESS_API_KEY` | [browserless.io](https://www.browserless.io/) — free tier | ContentFlow, TradAI |
| `TAVILY_API_KEY` | [app.tavily.com](https://app.tavily.com/) | InboxAI |
| `MY_EMAIL` | Seu endereço Gmail | InboxAI |
| `SLACK_TOKEN` | [api.slack.com/apps](https://api.slack.com/apps) | MeetingOps |
| `SLACK_CHANNEL_ID` | ID do canal Slack (começa com C) | MeetingOps |
| `TRELLO_API_KEY` | [trello.com/app-key](https://trello.com/app-key) | MeetingOps |
| `TRELLO_TOKEN` | OAuth em trello.com/app-key | MeetingOps |
| `TRELLO_LIST_ID` | ID da lista Trello | MeetingOps |
| `SEC_API_API_KEY` | [sec-api.io](https://sec-api.io/) — free tier | TradAI |
| `SEC_API_USER_AGENT` | `"NomeApp contact@seudominio.com"` | TradAI |

> **Dica:** Para testar sem ativar todos os serviços, comece com StrategyAI e MeetingOps — precisam só de `OPENAI_API_KEY` + `SERPER_API_KEY`.

---

## Passo 4 — Configurar Gmail OAuth (apenas InboxAI)

> Pule este passo se não for usar InboxAI.

### 4.1 Criar projeto no Google Cloud

1. Acesse [console.cloud.google.com](https://console.cloud.google.com/)
2. Crie um novo projeto: **GoodySEO InboxAI**
3. Ative a **Gmail API**: APIs & Services → Enable APIs → Gmail API
4. Crie credenciais OAuth: APIs & Services → Credentials → Create Credentials → OAuth client ID
   - Application type: **Desktop app**
   - Baixe o arquivo JSON e salve como `secrets/gmail_credentials.json`

### 4.2 Gerar o token de acesso

```bash
mkdir -p secrets
# Copie o arquivo baixado do Google Cloud
mv ~/Downloads/client_secret_*.json secrets/gmail_credentials.json

# Gerar token (abrirá o browser para autorizar)
pip install google-auth-oauthlib google-api-python-client
python3 - <<'EOF'
from google_auth_oauthlib.flow import InstalledAppFlow
import json, pathlib

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
flow = InstalledAppFlow.from_client_secrets_file('secrets/gmail_credentials.json', SCOPES)
creds = flow.run_local_server(port=0)
pathlib.Path('secrets/gmail_token.json').write_text(creds.to_json())
print("Token salvo em secrets/gmail_token.json")
EOF
```

---

## Passo 5 — Subir os serviços com Docker

```bash
# Build e subir tudo (primeira vez demora ~5-10 min)
docker compose up --build -d

# Ver logs em tempo real
docker compose logs -f

# Ver status de saúde
docker compose ps
```

Para subir só alguns serviços:
```bash
docker compose up -d strategyai meetingops redis
```

Verificar se todos estão saudáveis:
```bash
curl http://localhost:8001/health  # StrategyAI
curl http://localhost:8002/health  # ContentFlow
curl http://localhost:8003/health  # InboxAI
curl http://localhost:8004/health  # MeetingOps
curl http://localhost:8005/health  # TradAI
```

---

## Passo 6 — Testar com curl

```bash
# Substitua SUA_CHAVE pela chave gerada no Passo 2
API_KEY="SUA_CHAVE_INTERNA"

# StrategyAI
curl -s -X POST http://localhost:8001/run \
  -H "X-Api-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://goodyseo.com","objective":"aumentar tráfego orgânico"}' | jq .

# MeetingOps
curl -s -X POST http://localhost:8004/run \
  -H "X-Api-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"transcript":"João: Vamos lançar a campanha na semana que vem. Maria: Ok, eu fico responsável pelo post.","meeting_title":"Reunião de Marketing"}' | jq .

# TradAI
curl -s -X POST http://localhost:8005/run \
  -H "X-Api-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"stock_symbol":"AAPL"}' | jq .

# Ver seu uso/custo
curl -s http://localhost:8001/usage/me \
  -H "X-Api-Key: $API_KEY" | jq .
```

---

## Passo 7 — Importar workflows no n8n

1. No n8n: **Workflows → Import from File**
2. Importe cada arquivo de `_shared/n8n_workflows/`
3. Em cada workflow, atualize a URL base se os serviços estiverem em servidor remoto:
   - Troque `http://localhost:800X` pelo IP/domínio do seu servidor
4. **Ative** cada workflow

### URLs dos webhooks após importação:

| Produto | Webhook URL |
|---------|------------|
| StrategyAI | `https://seu-n8n.com/webhook/strategyai/run` |
| ContentFlow | `https://seu-n8n.com/webhook/contentflow/run` |
| InboxAI | `https://seu-n8n.com/webhook/inboxai/run` |
| MeetingOps | `https://seu-n8n.com/webhook/meetingops/run` |
| TradAI | `https://seu-n8n.com/webhook/tradai/run` |

---

## Passo 8 — Deploy em servidor (produção)

Para uso comercial, você precisa de um servidor. Opções recomendadas:

### Opção A — Railway (mais simples, ~$10-20/mês total)

```bash
# Instalar Railway CLI
npm install -g @railway/cli
railway login
railway init

# Deploy cada serviço como um Railway Service apontando para o Dockerfile correto
# Configure as variáveis de ambiente no dashboard do Railway
```

### Opção B — VPS (DigitalOcean, Hetzner, Vultr — mais barato a longo prazo)

```bash
# Em um VPS com Ubuntu 22.04:
apt update && apt install -y docker.io docker-compose-plugin

git clone https://github.com/goodjenian/ai-solutions-portfolio.git
cd ai-solutions-portfolio
cp .env.template .env
nano .env  # preencher variáveis

docker compose up -d --build
```

Adicionar um domínio e HTTPS com Nginx + Certbot:
```bash
apt install -y nginx certbot python3-certbot-nginx
# Configurar nginx como reverse proxy para portas 8001-8005
certbot --nginx -d api.goodyseo.com
```

### Opção C — Render.com (free tier disponível)

1. Conectar repositório GitHub no Render
2. Criar um **Web Service** por produto
3. Definir Dockerfile: `docker/Dockerfile.strategyai` etc.
4. Adicionar variáveis de ambiente no painel

---

## Gerenciar clientes

### Adicionar um novo cliente

```bash
# 1. Gerar chave
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 2. Adicionar ao .env (separado por vírgula, sem espaço)
# GOODYSEO_API_KEYS=chave-interna,chave-cliente-xyz,NOVA_CHAVE_AQUI

# 3. Reiniciar os serviços
docker compose restart
```

### Ver consumo de um cliente

```bash
curl http://localhost:8001/usage/me \
  -H "X-Api-Key: CHAVE_DO_CLIENTE" | jq .
```

### Logs de auditoria

```bash
# Logs ficam em: _shared/goodyseo_security/audit/
ls _shared/goodyseo_security/audit/
# audit_2025-03-20.csv — uma linha por request, com cliente hasheado, custo, timestamp
```

---

## Monitoramento

```bash
# Status de todos os serviços
docker compose ps

# Logs de um serviço específico
docker compose logs -f strategyai

# Reiniciar um serviço com problema
docker compose restart meetingops

# Parar tudo
docker compose down

# Atualizar após mudança no código
git pull
docker compose up -d --build
```

---

## Solução de problemas

| Erro | Causa | Solução |
|------|-------|---------|
| `401 Authentication required` | X-Api-Key ausente | Adicionar header `X-Api-Key` |
| `403 Invalid API key` | Chave incorreta | Verificar `GOODYSEO_API_KEYS` no .env |
| `429 Rate limit` | Muitas requests do cliente | Aguardar reset ou aumentar `rate_limit_rpm` |
| `402 Daily budget exhausted` | Limite de custo atingido | Aguardar meia-noite UTC ou aumentar `daily_budget_usd` |
| `500 Agent error` | Erro interno do CrewAI | Ver `docker compose logs <serviço>` |
| InboxAI: `credentials not found` | gmail_credentials.json ausente | Executar Passo 4 |
