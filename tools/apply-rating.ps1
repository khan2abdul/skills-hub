#!/usr/bin/env pwsh
# Reads RATING.json and applies the fixes it can apply without editing a skill
# body. The hub's core guarantee is that skill text is immutable, so this tool
# deliberately cannot touch SKILL.md: every fix here copies or deletes files
# AROUND the body, and re-runs verify.ps1 to prove nothing drifted.
#
#   apply-rating.ps1              -> show what would change
#   apply-rating.ps1 -Apply       -> do it, then verify
#   apply-rating.ps1 -Apply -Only debug-this-code
#
# Unapplied findings (VENDOR-HELPER, BIGGER-CANDIDATE, SLASH-ONLY, EMPTY-BODY)
# need a decision, not a script: they are printed as TODO.
param(
  [switch]$Apply,
  [string]$Only = ""
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '_common.ps1')

$hub = Get-HubRoot
$ratingFile = Join-Path $hub 'RATING.json'
if (-not (Test-Path $ratingFile)) {
  Write-Host "no RATING.json - run tools/rate-skills.ps1 first" -ForegroundColor Red
  exit 2
}
$rating = Get-Content $ratingFile -Raw | ConvertFrom-Json

# Guard: a stale report must not be applied to a skill set that has changed.
$skillsNow = @(Get-ChildItem (Join-Path $hub 'skills') -Directory |
  Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') }).Count
if ($rating.summary.count -ne $skillsNow) {
  Write-Host "RATING.json is stale: it rated $($rating.summary.count) skills, $skillsNow exist." -ForegroundColor Red
  Write-Host "Re-run tools/rate-skills.ps1." -ForegroundColor Yellow
  exit 1
}

$fixes = @($rating.skills | ForEach-Object { $_.fixes } | Where-Object { $_ })
if ($Only) { $fixes = @($fixes | Where-Object { $_.skill -eq $Only }) }

$todos = @($rating.plan | Where-Object { -not $_.auto })
if ($Only) { $todos = @($todos | Where-Object { $_.skill -eq $Only }) }

Write-Host "=== apply-rating ===" -ForegroundColor Cyan
Write-Host "rated   : $($rating.generated)  rubric v$($rating.rubric_version)  mean $($rating.summary.mean)"
Write-Host "apply   : $($fixes.Count) automatic, $($todos.Count) need a decision"
Write-Host ""

if (-not $fixes) {
  Write-Host "nothing to apply automatically." -ForegroundColor Green
} else {
  $done = 0; $skipped = 0; $errors = @()
  foreach ($f in $fixes) {
    $src = Join-Path $hub $f.source
    $dst = Join-Path (Join-Path $hub 'skills') $f.target
    if (-not (Test-Path $src)) {
      $errors += "$($f.skill): source missing $($f.source)"
      continue
    }
    if ((Test-Path $dst) -and -not $Apply) {
      Write-Host ("SKIP  {0,-24} {1} (exists)" -f $f.skill, $f.ref) -ForegroundColor Yellow
      $skipped++
      continue
    }
    if (-not $Apply) {
      Write-Host ("WOULD {0,-24} copy {1} -> {2}" -f $f.skill, $f.source, $f.target) -ForegroundColor Cyan
      $done++
      continue
    }
    # payload only: refuse to overwrite a SKILL.md even if the JSON asks
    if ((Split-Path $dst -Leaf) -eq 'SKILL.md') {
      $errors += "$($f.skill): refusing to overwrite SKILL.md (bodies are immutable)"
      continue
    }
    New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent) | Out-Null
    Copy-Item $src $dst -Force
    Write-Host ("OK    {0,-24} {1}" -f $f.skill, $f.ref) -ForegroundColor Green
    $done++
  }

  Write-Host ""
  Write-Host "applied: $done  skipped: $skipped  errors: $($errors.Count)"
  if ($errors) { $errors | ForEach-Object { Write-Host "  $_" -ForegroundColor Red } }
  if ($errors) { exit 1 }
}

if ($todos.Count) {
  Write-Host ""
  Write-Host "=== needs a decision (not auto-applied) ===" -ForegroundColor Yellow
  $todos | Group-Object finding | Sort-Object Name | ForEach-Object {
    Write-Host ""
    Write-Host "$($_.Name) ($($_.Count))" -ForegroundColor Yellow
    foreach ($t in $_.Group) {
      Write-Host "  $($t.skill): $($t.message)"
      if ($t.command) { Write-Host "    -> $($t.command)" -ForegroundColor DarkGray }
    }
  }
}

if ($Apply) {
  Write-Host ""
  Write-Host "--- verify ---" -ForegroundColor Cyan
  $global:LASTEXITCODE = 0
  & (Join-Path $PSScriptRoot 'verify.ps1')
  if ($LASTEXITCODE -ne 0) {
    Write-Host "verify failed after applying - the fix changed something it should not have" -ForegroundColor Red
    exit 1
  }
  Write-Host ""
  Write-Host "re-run tools/rate-skills.ps1 to see the new scores." -ForegroundColor Cyan
}
exit 0
