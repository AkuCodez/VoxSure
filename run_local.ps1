# Start VoxSure locally: .\run_local.ps1   (then open http://localhost:8000)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

# stop any older copy already using port 8000
Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue |
  ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }

# keep model downloads on D: (C: is nearly full on this machine)
$env:HF_HOME = Join-Path $root ".hf_cache"
$env:TMP = Join-Path $root ".tmp"; $env:TEMP = $env:TMP
New-Item -ItemType Directory -Force $env:TMP | Out-Null

if (-not (Test-Path (Join-Path $root "frontend\dist\index.html"))) {
  Write-Host "Building the frontend first..."; Push-Location (Join-Path $root "frontend"); npm install; npm run build; Pop-Location
}
if (-not (Test-Path (Join-Path $root ".env"))) { Write-Host "Note: no .env file, so AI answers for non-campus questions are OFF (copy .env.example to .env and add a key)." }

Push-Location (Join-Path $root "backend")
Write-Host "Starting on http://localhost:8000 (first start loads models, give it about a minute)..."
& (Join-Path $root ".venv\Scripts\python.exe") -m uvicorn app.main:app --port 8000
