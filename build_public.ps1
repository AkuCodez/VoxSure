# Rebuild the website into public/ (the folder Vercel serves). Run after any frontend change, then commit public/.
#   .\build_public.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location (Join-Path $root "frontend")
try {
  if (-not (Test-Path "node_modules")) { npm ci }
  npm run build
  if ($LASTEXITCODE -ne 0) { throw "Frontend build failed." }
}
finally { Pop-Location }
$pub = Join-Path $root "public"
if (Test-Path $pub) { Remove-Item $pub -Recurse -Force }
New-Item -ItemType Directory -Force $pub | Out-Null
Copy-Item (Join-Path $root "frontend\dist\*") $pub -Recurse -Force
Write-Host ("public/ updated: " + (Get-ChildItem $pub -Recurse -File | Measure-Object).Count + " files")
