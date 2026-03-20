<#
.SYNOPSIS
    Docker CPU-only launcher for AI Real Estate Assistant.
.DESCRIPTION
    Runs the application in Docker with CPU-only mode (no GPU acceleration).
    Uses external AI providers (OpenAI, Anthropic, etc.) by default.
.PARAMETER Args
    Arguments to pass to the launcher.
.EXAMPLE
    .\scripts\docker\cpu.ps1
    .\scripts\docker\cpu.ps1 --dry-run
#>
param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$Args
)

$ErrorActionPreference = "Stop"

# Help support
if ($Args -contains '--help' -or $Args -contains '-h' -or $Args -contains '-?') {
    @”
Usage: cpu.ps1 [options]

Docker CPU-only launcher for AI Real Estate Assistant.
Runs containers without GPU acceleration.

Options:
  --help, -h, -?    Show this help message
  --dry-run         Show commands without executing

Examples:
  .\scripts\docker\cpu.ps1              # Start in CPU mode
  .\scripts\docker\cpu.ps1 --dry-run    # Show commands

For full options, run: python scripts/start.py --help
“@
    exit 0
}

$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $root

. (Join-Path $root "scripts\shared\resolve_python.ps1")

$invocation = Get-PythonInvocation -ProjectRoot $root
& $invocation.Python @($invocation.Args) (Join-Path $root "scripts\start.py") --mode docker --docker-mode cpu @Args
exit $LASTEXITCODE
