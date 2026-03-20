#!/bin/bash
# Docker GPU launcher for AI Real Estate Assistant
# Runs containers with GPU acceleration for local LLM (Ollama)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Help support
show_help() {
    cat << EOF
Usage: gpu.sh [options]

Docker GPU launcher for AI Real Estate Assistant.
Runs containers with GPU acceleration for local LLM (Ollama).

Options:
  --help, -h        Show this help message
  --dry-run         Show commands without executing

Requirements:
  - NVIDIA GPU with Docker support
  - nvidia-container-toolkit installed

Examples:
  ./scripts/docker/gpu.sh              # Start in GPU mode
  ./scripts/docker/gpu.sh --dry-run    # Show commands

For full options, run: python3 scripts/start.py --help
EOF
    exit 0
}

# Check for help flag
for arg in "$@"; do
    if [ "$arg" = "--help" ] || [ "$arg" = "-h" ]; then
        show_help
    fi
done

echo "Starting AI Real Estate Assistant in Docker GPU mode..."
echo "Project root: $PROJECT_ROOT"

# Check if Python3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is not installed or not on PATH."
    exit 1
fi

python3 "$PROJECT_ROOT/scripts/start.py" --mode docker --docker-mode gpu "$@"
