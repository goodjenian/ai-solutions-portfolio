function Get-BestPyVersionArg {
  param(
    [Parameter(Mandatory = $true)]
    [Version]$MinimumVersion
  )

  try {
    $lines = & py -0p 2>$null
  } catch {
    return "-3"
  }

  if (-not $lines) {
    return "-3"
  }

  $best = $null
  foreach ($line in $lines) {
    if ($line -match '^\s*-(\d+\.\d+)(?:-[^\s]+)?\s+') {
      try {
        $v = [Version]$Matches[1]
      } catch {
        continue
      }
      if ($v -ge $MinimumVersion -and ($null -eq $best -or $v -gt $best)) {
        $best = $v
      }
    }
  }

  if ($null -ne $best) {
    return "-$($best.Major).$($best.Minor)"
  }

  return "-3"
}

function Get-PythonInvocation {
  param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectRoot
  )

  $venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
  if (Test-Path $venvPython) {
    return @{
      Python = $venvPython
      Args   = @()
    }
  }

  if (Get-Command py -ErrorAction SilentlyContinue) {
    $versionArg = Get-BestPyVersionArg -MinimumVersion ([Version]"3.11")
    return @{
      Python = "py"
      Args   = @($versionArg)
    }
  }

  if (Get-Command python -ErrorAction SilentlyContinue) {
    return @{
      Python = "python"
      Args   = @()
    }
  }

  throw "Python executable not found. Install Python 3.11+ or run scripts\setup\setup.ps1."
}
