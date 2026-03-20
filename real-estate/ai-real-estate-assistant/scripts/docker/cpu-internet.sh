#!/bin/bash
# Docker CPU + Internet launcher for AI Real Estate Assistant
# Runs containers with CPU mode and SearXNG web search

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Help support
show_help() {
    cat << EOF
Usage: cpu-internet.sh [options]

Docker CPU + Internet launcher for AI Real Estate Assistant.
Runs containers with CPU mode and SearXNG web search.

Options:
  --help, -h        Show this help message
  --dry-run         Show commands without executing

Features:
  - External AI providers (OpenAI, Anthropic, etc.)
  - SearXNG web search for real-time data

Examples:
  ./scripts/docker/cpu-internet.sh              # Start with web search
  ./scripts/docker/cpu-internet.sh --dry-run    # Show commands

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

echo "Starting AI Real Estate Assistant in Docker CPU+Internet mode..."
echo "Project root: $PROJECT_ROOT"

# Check if Python3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is not installed or not on PATH."
    exit 1
fi

python3 "$PROJECT_ROOT/scripts/start.py" --mode docker --docker-mode cpu --internet "$@"
