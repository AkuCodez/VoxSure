# Interactive helper: .\setup_ai.ps1
# Asks which AI provider you use and writes the settings into .env (the key is typed hidden and never printed).
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$envPath = Join-Path $root ".env"

Write-Host ""
Write-Host "Which AI provider do you want for non-campus questions?"
Write-Host "  1) Groq            (console.groq.com -> API Keys)"
Write-Host "  2) Google Gemini   (aistudio.google.com -> Get API key)"
Write-Host "  3) Claude          (console.anthropic.com -> API Keys; paid)"
$choice = Read-Host "Type 1, 2 or 3"
if ($choice -notin "1","2","3") { Write-Host "Please run again and type 1, 2 or 3."; exit 1 }

$secure = Read-Host "Paste your API key and press Enter (it stays hidden)" -AsSecureString
$key = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure))
if ([string]::IsNullOrWhiteSpace($key)) { Write-Host "No key entered. Nothing was changed."; exit 1 }
$key = $key.Trim()

$new = [ordered]@{}
if ($choice -eq "3") {
  $new["ANTHROPIC_API_KEY"] = $key
} else {
  if ($choice -eq "1") { $base = "https://api.groq.com/openai/v1"; $name = "Groq";          $hint = "a model name from Groq's current model list" }
  else                 { $base = "https://generativelanguage.googleapis.com/v1beta/openai/"; $name = "Google Gemini"; $hint = "a model name from Google's current Gemini model list" }
  $model = Read-Host "Model name (copy $hint)"
  if ([string]::IsNullOrWhiteSpace($model)) { Write-Host "No model entered. Nothing was changed."; exit 1 }
  $new["GENERAL_PROVIDER"] = "openai_compat"; $new["GENERAL_API_KEY"] = $key; $new["GENERAL_BASE_URL"] = $base
  $new["GENERAL_MODEL"] = $model.Trim(); $new["GENERAL_PROVIDER_NAME"] = $name
}

# keep every other line of an existing .env; replace only the AI settings
$managed = "ANTHROPIC_API_KEY","GENERAL_PROVIDER","GENERAL_API_KEY","GENERAL_BASE_URL","GENERAL_MODEL","GENERAL_PROVIDER_NAME"
$lines = @()
if (Test-Path $envPath) { $lines = Get-Content $envPath | Where-Object { $l = $_; -not ($managed | Where-Object { $l -match "^\s*#?\s*$_\s*=" }) } }
$lines += ($new.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" })
[IO.File]::WriteAllLines($envPath, $lines, (New-Object Text.UTF8Encoding($false)))

Write-Host ""
Write-Host "Saved to $envPath (this file is git-ignored; never share it)."
Write-Host "Now start the app with:  .\run_local.ps1"
