<#
.SYNOPSIS
    Local frontend-only launcher for AI Real Estate Assistant.
.DESCRIPTION
    Runs only the Next.js frontend locally without Docker.
    All arguments are passed through to the Python launcher.
.PARAMETER Args
    Arguments to pass to the launcher.
.EXAMPLE
    .\scripts\local\frontend.ps1
    .\scripts\local\frontend.ps1 --dry-run
    .\scripts\local\frontend.ps1 --frontend-port 4000
#>
param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$Args
)

$ErrorActionPreference = "Stop"

# Help support
if ($Args -contains '--help' -or $Args -contains '-h' -or $Args -contains '-?') {
    @”
Usage: frontend.ps1 [options]

Local frontend-only launcher for AI Real Estate Assistant.
Runs only the Next.js frontend (port 3000).

Options:
  --help, -h, -?    Show this help message
  --dry-run         Show commands without executing
  --no-bootstrap    Skip dependency installation
  --frontend-port   Frontend port (default: 3000)

Examples:
  .\scripts\local\frontend.ps1                        # Start frontend
  .\scripts\local\frontend.ps1 --no-bootstrap         # Skip bootstrap
  .\scripts\local\frontend.ps1 --frontend-port 4000   # Custom port
  .\scripts\local\frontend.ps1 --dry-run              # Show commands

For full options, run: python scripts/start.py --help
“@
    exit 0
}

$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $root

. (Join-Path $root "scripts\shared\resolve_python.ps1")

$invocation = Get-PythonInvocation -ProjectRoot $root
& $invocation.Python @($invocation.Args) (Join-Path $root "scripts\start.py") --mode local --service frontend @Args
exit $LASTEXITCODE
