<#
.SYNOPSIS
    Stop backend (uvicorn on :8000).
#>

$ErrorActionPreference = "Stop"

# Kill uvicorn processes on port 8000
$processes = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($processes) {
    foreach ($pid in $processes) {
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        Write-Host "Stopped process $pid on port 8000"
    }
    Write-Host "Backend stopped."
} else {
    Write-Host "No process found on port 8000."
}
