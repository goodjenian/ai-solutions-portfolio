# =============================================================================
# AI Real Estate Assistant - Vercel Deployment Script (Windows)
# =============================================================================
#
# This script guides you through deploying to Vercel production
#
# Usage:
#   .\scripts\deploy-vercel.ps1
#
# =============================================================================

param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

function Write-Step {
    param([string]$Message)
    Write-Host "`n=== $Message ===" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Info {
    param([string]$Message)
    Write-Host "  $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

# =============================================================================
# Step 1: Check Vercel CLI
# =============================================================================
Write-Step "Step 1: Checking Vercel CLI"

try {
    $vercelVersion = vercel --version 2>$null
    Write-Success "Vercel CLI installed: $vercelVersion"
} catch {
    Write-Error "Vercel CLI not found!"
    Write-Info "Install with: npm i -g vercel"
    exit 1
}

# =============================================================================
# Step 2: Check .env file
# =============================================================================
Write-Step "Step 2: Checking environment file"

if (-not (Test-Path ".env")) {
    Write-Error ".env file not found!"
    Write-Info "Copy .env.example to .env and configure your API keys:"
    Write-Info "  cp .env.example .env"
    Write-Info "  Then edit .env and add your OPENAI_API_KEY or ANTHROPIC_API_KEY"
    exit 1
}
Write-Success ".env file found"

# =============================================================================
# Step 3: Generate API_ACCESS_KEY
# =============================================================================
Write-Step "Step 3: Generate API_ACCESS_KEY for Vercel"

Write-Info "Generate a secure API key for Vercel deployment:"
Write-Info ""
Write-Info "  PowerShell:"
Write-Info "    -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | % {[char]$_})"
Write-Info ""
Write-Info "  Python:"
Write-Info "    python -c `"import secrets; print(secrets.token_urlsafe(48))`""
Write-Info ""
Write-Info "  OpenSSL:"
Write-Info "    openssl rand -hex 32"
Write-Info ""
$confirm = Read-Host "Have you generated your API_ACCESS_KEY? (y/n)"
if ($confirm -ne "y") {
    Write-Info "Please generate the key first, then run this script again."
    exit 0
}

# =============================================================================
# Step 4: Login to Vercel
# =============================================================================
Write-Step "Step 4: Login to Vercel"

Write-Info "This will open a browser window for authentication..."
Write-Host ""
vercel login

if ($LASTEXITCODE -ne 0) {
    Write-Error "Vercel login failed!"
    exit 1
}
Write-Success "Logged in to Vercel"

# =============================================================================
# Step 5: Link project to Vercel
# =============================================================================
Write-Step "Step 5: Link project to Vercel"

Write-Info "Answer the prompts as follows:"
Write-Info "  - Set up and deploy? → Y"
Write-Info "  - Which scope? → Your account"
Write-Info "  - Link to existing project? → N (new project)"
Write-Info "  - Project name? → ai-real-estate-assistant"
Write-Info "  - Directory? → . (current directory)"
Write-Info "  - Override settings? → N (use existing vercel.json)"
Write-Host ""

$linkResult = vercel link 2>&1
if ($LASTEXITCODE -ne 0 -and $linkResult -notmatch "already linked") {
    Write-Error "Vercel link failed!"
    exit 1
}
Write-Success "Project linked to Vercel"

# =============================================================================
# Step 6: Environment Variables Setup Instructions
# =============================================================================
Write-Step "Step 6: Configure Environment Variables in Vercel"

Write-Info "Go to Vercel Dashboard to set environment variables:"
Write-Info ""
Write-Info "  1. Open: https://vercel.app/dashboard"
Write-Info "  2. Select your project"
Write-Info "  3. Go to: Settings → Environment Variables"
Write-Info "  4. Add these variables for Production, Preview, Development:"
Write-Info ""
Write-Info "     Variable           Value"
Write-Info "     ----------------   -----------------------------------"
Write-Info "     API_ACCESS_KEY     (your generated key)"
Write-Info "     ENVIRONMENT        production"
Write-Info "     OPENAI_API_KEY     (from your .env file)"
Write-Info "     ANTHROPIC_API_KEY  (from your .env file, optional)"
Write-Info "     CORS_ALLOW_ORIGINS https://your-app.vercel.app"
Write-Info ""
$confirm = Read-Host "Have you configured the environment variables? (y/n)"
if ($confirm -ne "y") {
    Write-Info "Please configure the variables first, then run this script again."
    Write-Info "You can re-run this script - it will skip the login/link steps."
    exit 0
}

# =============================================================================
# Step 7: Deploy to Production
# =============================================================================
Write-Step "Step 7: Deploy to Vercel Production"

Write-Info "Starting production deployment..."
Write-Host ""

vercel --prod

if ($LASTEXITCODE -ne 0) {
    Write-Error "Deployment failed!"
    Write-Info "Check the Vercel build logs for errors."
    exit 1
}

Write-Success "Deployment completed!"

# =============================================================================
# Step 8: Post-Deployment Instructions
# =============================================================================
Write-Step "Step 8: Post-Deployment Verification"

Write-Info "Test your deployment:"
Write-Info ""
Write-Info "  Health check:"
Write-Info "    curl https://your-app.vercel.app/health"
Write-Info ""
Write-Info "  Auth check (replace YOUR_KEY with your generated key):"
Write-Info "    curl -H `"X-API-Key: your-api-key" https://your-app.vercel.app/api/v1/verify-auth"
Write-Info ""
Write-Info "  Open in browser:"
Write-Info "    https://your-app.vercel.app"
Write-Info ""

Write-Success "Done! Your app is deployed to Vercel."
