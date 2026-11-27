# Weekly publish: thin wrapper around tools/publish.py.
# Prefer --week (short) so dated folder names never hit PowerShell path binding.
#
# From repo root:
#   .\tools\publish.ps1 -Week w2
#   .\tools\publish.ps1 -WeekDir "C:\Users\Nikola\Desktop\CyberpunkTCG\WTNC\WTNC_w2_2026-11-21"
#   .\tools\publish.ps1 -Dashboard "...\cumulative\dashboard.html"
#   .\tools\publish.ps1 -Week w2 -DryRun
#   .\tools\publish.ps1 -SelfTest
#
# Why Python owns the work: PS 5.1 Split-Path -LiteralPath / advanced binding
# throws AmbiguousParameterSet on paths like WTNC_w2_2026-11-21.

param(
    [string]$Week,
    [string]$WeekDir,
    [string]$Dashboard,
    [switch]$DryRun,
    [switch]$SkipCommit,
    [switch]$SkipPush,
    [switch]$SelfTest
)

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command python3 -ErrorAction SilentlyContinue }
if (-not $py) { throw "python/python3 not found on PATH." }

$publishPy = Join-Path $PSScriptRoot "publish.py"
if (-not (Test-Path -Path $publishPy)) {
    throw "Missing $publishPy"
}

# Build argv as a string list — never interpolate dated paths into a raw
# command line where -11-21 can look like switches.
$argv = New-Object System.Collections.Generic.List[string]
if ($SelfTest) { [void]$argv.Add("--self-test") }
if ($DryRun) { [void]$argv.Add("--dry-run") }
if ($SkipCommit) { [void]$argv.Add("--skip-commit") }
if ($SkipPush) { [void]$argv.Add("--skip-push") }
if ($Week) {
    [void]$argv.Add("--week")
    [void]$argv.Add($Week)
}
if ($WeekDir) {
    [void]$argv.Add("--week-dir")
    [void]$argv.Add($WeekDir)
}
if ($Dashboard) {
    [void]$argv.Add("--dashboard")
    [void]$argv.Add($Dashboard)
}

& $py.Source $publishPy @($argv.ToArray())
exit $LASTEXITCODE
