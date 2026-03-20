<#
.SYNOPSIS
    Docker GPU + Internet launcher for AI Real Estate Assistant.
.DESCRIPTION
    Runs the application in Docker with GPU acceleration and web search (SearXNG).
    Enables Ollama with GPU support and internet search for real-time data.
.PARAMETER Args
    Arguments to pass to the launcher.
.EXAMPLE
    .\scripts\docker\gpu-internet.ps1
    .\scripts\docker\gpu-internet.ps1 --dry-run
#>
param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$Args
)

$ErrorActionPreference = "Stop"

# Help support
if ($Args -contains '--help' -or $Args -contains '-h' -or $Args -contains '-?') {
    @”
Usage: gpu-internet.ps1 [options]

Docker GPU + Internet launcher for AI Real Estate Assistant.
Runs containers with GPU acceleration and SearXNG web search.

Options:
  --help, -h, -?    Show this help message
  --dry-run         Show commands without executing

Features:
  - Local LLM (Ollama) with GPU acceleration
  - SearXNG web search for real-time data

Requirements:
  - NVIDIA GPU with Docker support
  - nvidia-container-toolkit installed

Examples:
  .\scripts\docker\gpu-internet.ps1              # Full featured mode
  .\scripts\docker\gpu-internet.ps1 --dry-run    # Show commands

For full options, run: python scripts/start.py --help
“@
    exit 0
}

$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $root

. (Join-Path $root "scripts\shared\resolve_python.ps1")

$invocation = Get-PythonInvocation -ProjectRoot $root
& $invocation.Python @($invocation.Args) (Join-Path $root "scripts\start.py") --mode docker --docker-mode gpu --internet @Args
exit $LASTEXITCODE
