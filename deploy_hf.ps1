# Deploy to a Hugging Face Space (Docker):   .\deploy_hf.ps1 -Space yourname/voxsure
# Dry run (builds the snapshot, uploads nothing):   .\deploy_hf.ps1 -Space yourname/voxsure -DryRun
#
# Why a snapshot: Hugging Face requires binary files (model weights, images) to be stored with Git LFS. The snapshot is a fresh,
# single-commit copy of the tracked files with the right LFS rules, so your project history is untouched and nothing old is uploaded.
param(
  [Parameter(Mandatory = $true)][string]$Space,
  [switch]$DryRun
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

if ($Space -notmatch "^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$") { throw "Space must look like  yourname/spacename" }
git --version | Out-Null
git lfs version | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Git LFS is not installed. Install it from https://git-lfs.com and run:  git lfs install" }
if (-not (Test-Path "ml\artifacts\intent_model\model.safetensors")) { throw "ml\artifacts\intent_model\model.safetensors is missing (train the model first)." }
if ((Get-Item "ml\artifacts\intent_model\model.safetensors").Length -lt 100MB) { throw "model.safetensors looks like an LFS pointer, not the real weights. Run: git lfs pull" }

# secrets must never be uploaded
$tracked = git ls-files
if ($tracked -match "(^|/)\.env$") { throw ".env is tracked by git. Remove it from git before deploying." }

$stage = Join-Path $root ".tmp\hf_stage"
if (Test-Path $stage) { Remove-Item $stage -Recurse -Force }
New-Item -ItemType Directory -Force $stage | Out-Null
foreach ($f in $tracked) {
  if ($f -eq ".gitattributes") { continue }
  $dest = Join-Path $stage $f
  New-Item -ItemType Directory -Force (Split-Path -Parent $dest) | Out-Null
  Copy-Item -LiteralPath (Join-Path $root $f) -Destination $dest -Force
}

Push-Location $stage
try {
  $ErrorActionPreference = "Continue"   # git writes progress/warnings to stderr; failures are checked via exit codes below
  git init -q -b main
  git config core.autocrlf false        # keep files byte-for-byte (Linux build)
  git config core.safecrlf false
  @(
    "*.safetensors filter=lfs diff=lfs merge=lfs -text",
    "*.png filter=lfs diff=lfs merge=lfs -text",
    "*.jpg filter=lfs diff=lfs merge=lfs -text",
    "*.jpeg filter=lfs diff=lfs merge=lfs -text",
    "*.bin filter=lfs diff=lfs merge=lfs -text",
    "*.wav filter=lfs diff=lfs merge=lfs -text"
  ) | Set-Content -Encoding ascii .gitattributes
  git lfs install --local | Out-Null
  git add -A 2>$null
  git -c user.name="VoxSure" -c user.email="deploy@voxsure.local" commit -q -m "VoxSure deployment snapshot" 2>$null
  if ($LASTEXITCODE -ne 0) { throw "Could not create the snapshot commit." }
  Write-Host ""
  Write-Host "Snapshot ready in $stage"
  Write-Host ("Files: " + (git ls-files | Measure-Object).Count)
  Write-Host "Stored with Git LFS:"
  git lfs ls-files
  if ($DryRun) { Write-Host ""; Write-Host "Dry run: nothing was uploaded."; return }

  Write-Host ""
  Write-Host "This will UPLOAD the snapshot to https://huggingface.co/spaces/$Space (replacing the Space's current files) and start a build."
  Write-Host "When Git asks for credentials: username = your Hugging Face username, password = a token with WRITE access (never paste it into chat)."
  $answer = Read-Host "Type YES to continue"
  if ($answer -ne "YES") { Write-Host "Cancelled. Nothing was uploaded."; return }
  git remote add space "https://huggingface.co/spaces/$Space"
  git push --force space main
  if ($LASTEXITCODE -ne 0) { throw "Upload failed (check the Space name and that your token has WRITE access)." }
  Write-Host ""
  Write-Host "Uploaded. Watch the build at: https://huggingface.co/spaces/$Space  (first build takes a long while)."
  Write-Host "Live URL when running: https://$($Space.Replace('/', '-').ToLower()).hf.space"
}
finally { Pop-Location }
