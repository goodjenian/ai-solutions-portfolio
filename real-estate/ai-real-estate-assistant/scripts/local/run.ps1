<#
.SYNOPSIS
    Local mode launcher for AI Real Estate Assistant (both services).
.DESCRIPTION
    Runs both backend and frontend locally without Docker.
    All arguments are passed through to the Python launcher.
.PARAMETER Args
    Arguments to pass to the launcher.
.EXAMPLE
    .\scripts\local\run.ps1
    .\scripts\local\run.ps1 --dry-run
    .\scripts\local\run.ps1 --backend-port 8080
#>
param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$Args
)

$ErrorActionPreference = "Stop"

# Help support
if ($Args -contains '--help' -or $Args -contains '-h' -or $Args -contains '-?') {
    @”
Usage: run.ps1 [options]

Local development launcher for AI Real Estate Assistant.
Runs both backend and frontend services locally.

Options:
  --help, -h, -?    Show this help message
  --dry-run         Show commands without executing
  --no-bootstrap    Skip dependency installation
  --backend-port    Backend port (default: 8000)
  --frontend-port   Frontend port (default: 3000)

Examples:
  .\scripts\local\run.ps1                        # Start both services
  .\scripts\local\run.ps1 --no-bootstrap         # Skip bootstrap
  .\scripts\local\run.ps1 --backend-port 8080    # Custom backend port
  .\scripts\local\run.ps1 --dry-run              # Show commands

For full options, run: python scripts/start.py --help
“@
    exit 0
}

$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $root

. (Join-Path $root "scripts\shared\resolve_python.ps1")

$invocation = Get-PythonInvocation -ProjectRoot $root
& $invocation.Python @($invocation.Args) (Join-Path $root "scripts\start.py") --mode local @Args
exit $LASTEXITCODE
