$BackendUrl = "http://localhost:8000"
$ApiKey = $env:API_ACCESS_KEY
if (-not $ApiKey -or -not $ApiKey.Trim()) {
    $ApiKey = "dev-secret-key"
}
$Headers = @{
    "X-API-Key" = $ApiKey
    "Content-Type" = "application/json"
}

Write-Host "Checking Health..."
$maxRetries = 10
$retryCount = 0
$healthy = $false

while ($retryCount -lt $maxRetries) {
    try {
        $response = Invoke-RestMethod -Uri "$BackendUrl/health" -Method Get -ErrorAction Stop
        Write-Host "Health Check Passed: $($response.status)"
        $healthy = $true
        break
    } catch {
        Write-Host "Health Check Failed (Attempt $($retryCount + 1)/$maxRetries): $($_.Exception.Message)"
        Start-Sleep -Seconds 5
        $retryCount++
    }
}

if (-not $healthy) {
    Write-Host "Backend did not become healthy."
    exit 1
}

Write-Host "Testing Ollama Runtime Status..."
try {
    $runtimeResponse = Invoke-RestMethod -Uri "$BackendUrl/api/v1/settings/test-runtime?provider=ollama" -Method Get -Headers $Headers -ErrorAction Stop
    Write-Host "Runtime Check Response:"
    Write-Host ($runtimeResponse | ConvertTo-Json -Depth 5)

    if ($runtimeResponse.runtime_available -eq $true) {
        Write-Host "SUCCESS: Ollama is available."
    } else {
        Write-Host "FAILURE: Ollama is NOT available. Error: $($runtimeResponse.runtime_error)"
    }
} catch {
    Write-Host "Runtime Check Failed: $($_.Exception.Message)"
    if ($_.Exception.Response) {
        $stream = $_.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($stream)
        Write-Host "Response Body: $($reader.ReadToEnd())"
    }
    exit 1
}
