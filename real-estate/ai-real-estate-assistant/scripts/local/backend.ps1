<#
.SYNOPSIS
    Local backend-only launcher for AI Real Estate Assistant.
.DESCRIPTION
    Runs only the FastAPI backend locally without Docker.
    All arguments are passed through to the Python launcher.
.PARAMETER Args
    Arguments to pass to the launcher.
.EXAMPLE
    .\scripts\local\backend.ps1
    .\scripts\local\backend.ps1 --dry-run
    .\scripts\local\backend.ps1 --backend-port 8080
#>
param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$Args
)

$ErrorActionPreference = "Stop"

# Help support
if ($Args -contains '--help' -or $Args -contains '-h' -or $Args -contains '-?') {
    @”
Usage: backend.ps1 [options]

Local backend-only launcher for AI Real Estate Assistant.
Runs only the FastAPI backend (port 8000).

Options:
  --help, -h, -?    Show this help message
  --dry-run         Show commands without executing
  --no-bootstrap    Skip dependency installation
  --backend-port    Backend port (default: 8000)

Examples:
  .\scripts\local\backend.ps1                        # Start backend
  .\scripts\local\backend.ps1 --no-bootstrap         # Skip bootstrap
  .\scripts\local\backend.ps1 --backend-port 8080    # Custom port
  .\scripts\local\backend.ps1 --dry-run              # Show commands

For full options, run: python scripts/start.py --help
“@
    exit 0
}

$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $root

. (Join-Path $root "scripts\shared\resolve_python.ps1")

$invocation = Get-PythonInvocation -ProjectRoot $root
& $invocation.Python @($invocation.Args) (Join-Path $root "scripts\start.py") --mode local --service backend @Args
exit $LASTEXITCODE
