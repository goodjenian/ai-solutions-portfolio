#!/usr/bin/env bash
# =============================================================================
# AI Real Estate Assistant - Vercel Deployment Script (Linux/Mac)
# =============================================================================
#
# This script guides you through deploying to Vercel production
#
# Usage:
#   ./scripts/deploy-vercel.sh
#
# =============================================================================

set -eu

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$ROOT_DIR"

# Helper functions
write_step() {
    echo -e "\n${CYAN}=== $1 ===${NC}"
}

write_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

write_info() {
    echo -e "${YELLOW}  $1${NC}"
}

write_error() {
    echo -e "${RED}✗ $1${NC}"
}

# =============================================================================
# Step 1: Check Vercel CLI
# =============================================================================
write_step "Step 1: Checking Vercel CLI"

if ! vercel --version &>/dev/null; then
    write_error "Vercel CLI not found!"
    write_info "Install with: npm i -g vercel"
    exit 1
fi

VERCEL_VERSION=$(vercel --version)
write_success "Vercel CLI installed: $VERCEL_VERSION"

# =============================================================================
# Step 2: Check .env file
# =============================================================================
write_step "Step 2: Checking environment file"

if [ ! -f ".env" ]; then
    write_error ".env file not found!"
    write_info "Copy .env.example to .env and configure your API keys:"
    write_info "  cp .env.example .env"
    write_info "  Then edit .env and add your OPENAI_API_KEY or ANTHROPIC_API_KEY"
    exit 1
fi

write_success ".env file found"

# =============================================================================
# Step 3: Generate API_ACCESS_KEY
# =============================================================================
write_step "Step 3: Generate API_ACCESS_KEY for Vercel"

write_info "Generate a secure API key for Vercel deployment:"
write_info ""
write_info "  Python:"
write_info "    python3 -c 'import secrets; print(secrets.token_urlsafe(48))'"
write_info ""
write_info "  OpenSSL:"
write_info "    openssl rand -hex 32"
write_info ""
read -p "Have you generated your API_ACCESS_KEY? (y/n) " -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    write_info "Please generate the key first, then run this script again."
    exit 0
fi

# =============================================================================
# Step 4: Login to Vercel
# =============================================================================
write_step "Step 4: Login to Vercel"

write_info "This will open a browser window for authentication..."
echo ""

if ! vercel login; then
    write_error "Vercel login failed!"
    exit 1
fi

write_success "Logged in to Vercel"

# =============================================================================
# Step 5: Link project to Vercel
# =============================================================================
write_step "Step 5: Link project to Vercel"

write_info "Answer the prompts as follows:"
write_info "  - Set up and deploy? → Y"
write_info "  - Which scope? → Your account"
write_info "  - Link to existing project? → N (new project)"
write_info "  - Project name? → ai-real-estate-assistant"
write_info "  - Directory? → . (current directory)"
write_info "  - Override settings? → N (use existing vercel.json)"
echo ""

# vercel link returns 1 if already linked, which is fine
vercel link || true

write_success "Project linked to Vercel"

# =============================================================================
# Step 6: Environment Variables Setup Instructions
# =============================================================================
write_step "Step 6: Configure Environment Variables in Vercel"

write_info "Go to Vercel Dashboard to set environment variables:"
write_info ""
write_info "  1. Open: https://vercel.app/dashboard"
write_info "  2. Select your project"
write_info "  3. Go to: Settings → Environment Variables"
write_info "  4. Add these variables for Production, Preview, Development:"
write_info ""
write_info "     Variable           Value"
write_info "     ----------------   -----------------------------------"
write_info "     API_ACCESS_KEY     (your generated key)"
write_info "     ENVIRONMENT        production"
write_info "     OPENAI_API_KEY     (from your .env file)"
write_info "     ANTHROPIC_API_KEY  (from your .env file, optional)"
write_info "     CORS_ALLOW_ORIGINS https://your-app.vercel.app"
write_info ""
read -p "Have you configured the environment variables? (y/n) " -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    write_info "Please configure the variables first, then run this script again."
    write_info "You can re-run this script - it will skip the login/link steps."
    exit 0
fi

# =============================================================================
# Step 7: Deploy to Production
# =============================================================================
write_step "Step 7: Deploy to Vercel Production"

write_info "Starting production deployment..."
echo ""

if ! vercel --prod; then
    write_error "Deployment failed!"
    write_info "Check the Vercel build logs for errors."
    exit 1
fi

write_success "Deployment completed!"

# =============================================================================
# Step 8: Post-Deployment Instructions
# =============================================================================
write_step "Step 8: Post-Deployment Verification"

write_info "Test your deployment:"
write_info ""
write_info "  Health check:"
write_info "    curl https://your-app.vercel.app/health"
write_info ""
write_info "  Auth check (replace YOUR_KEY with your generated key):"
write_info "    curl -H 'X-API-Key: your-api-key' https://your-app.vercel.app/api/v1/verify-auth"
write_info ""
write_info "  Open in browser:"
write_info "    https://your-app.vercel.app"
write_info ""

write_success "Done! Your app is deployed to Vercel."
