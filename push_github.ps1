# Pushes VoxSure to GitHub. Run from D:\VoxSure:   .\push_github.ps1
# Before running: create an EMPTY repo at https://github.com/new (name: voxsure, no README, no .gitignore, no license).
param([string]$Owner = "AkuCodez", [string]$Repo = "voxsure")
$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot

$url = "https://github.com/$Owner/$Repo.git"
git lfs install | Out-Null
if (git remote | Select-String -SimpleMatch "origin") { git remote set-url origin $url } else { git remote add origin $url }
git branch -M main

Write-Host "Pushing to $url (a browser window may ask you to sign in to GitHub)..."
git push -u origin main
if ($LASTEXITCODE -ne 0) { Write-Host "Push failed. Check that the repo exists and is empty, and that you signed in as $Owner." -ForegroundColor Red; exit 1 }

Write-Host "Done: https://github.com/$Owner/$Repo" -ForegroundColor Green
Write-Host "Next: .\set_links.ps1 -Repo https://github.com/$Owner/$Repo"
