# After deploying, record your links in the README and report:
#   .\set_links.ps1 -Live https://yourname-voxsure.hf.space -Repo https://github.com/you/voxsure
param([string]$Live = "", [string]$Repo = "")
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$file = Join-Path $root "docs\links.json"
$cur = @{ live = ""; repo = "" }
if (Test-Path $file) { $j = Get-Content $file -Raw | ConvertFrom-Json; if ($j.live) { $cur.live = $j.live }; if ($j.repo) { $cur.repo = $j.repo } }
foreach ($u in @($Live, $Repo)) { if ($u -and $u -notmatch "^https://") { throw "Links must start with https://" } }
if ($Live) { $cur.live = $Live }
if ($Repo) { $cur.repo = $Repo }
[IO.File]::WriteAllText($file, ($cur | ConvertTo-Json), (New-Object Text.UTF8Encoding($false)))

$readme = Join-Path $root "README.md"
$t = [IO.File]::ReadAllText($readme)
$t = [regex]::Replace($t, "(?m)^\* Live app:.*$", "* Live app: " + $(if ($cur.live) { $cur.live } else { "_add URL after deployment_" }))
if ($cur.repo -and $t -notmatch "(?m)^\* Source code:") { $t = [regex]::Replace($t, "(?m)^(\* Live app:.*)$", "`$1`n* Source code: $($cur.repo)") }
elseif ($cur.repo) { $t = [regex]::Replace($t, "(?m)^\* Source code:.*$", "* Source code: $($cur.repo)") }
[IO.File]::WriteAllText($readme, $t, (New-Object Text.UTF8Encoding($false)))

$env:PYTHONIOENCODING = "utf-8"
& (Join-Path $root ".venv\Scripts\python.exe") (Join-Path $root "ml\scripts\build_report.py")
Write-Host "Saved. README.md and docs\REPORT.md now show your links. Commit them with:  git add -A; git commit -m 'Add live links'"
