# Weekly publish: copy the rebuilt dashboard, then re-apply SEO so the head is never wiped.
# Usage (from repo root):
#   .\tools\publish.ps1 -WeekDir "C:\Users\Nikola\Desktop\CyberpunkTCG\WTNC\WTNC_w2_2026-11-21"
# Or pass the dashboard file directly:
#   .\tools\publish.ps1 -Dashboard "C:\Users\Nikola\Desktop\CyberpunkTCG\WTNC\...\cumulative\dashboard.html"

# No [CmdletBinding()]: PS 5.1 AmbiguousParameterSet on week folders whose
# names end in a date (WTNC_w2_2026-11-21) when advanced param binding is on.
param(
    [string]$WeekDir,
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

# -LiteralPath + -Parent AmbiguousParameterSet on dated week paths in PS 5.1.
$CumDir = Split-Path -Path $Dashboard -Parent
Write-Host "Copying dashboard -> index.html"
Copy-Item -LiteralPath $Dashboard -Destination (Join-Path $RepoRoot "index.html") -Force

# Multi-file live site: shell + assets/ + data/ + panels/ beside index.html.
foreach ($name in @("assets", "data", "panels")) {
    $src = Join-Path $CumDir $name
    $dst = Join-Path $RepoRoot $name
    if (Test-Path -LiteralPath $dst) {
        Remove-Item -LiteralPath $dst -Recurse -Force
    }
    if (Test-Path -LiteralPath $src) {
        Write-Host "Copying $name/"
        Copy-Item -LiteralPath $src -Destination $dst -Recurse -Force
    }
}

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

git add -- index.html robots.txt sitemap.xml assets data panels
$status = git status --porcelain -- index.html robots.txt sitemap.xml assets data panels
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
