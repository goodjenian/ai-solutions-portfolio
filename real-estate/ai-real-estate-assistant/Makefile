# AI Real Estate Assistant - Makefile
# Quick commands for development, testing, and CI/CD
#
# Usage:
#   make help        - Show all available targets
#   make security    - Run security scans
#   make test        - Run all tests
#   make lint        - Run linting
#   make dev         - Start development servers
#   make docker-up   - Start Docker containers
#   make docker-down - Stop Docker containers
#   make ci          - Run full CI locally

# Variables
PYTHON := python
DOCKER_COMPOSE := docker compose
DOCKER_COMPOSE_FILE := deploy/compose/docker-compose.yml
SCRIPTS_DIR := scripts

# Colors for help output
BLUE := \033[34m
GREEN := \033[32m
RESET := \033[0m

# Phony targets
.PHONY: help security security-quick test test-api test-web lint lint-api lint-web format
.PHONY: docker-up docker-down docker-logs docker-build
.PHONY: ci ci-quick dev dev-api dev-web setup clean install

# Default target
.DEFAULT_GOAL := help

## ============================================================================
## HELP
## ============================================================================

help: ## Show this help message
	@echo "$(BLUE)AI Real Estate Assistant - Available Commands$(RESET)"
	@echo ""
	@echo "$(GREEN)Security:$(RESET)"
	@sed -n 's/^## security/\tmake &/p' $(MAKEFILE_LIST)
	@sed -n 's/^## security-quick/\tmake &/p' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(GREEN)Testing:$(RESET)"
	@sed -n 's/^## test/\tmake &/p' $(MAKEFILE_LIST) | head -3
	@echo ""
	@echo "$(GREEN)Linting & Formatting:$(RESET)"
	@sed -n 's/^## lint/\tmake &/p' $(MAKEFILE_LIST)
	@sed -n 's/^## format/\tmake &/p' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(GREEN)Development:$(RESET)"
	@sed -n 's/^## dev/\tmake &/p' $(MAKEFILE_LIST) | head -2
	@sed -n 's/^## setup/\tmake &/p' $(MAKEFILE_LIST)
	@sed -n 's/^## install/\tmake &/p' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(GREEN)Docker:$(RESET)"
	@sed -n 's/^## docker/\tmake &/p' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(GREEN)CI/CD:$(RESET)"
	@sed -n 's/^## ci/\tmake &/p' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(GREEN)Maintenance:$(RESET)"
	@sed -n 's/^## clean/\tmake &/p' $(MAKEFILE_LIST)

## ============================================================================
## SECURITY
## ============================================================================

## security: Run all security scans (Gitleaks, Semgrep, Bandit, pip-audit)
security:
	$(PYTHON) $(SCRIPTS_DIR)/security/local_scan.py

## security-quick: Run quick security scan (skip pip-audit)
security-quick:
	$(PYTHON) $(SCRIPTS_DIR)/security/local_scan.py --quick

## ============================================================================
## TESTING
## ============================================================================

## test: Run all tests (backend + frontend)
test: test-api test-web

## test-api: Run backend tests with coverage
test-api:
	cd apps/api && $(PYTHON) -m pytest tests/unit tests/integration --cov=. --cov-report=term -n auto

## test-web: Run frontend tests
test-web:
	cd apps/web && npm test

## ============================================================================
## LINTING & FORMATTING
## ============================================================================

## lint: Run all linting (backend + frontend)
lint: lint-api lint-web

## lint-api: Run backend linting (ruff)
lint-api:
	cd apps/api && $(PYTHON) -m ruff check .

## lint-web: Run frontend linting (ESLint)
lint-web:
	cd apps/web && npm run lint

## format: Format all code (backend + frontend)
format:
	cd apps/api && $(PYTHON) -m ruff format .
	cd apps/web && npm run format || true

## ============================================================================
## DEVELOPMENT
## ============================================================================

## dev: Start development servers (auto-detect Docker or local)
dev:
	$(PYTHON) $(SCRIPTS_DIR)/start.py --mode auto

## dev-api: Start backend development server only
dev-api:
	$(PYTHON) $(SCRIPTS_DIR)/start.py --mode local --service backend

## dev-web: Start frontend development server only
dev-web:
	$(PYTHON) $(SCRIPTS_DIR)/start.py --mode local --service frontend

## setup: Run environment setup (first-time setup)
setup:
	$(PYTHON) $(SCRIPTS_DIR)/bootstrap.py

## install: Install all dependencies
install:
	cd apps/api && uv pip install -e .[dev]
	cd apps/web && npm install

## ============================================================================
## DOCKER
## ============================================================================

## docker-up: Start Docker containers (background)
docker-up:
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) up -d

## docker-down: Stop Docker containers
docker-down:
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) down

## docker-logs: Show Docker container logs
docker-logs:
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) logs -f

## docker-build: Build Docker images
docker-build:
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) build

## docker-gpu: Start Docker with GPU support (Ollama)
docker-gpu:
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) --profile local-llm --profile gpu up -d

## docker-internet: Start Docker with internet search (SearXNG)
docker-internet:
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) --profile internet up -d

## ============================================================================
## CI/CD
## ============================================================================

## ci: Run full CI pipeline locally
ci:
	$(PYTHON) $(SCRIPTS_DIR)/workflows/full_ci.py

## ci-quick: Run quick CI (skip slower scans)
ci-quick:
	$(PYTHON) $(SCRIPTS_DIR)/ci/ci_parity.py --quick

## ============================================================================
## MAINTENANCE
## ============================================================================

## clean: Clean build artifacts and caches
clean:
	rm -rf apps/api/.pytest_cache apps/api/__pycache__ apps/api/.coverage apps/api/.ruff_cache
	rm -rf apps/api/**/__pycache__ apps/api/**/*.pyc
	rm -rf apps/web/.next apps/web/node_modules/.cache apps/web/coverage
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

## clean-all: Deep clean (includes node_modules, .venv)
clean-all: clean
	rm -rf apps/web/node_modules
	rm -rf node_modules
	rm -rf .venv venv .venv_ci
