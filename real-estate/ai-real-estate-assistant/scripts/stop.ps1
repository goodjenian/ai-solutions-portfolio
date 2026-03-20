<#
.SYNOPSIS
    Stop all services (backend :8000 + frontend :3000).
#>

$ErrorActionPreference = "Stop"

Write-Host "Stopping all services..."

# Stop backend on :8000
$beProcesses = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($beProcesses) {
    foreach ($pid in $beProcesses) {
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        Write-Host "Stopped backend process $pid"
    }
}

# Stop frontend on :3000
$feProcesses = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($feProcesses) {
    foreach ($pid in $feProcesses) {
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        Write-Host "Stopped frontend process $pid"
    }
}

if (-not $beProcesses -and -not $feProcesses) {
    Write-Host "No running services found."
} else {
    Write-Host "All services stopped."
}
