#!/usr/bin/env pwsh
# Reports what the source repos contain versus what the manifest claims.
# Read-only. Never writes skills/ and never edits manifest.yml.
#   harvest.ps1              -> drift report + unclaimed candidates
#   harvest.ps1 -NewRepo X   -> also list skills from repo X not yet in the manifest
param(
  [string]$NewRepo = ""
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '_common.ps1')

$hub = Get-HubRoot
$loaded = Read-Repos (Join-Path $hub 'repos.toml')
$repos = $loaded.repos
$manifest = Read-Manifest (Join-Path $hub 'manifest.yml')

Write-Host "sources root   : $($loaded.sourcesRoot)"

if (-not (Test-Path $loaded.sourcesRoot)) {
  Write-Host ""
  Write-Host "No sources root at that path. The 9 cloned repos are not on this machine." -ForegroundColor Red
  Write-Host "Point at them with either:" -ForegroundColor Yellow
  Write-Host "  -e SKILLS_HUB_SOURCES   (environment variable, wins)" -ForegroundColor Yellow
  Write-Host "  sources_root in repos.toml (relative to the hub, or absolute)" -ForegroundColor Yellow
  Write-Host "Then re-run. Manifest entries are not validated until sources resolve." -ForegroundColor Yellow
  exit 2
}

# --- index every upstream skill actually on disk ---
$onDisk = @{}
$refCount = 0
foreach ($r in $repos) {
  if ($r.status -eq 'reference') { $refCount++; continue }
  if (-not $r.path -or -not (Test-Path $r.path)) { Write-Warning "repo missing: $($r.name) -> $($r.path)"; continue }
  foreach ($root in $r.roots) {
    $p = if ($root -eq '.') { $r.path } else { Join-Path $r.path $root }
    if (-not (Test-Path $p)) { continue }
    foreach ($d in Get-ChildItem $p -Directory -ErrorAction SilentlyContinue) {
      if (Test-Path (Join-Path $d.FullName 'SKILL.md')) {
        if (-not $onDisk.ContainsKey($d.Name)) { $onDisk[$d.Name] = @() }
        if ($onDisk[$d.Name] -notcontains $r.name) { $onDisk[$d.Name] += $r.name }
      }
    }
  }
}

# --- claimed candidate that does not exist upstream = broken manifest ---
$broken = @()
$claimed = @{}
foreach ($s in $manifest) {
  $all = @($s.candidates) + @($s.composed)
  foreach ($c in $all) {
    if (-not $c) { continue }
    $claimed[$c] = $true
    if (-not $onDisk.ContainsKey($c)) { $broken += "$($s.name) -> $c (not found)" }
  }
}

# --- on disk but claimed by nobody = candidate for a new manifest entry ---
# "Claimed" means SHIPPED (proven by skills/<name>/PROVENANCE.md). A skill that
# only appears in a `candidates` list was proposed and then lost; counting it as
# claimed is how 72 upstream skills went missing with harvest reporting zero.
$cov = Get-SkillCoverage
$shipped = $cov.shipped
$ignored = $cov.ignored
$unclaimed = @($onDisk.Keys | Where-Object { -not $shipped.ContainsKey($_) -and -not $ignored.ContainsKey($_) } | Sort-Object)
$suppressed = @($onDisk.Keys | Where-Object { $ignored.ContainsKey($_) }).Count

Write-Host "=== skills-hub harvest ===" -ForegroundColor Cyan
Write-Host "repos          : $(@($repos | Where-Object status -ne 'reference').Count) cloned, $refCount reference"
Write-Host "upstream skills: $($onDisk.Count)"
Write-Host "manifest needs : $($manifest.Count)"
Write-Host "shipped        : $($shipped.Count) upstream skills -> $(@($manifest | Where-Object status -eq 'merged').Count) canonical names"
Write-Host "ignored        : $suppressed (rejected, reason in ignore.txt)"
Write-Host "dropped        : $($unclaimed.Count) (neither shipped nor rejected)"
Write-Host ""

Write-Host "=== BROKEN: manifest cites a skill that is not on disk ($($broken.Count)) ===" -ForegroundColor $(if ($broken) { 'Red' } else { 'Green' })
if ($broken) { $broken | ForEach-Object { Write-Host "  $_" -ForegroundColor Red } }

Write-Host ""
Write-Host "=== DROPPED: on disk, not shipped, not rejected ($($unclaimed.Count), $suppressed ignored) ===" -ForegroundColor $(if ($unclaimed) { 'Yellow' } else { 'Green' })
Write-Host "  give each one a decision: ship it, fold it into a shipped skill, or add it to ignore.txt" -ForegroundColor DarkGray
foreach ($u in $unclaimed) { Write-Host ("  {0,-34} {1}" -f $u, ($onDisk[$u] -join ', ')) -ForegroundColor Yellow }

Write-Host ""
Write-Host "=== MERGED entries whose source is gone ===" -ForegroundColor Cyan
$gone = $manifest | Where-Object { $_.status -eq 'merged' -and $_.chosen -and -not $onDisk.ContainsKey($_.chosen) }
if ($gone) { $gone | ForEach-Object { Write-Host "  $($_.name) <- $($_.chosen) MISSING" -ForegroundColor Red } } else { Write-Host "  none" -ForegroundColor Green }

if ($broken.Count -gt 0) { exit 1 }
