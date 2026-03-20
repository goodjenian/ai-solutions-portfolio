# Scripts Directory

Entry point scripts for running the AI Real Estate Assistant.

## Single Source of Truth

All scripts delegate to **`scripts/start.py`** - the Python-based launcher that handles:

- Environment detection (Docker vs local)
- GPU availability detection
- Dependency bootstrapping
- Port configuration

## Quick Reference

### Windows (PowerShell)

| Want to... | Command |
| ---------- | ------- |
| Auto-detect mode | `.\scripts\run.ps1` |
| Force local mode | `.\scripts\local\run.ps1` |
| Docker mode | `.\scripts\docker.ps1` |
| Backend only | `.\scripts\local\backend.ps1` |
| Frontend only | `.\scripts\local\frontend.ps1` |
| Docker CPU | `.\scripts\docker\cpu.ps1` |
| Docker GPU | `.\scripts\docker\gpu.ps1` |
| Docker + Internet | `.\scripts\docker\gpu-internet.ps1` |

### Linux/Mac (Bash)

| Want to... | Command |
| ---------- | ------- |
| Auto-detect mode | `./scripts/run.sh` |
| Force local mode | `./scripts/local/run.sh` |
| Docker mode | `./scripts/docker.sh` |
| Backend only | `./scripts/local/backend.sh` |
| Frontend only | `./scripts/local/frontend.sh` |
| Docker CPU | `./scripts/docker/cpu.sh` |
| Docker GPU | `./scripts/docker/gpu.sh` |
| Docker + Internet | `./scripts/docker/gpu-internet.sh` |

## Script Hierarchy

```text
scripts/
├── start.py                   # << SINGLE SOURCE OF TRUTH >>
├── bootstrap.py               # Environment setup
│
├── run.ps1 / run.sh           # Auto-detect mode
├── docker.ps1 / docker.sh     # Force Docker mode
│
├── local/                     # Local development
│   ├── run.ps1 / run.sh       # Both services
│   ├── backend.ps1 / run.sh   # Backend only
│   └── frontend.ps1 / run.sh  # Frontend only
│
├── docker/                    # Docker profiles
│   ├── cpu.ps1 / cpu.sh       # CPU-only mode
│   ├── gpu.ps1 / gpu.sh       # GPU-accelerated
│   ├── cpu-internet.ps1 / cpu-internet.sh
│   └── gpu-internet.ps1 / gpu-internet.sh
│
├── shared/                    # Shared utilities
│   └── resolve_python.ps1     # Python detection
│
├── setup/                     # Environment setup
│   ├── setup.ps1
│   └── setup.sh
│
├── ci/                        # CI/CD scripts
├── security/                  # Security scanning
└── README.md                  # This file
```

## Advanced Usage

All launcher flags are available through any wrapper script:

```powershell
# Dry run (show commands without executing)
.\scripts\run.ps1 --dry-run

# Custom ports
.\scripts\local\run.ps1 --backend-port 8080 --frontend-port 4000

# Skip bootstrap
.\scripts\local\run.ps1 --no-bootstrap

# Docker with internet search
.\scripts\docker.ps1 --internet

# Force specific Docker mode
.\scripts\docker.ps1 --docker-mode ask
```

### Launcher Flags

```text
--mode {auto,docker,local}       Execution mode (default: auto)
--service {all,backend,frontend} Which services (default: all)
--docker-mode {auto,cpu,gpu,ask} Docker variant (default: auto)
--internet                       Enable web search (SearXNG)
--dry-run                        Show commands without executing
--no-bootstrap                   Skip dependency installation
--backend-port PORT              Backend port (default: 8000)
--frontend-port PORT             Frontend port (default: 3000)
```

## Docker Profiles

| Profile | Description | Command |
| ------- | ----------- | ------- |
| (default) | External AI only | `docker compose up` |
| `local-llm` | + Ollama CPU | `--profile local-llm` |
| `local-llm` + `gpu` | + Ollama GPU | `--profile local-llm --profile gpu` |
| `internet` | + SearXNG search | `--profile internet` |

## Troubleshooting

### "Python not found" (Windows)

Run: `.\scripts\setup\setup.ps1`

Or install Python 3.11+ from https://python.org

### "Python3 not found" (Linux/Mac)

```bash
# Ubuntu/Debian
sudo apt install python3.11

# macOS
brew install python@3.11
```

### "uv not found"

```bash
# Windows
pip install uv

# Linux/Mac
pip3 install uv
# or
pipx install uv
```

### "Docker compose not available"

Install Docker Desktop (Windows/Mac) or Docker Compose plugin (Linux).

### Port conflicts

Use `--backend-port` and `--frontend-port` flags:

```powershell
.\scripts\local\run.ps1 --backend-port 8080 --frontend-port 4000
```

## Getting Help

All scripts support `--help`:

```powershell
.\scripts\run.ps1 --help
.\scripts\docker.ps1 --help
.\scripts\local\run.ps1 --help
```

For full options:

```bash
python scripts/start.py --help
```
