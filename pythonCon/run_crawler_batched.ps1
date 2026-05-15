param(
  [int]$BatchSize = 50,
  [string]$InputCsv = "c:\Users\phile\Desktop\Comic-Ink\pythonCon\convention_enricher\input.csv",
  [string]$OutputCsv = "c:\Users\phile\Desktop\Comic-Ink\pythonCon\convention_enricher\output.csv",
  [string]$WorkDir = "c:\Users\phile\Desktop\Comic-Ink\pythonCon\.convention_crawler"
)

$env:PYTHONPATH = "c:\Users\phile\Desktop\Comic-Ink\pythonCon"
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
