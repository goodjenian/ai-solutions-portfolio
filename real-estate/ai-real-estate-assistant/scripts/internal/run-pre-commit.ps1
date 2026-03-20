param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$Args
)

$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $root

pre-commit run @Args
exit $LASTEXITCODE
