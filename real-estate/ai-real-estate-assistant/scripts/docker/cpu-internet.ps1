<#
.SYNOPSIS
    Docker CPU + Internet launcher for AI Real Estate Assistant.
.DESCRIPTION
    Runs the application in Docker with CPU-only mode and web search (SearXNG).
    Enables internet search for real-time property market data.
.PARAMETER Args
    Arguments to pass to the launcher.
.EXAMPLE
    .\scripts\docker\cpu-internet.ps1
    .\scripts\docker\cpu-internet.ps1 --dry-run
#>
param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$Args
)

$ErrorActionPreference = "Stop"

# Help support
if ($Args -contains '--help' -or $Args -contains '-h' -or $Args -contains '-?') {
    @”
Usage: cpu-internet.ps1 [options]

Docker CPU + Internet launcher for AI Real Estate Assistant.
Runs containers with CPU mode and SearXNG web search.

Options:
  --help, -h, -?    Show this help message
  --dry-run         Show commands without executing

Features:
  - External AI providers (OpenAI, Anthropic, etc.)
  - SearXNG web search for real-time data

Examples:
  .\scripts\docker\cpu-internet.ps1              # Start with web search
  .\scripts\docker\cpu-internet.ps1 --dry-run    # Show commands

For full options, run: python scripts/start.py --help
“@
    exit 0
}

$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $root

. (Join-Path $root "scripts\shared\resolve_python.ps1")

$invocation = Get-PythonInvocation -ProjectRoot $root
& $invocation.Python @($invocation.Args) (Join-Path $root "scripts\start.py") --mode docker --docker-mode cpu --internet @Args
exit $LASTEXITCODE
