#!/bin/bash
# Local mode launcher for AI Real Estate Assistant (both services)
# Runs both backend and frontend locally without Docker

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Help support
show_help() {
    cat << EOF
Usage: run.sh [options]

Local development launcher for AI Real Estate Assistant.
Runs both backend and frontend services locally.

Options:
  --help, -h        Show this help message
  --dry-run         Show commands without executing
  --no-bootstrap    Skip dependency installation
  --backend-port    Backend port (default: 8000)
  --frontend-port   Frontend port (default: 3000)

Examples:
  ./scripts/local/run.sh                        # Start both services
  ./scripts/local/run.sh --no-bootstrap         # Skip bootstrap
  ./scripts/local/run.sh --backend-port 8080    # Custom backend port
  ./scripts/local/run.sh --dry-run              # Show commands

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

echo "Starting AI Real Estate Assistant locally..."
echo "Project root: $PROJECT_ROOT"

# Check if Python3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is not installed or not on PATH."
    echo "Please install Python 3.11+ from https://python.org"
    exit 1
fi

# Run the launcher script with local mode
python3 "$PROJECT_ROOT/scripts/start.py" --mode local "$@"
