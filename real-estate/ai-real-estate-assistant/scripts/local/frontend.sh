#!/bin/bash
# Local frontend-only launcher for AI Real Estate Assistant
# Runs only the Next.js frontend locally without Docker

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Help support
show_help() {
    cat << EOF
Usage: frontend.sh [options]

Local frontend-only launcher for AI Real Estate Assistant.
Runs only the Next.js frontend (port 3000).

Options:
  --help, -h        Show this help message
  --dry-run         Show commands without executing
  --no-bootstrap    Skip dependency installation
  --frontend-port   Frontend port (default: 3000)

Examples:
  ./scripts/local/frontend.sh                        # Start frontend
  ./scripts/local/frontend.sh --no-bootstrap         # Skip bootstrap
  ./scripts/local/frontend.sh --frontend-port 4000   # Custom port
  ./scripts/local/frontend.sh --dry-run              # Show commands

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

echo "Starting AI Real Estate Assistant frontend..."
echo "Project root: $PROJECT_ROOT"

# Check if Python3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is not installed or not on PATH."
    echo "Please install Python 3.11+ from https://python.org"
    exit 1
fi

# Run the launcher script with local mode and frontend only
python3 "$PROJECT_ROOT/scripts/start.py" --mode local --service frontend "$@"
