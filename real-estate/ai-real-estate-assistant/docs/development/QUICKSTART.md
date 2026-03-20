# Quickstart: Run Your AI Realtor in 5 Minutes

## Prerequisites
- Docker and Docker Compose
- Create `.env` from `.env.example`
- Provide BYOK: `OPENAI_API_KEY` or configure local Ollama (`OLLAMA_BASE_URL`)

## Steps
1. Copy environment:
   ```powershell
   Copy-Item .env.example .env
   ```
2. Set keys and DB options in `.env`.
3. Start services (recommended one-command scripts):
   ```powershell
   # CPU (no GPU required)
   .\scripts\dev\run-docker-cpu.ps1

   # GPU (if Docker GPU is available)
   .\scripts\dev\run-docker-gpu.ps1

   # GPU + Internet web research (starts the `internet` compose profile)
   .\scripts\dev\run-docker-gpu-internet.ps1
   ```
   Or run directly:
   ```powershell
   .\scripts\dev\start.ps1 --mode docker --docker-mode auto
   .\scripts\dev\start.ps1 --mode docker --docker-mode gpu --internet
   ```
   Optional: start only Redis for MCP/caching
   ```powershell
   docker compose up -d redis
   ```
4. Open:
   - Frontend: http://localhost:3000
   - Backend: http://localhost:8000/docs
   - Redis (optional): redis://localhost:6379

## Local RAG
- Upload PDFs/Docs in the app and query property details.

## Troubleshooting
- Ensure backend CORS allows the frontend origin.
- Check logs:
  ```powershell
  docker compose logs -f
  ```
