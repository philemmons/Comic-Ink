param(
  [int]$BatchSize = 50,
  [string]$InputCsv,
  [string]$OutputCsv,
  [string]$WorkDir
)

$PythonConRoot = $PSScriptRoot

if (-not $InputCsv) {
  $InputCsv = Join-Path $PythonConRoot "input.csv"
}

if (-not $OutputCsv) {
  $OutputCsv = Join-Path $PythonConRoot "output.csv"
}

if (-not $WorkDir) {
  $WorkDir = Join-Path $PythonConRoot ".convention_crawler"
}

$env:PYTHONPATH = $PythonConRoot
$lines = (Get-Content $InputCsv | Measure-Object -Line).Lines
$total = [Math]::Max($lines - 1, 0)

for ($offset = 0; $offset -lt $total; $offset += $BatchSize) {
  Write-Host "Processing batch offset=$offset size=$BatchSize"
  python -m convention_enricher.enrich $InputCsv `
    --output $OutputCsv `
    --work-dir $WorkDir `
    --offset $offset `
    --limit $BatchSize `
    --search-results-per-provider 8 `
    --max-search-seconds 12 `
    --network-failure-threshold 3 `
    --progress-every 10

  if ($LASTEXITCODE -ne 0) {
    throw "Batch failed at offset $offset"
  }
}

Write-Host "Done. Output: $OutputCsv"
