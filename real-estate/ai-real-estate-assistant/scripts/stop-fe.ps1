<#
.SYNOPSIS
    Stop frontend (Next.js on :3000).
#>

$ErrorActionPreference = "Stop"

# Kill node processes on port 3000
$processes = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($processes) {
    foreach ($pid in $processes) {
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        Write-Host "Stopped process $pid on port 3000"
    }
    Write-Host "Frontend stopped."
} else {
    Write-Host "No process found on port 3000."
}
