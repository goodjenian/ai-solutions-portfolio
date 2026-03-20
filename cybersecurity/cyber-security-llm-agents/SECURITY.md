# Security Guidelines — cyber-security-llm-agents

## ⚠️ Mandatory: Isolated Environment

This tool executes LLM-generated shell commands on the host. **Never run on a production or shared machine.**

Required setup (choose one):
1. **Docker** (recommended): `docker compose up` — runs in a sandboxed container with no host mounts
2. **VM**: Use a disposable virtual machine (e.g., VirtualBox snapshot)
3. **Air-gapped lab**: Dedicated network-isolated host

## Required Environment Variables

Copy `.env_template` to `.env` before running:

```
OPENAI_API_KEY=sk-...         # Your OpenAI key
SANDBOX_ENABLED=true          # Must be set to "true" to run
```

The application will **refuse to start** if `SANDBOX_ENABLED` is not explicitly set to `true`.

## What This Tool Does

- Sends prompts to an LLM (OpenAI GPT)
- Receives shell commands as responses
- Executes those commands locally via `subprocess`

## Threat Model

| Risk | Mitigation |
|------|-----------|
| LLM generates destructive commands | Run in isolated container/VM |
| API key leakage | Key loaded from `.env` (never committed) |
| Network exfiltration by LLM-generated code | Use air-gapped lab or egress firewall rules |
| Prompt injection via external data | Treat all agent outputs as untrusted |

## Reporting Issues

Open an issue at the upstream repo: https://github.com/NVISOsecurity/cyber-security-llm-agents
