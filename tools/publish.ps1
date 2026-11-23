# Weekly publish: copy the rebuilt dashboard, then re-apply SEO so the head is never wiped.
# Usage (from repo root):
#   .\tools\publish.ps1 -WeekDir "C:\Users\Nikola\Desktop\CyberpunkTCG\WTNC\WTNC_w2_2026-11-21"
# Or pass the dashboard file directly:
#   .\tools\publish.ps1 -Dashboard "C:\Users\Nikola\Desktop\CyberpunkTCG\WTNC\...\cumulative\dashboard.html"

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$WeekDir,

    [Parameter(Mandatory = $false)]
    [string]$Dashboard,

    [switch]$SkipCommit,
    [switch]$SkipPush
)

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

if (-not $Dashboard) {
    if (-not $WeekDir) {
        throw "Pass -WeekDir (WTNC week folder) or -Dashboard (path to dashboard.html)."
    }
    $Dashboard = Join-Path $WeekDir "world_meta\cumulative\dashboard.html"
}

if (-not (Test-Path -LiteralPath $Dashboard)) {
    throw "Dashboard not found: $Dashboard"
}

Write-Host "Copying dashboard -> index.html"
Copy-Item -LiteralPath $Dashboard -Destination (Join-Path $RepoRoot "index.html") -Force

$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command python3 -ErrorAction SilentlyContinue }
if (-not $py) { throw "python/python3 not found on PATH (needed for tools/ensure_seo.py)." }

Write-Host "Ensuring SEO head / H1 / overall title"
& $py.Source (Join-Path $RepoRoot "tools\ensure_seo.py")
if ($LASTEXITCODE -ne 0) { throw "ensure_seo.py failed with exit $LASTEXITCODE" }

if ($SkipCommit) {
    Write-Host "Done (copy + SEO). Skipped commit."
    exit 0
}

git add -- index.html robots.txt sitemap.xml
$status = git status --porcelain -- index.html robots.txt sitemap.xml
if (-not $status) {
    Write-Host "No file changes to commit."
    exit 0
}

git commit -m "Update world dashboard (SEO preserved)"
if ($SkipPush) {
    Write-Host "Committed. Skipped push."
    exit 0
}

git push
Write-Host "Pushed. Live: https://nikiva-dev.github.io/night-city-meta/"
