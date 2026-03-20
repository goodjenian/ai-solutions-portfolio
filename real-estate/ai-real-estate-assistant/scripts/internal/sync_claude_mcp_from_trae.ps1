param(
  [string]$TraeMcpPath = (Join-Path $env:APPDATA "Trae\User\mcp.json"),
  [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,
  [switch]$WhatIf
)

$ErrorActionPreference = "Stop"

function Convert-TraeJsonToStrictJson([string]$raw) {
  $raw = $raw -replace ",(\s*[}\]])", '$1'
  return $raw
}

function Convert-CommandSpec([pscustomobject]$server) {
  $cmd = [string]$server.command
  $args = @()

  if ($cmd -eq "npx") {
    $cmd = "cmd"
    $args = @("/c", "npx") + @($server.args)
  } elseif ($cmd -match "\s") {
    $maybeNpxIndex = $cmd.IndexOf("npx")
    if ($maybeNpxIndex -ge 0) {
      $tail = $cmd.Substring($maybeNpxIndex)
      $cmd = "cmd"
      $args = @("/c") + @($tail -split "\s+")
    } else {
      $cmd = "cmd"
      $args = @("/c") + @($server.command -split "\s+")
    }
  } else {
    $args = @($server.args)
  }

  return [pscustomobject]@{
    command = $cmd
    args = $args
  }
}

function Sanitize-Env([hashtable]$envTable) {
  $result = [ordered]@{}

  foreach ($k in $envTable.Keys) {
    $v = $envTable[$k]
    if ($k -eq "MEMORY_FILE_PATH") {
      $result[$k] = (Join-Path $RepoRoot ".claude\memory.json")
      continue
    }
    if ($k -eq "TASK_MANAGER_FILE_PATH") {
      $result[$k] = '${TASK_MANAGER_FILE_PATH}'
      continue
    }
    if ($k -eq "TM_CONFIG_PATH") {
      $result[$k] = '${TM_CONFIG_PATH}'
      continue
    }
    if ($k -eq "SSH_CONFIG_PATH") {
      $result[$k] = '${USERPROFILE}\.ssh\mcp-db.toml'
      continue
    }
    if ($k -eq "HOME") {
      $result[$k] = '${USERPROFILE}'
      continue
    }

    if ($v -is [string] -and $v.Length -gt 0 -and -not ($v -match "^\$\{.+\}$")) {
      $secretKeys = @(
        "BRAVE_API_KEY",
        "GITHUB_PERSONAL_ACCESS_TOKEN",
        "FIRECRAWL_API_KEY",
        "STRIPE_SECRET_KEY",
        "REF_API_KEY",
        "SEMGREP_APP_TOKEN",
        "TAVILY_API_KEY",
        "EXA_API_KEY",
        "GOOGLE_API_KEY",
        "MISTRAL_API_KEY",
        "GLM_API_KEY"
      )
      if ($secretKeys -contains $k) {
        $result[$k] = '${' + $k + '}'
      } else {
        $result[$k] = $v
      }
    } else {
      $result[$k] = $v
    }
  }

  return $result
}

function Sanitize-Args([string[]]$args, [string]$serverName) {
  $out = New-Object System.Collections.Generic.List[string]
  foreach ($a in $args) {
    $b = $a
    $b = $b -replace "C:/Projects/ai-real-estate-assistant", $RepoRoot.Replace("\", "\\")
    $b = $b -replace "C:\\\\Projects\\\\ai-real-estate-assistant", $RepoRoot.Replace("\", "\\")
    if ($serverName -match "Postgres" -and $b -match "^postgresql://") {
      $b = '${POSTGRES_URL}'
    }
    if ($serverName -eq "Redis" -and $b -match "^redis://") {
      $b = '${REDIS_URL}'
    }
    if ($serverName -eq "Cloudflare" -and $b -eq "<account-id>") {
      $b = '${CLOUDFLARE_ACCOUNT_ID}'
    }
    $out.Add($b)
  }

  if ($serverName -eq "Filesystem") {
    $replaced = New-Object System.Collections.Generic.List[string]
    $hasFsPackage = $false
    foreach ($x in $out) {
      if ($x -eq "@modelcontextprotocol/server-filesystem") { $hasFsPackage = $true }
      $replaced.Add($x)
    }
    if ($hasFsPackage) {
      return @($replaced | Where-Object { $_ -notmatch "^([A-Za-z]:\\\\|[A-Za-z]:/)" }) + @($RepoRoot)
    }
  }

  return $out.ToArray()
}

$strictJson = Convert-TraeJsonToStrictJson (Get-Content -Raw -LiteralPath $TraeMcpPath -Encoding UTF8)
$data = $strictJson | ConvertFrom-Json
$servers = $data.mcpServers

$outServers = [ordered]@{}
foreach ($prop in $servers.PSObject.Properties) {
  $name = $prop.Name
  $server = [pscustomobject]$prop.Value

  $cmdSpec = Convert-CommandSpec $server

  $envTable = @{}
  if ($null -ne $server.env) {
    foreach ($e in $server.env.PSObject.Properties) {
      $envTable[$e.Name] = $e.Value
    }
  }
  $sanitizedEnv = Sanitize-Env $envTable

  $args = @()
  if ($null -ne $cmdSpec.args) { $args = @($cmdSpec.args) }
  $args = Sanitize-Args $args $name

  $outServer = [ordered]@{
    command = $cmdSpec.command
    args = $args
    env = $sanitizedEnv
  }
  if ($null -ne $server.disabled) {
    $outServer["disabled"] = [bool]$server.disabled
  }

  $outServers[$name] = $outServer
}

$out = [ordered]@{ mcpServers = $outServers }
$json = $out | ConvertTo-Json -Depth 20
$outPath = Join-Path $RepoRoot ".mcp.json"

if ($WhatIf) {
  $json
} else {
  Set-Content -LiteralPath $outPath -Value $json -Encoding UTF8
  Write-Output $outPath
}
