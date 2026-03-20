<#
.SYNOPSIS
    Docker GPU launcher for AI Real Estate Assistant.
.DESCRIPTION
    Runs the application in Docker with GPU acceleration for local LLM inference.
    Enables Ollama with GPU support.
.PARAMETER Args
    Arguments to pass to the launcher.
.EXAMPLE
    .\scripts\docker\gpu.ps1
    .\scripts\docker\gpu.ps1 --dry-run
#>
param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$Args
)

$ErrorActionPreference = "Stop"

# Help support
if ($Args -contains '--help' -or $Args -contains '-h' -or $Args -contains '-?') {
    @”
Usage: gpu.ps1 [options]

Docker GPU launcher for AI Real Estate Assistant.
Runs containers with GPU acceleration for local LLM (Ollama).

Options:
  --help, -h, -?    Show this help message
  --dry-run         Show commands without executing

Requirements:
  - NVIDIA GPU with Docker support
  - nvidia-container-toolkit installed

Examples:
  .\scripts\docker\gpu.ps1              # Start in GPU mode
  .\scripts\docker\gpu.ps1 --dry-run    # Show commands

For full options, run: python scripts/start.py --help
“@
    exit 0
}

$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $root

. (Join-Path $root "scripts\shared\resolve_python.ps1")

$invocation = Get-PythonInvocation -ProjectRoot $root
& $invocation.Python @($invocation.Args) (Join-Path $root "scripts\start.py") --mode docker --docker-mode gpu @Args
exit $LASTEXITCODE
