#!/usr/bin/env pwsh
# Clones every status="cloned" repo from repos.toml into the hub's own repos/.
# Makes the hub self-contained: no dependency on an external sources folder.
#
#   clone-repos.ps1              -> clone anything missing, report what exists
#   clone-repos.ps1 -Update      -> fetch and report drift (changes nothing)
#   clone-repos.ps1 -Update -Force -> fetch and hard-reset to upstream HEAD
#   clone-repos.ps1 -Full        -> full history instead of --depth 1
#
# Shallow by default: the hub only needs current file contents to vendor from,
# and gstack alone is ~1.5 GB with history and node_modules.
param(
  [switch]$Update,
  [switch]$Force,
  [switch]$Full,
  [switch]$WhatIf
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '_common.ps1')

$hub = Get-HubRoot
$loaded = Read-Repos (Join-Path $hub 'repos.toml') -Strict
$reposDir = Join-Path $hub 'repos'

Write-Host "hub         : $hub"
Write-Host "repos dir   : $reposDir"
Write-Host ""

if (-not $WhatIf) { New-Item -ItemType Directory -Force -Path $reposDir | Out-Null }

$rows = @()
foreach ($r in $loaded.repos) {
  if ($r.status -ne 'cloned') { continue }
  if (-not $r.url) { Write-Warning "no url for $($r.name), skipping"; continue }

  $dest = $r.path
  $isGit = Test-Path (Join-Path $dest '.git')

  if (-not $isGit) {
    if ($WhatIf) { Write-Host ("WOULD clone {0,-24} {1}" -f $r.name, $r.url) -ForegroundColor Cyan; continue }
    Write-Host ("cloning {0,-24} ..." -f $r.name) -ForegroundColor Cyan
    $args = @('clone','--single-branch','--quiet')
    if (-not $Full) { $args += @('--depth','1') }
    $args += @($r.url, $dest)
    # git writes progress to stderr; verify on disk instead of trusting $LASTEXITCODE
    & git @args 2>&1 | Out-String | Write-Verbose
    if (-not (Test-Path (Join-Path $dest '.git'))) {
      Write-Host ("FAILED  {0}" -f $r.name) -ForegroundColor Red
      $rows += [pscustomobject]@{ repo = $r.name; state = 'FAILED'; commit = ''; skills = 0; mb = 0 }
      continue
    }
  } elseif ($Update) {
    & git -C $dest fetch --quiet origin 2>&1 | Out-String | Write-Verbose
    $head = (& git -C $dest rev-parse HEAD 2>$null)
    $remote = (& git -C $dest rev-parse 'origin/HEAD' 2>$null)
    if (-not $remote) { $remote = (& git -C $dest rev-parse 'origin/HEAD^{commit}' 2>$null) }
    $drift = ($head -ne $remote)
    if ($drift -and $Force) {
      & git -C $dest reset --hard --quiet $remote 2>&1 | Out-String | Write-Verbose
      Write-Host ("updated {0,-24} {1} -> {2}" -f $r.name, $head.Substring(0,7), $remote.Substring(0,7)) -ForegroundColor Green
    } elseif ($drift) {
      Write-Host ("DRIFT   {0,-24} local {1}, upstream {2} (use -Force to reset)" -f `
        $r.name, $head.Substring(0,7), $remote.Substring(0,7)) -ForegroundColor Yellow
    }
  }

  $commit = ''
  if (Test-Path (Join-Path $dest '.git')) { $commit = (& git -C $dest rev-parse --short HEAD 2>$null) }

  # count skill bundles this repo contributes through its declared roots
  $count = 0
  foreach ($root in $r.roots) {
    $p = if ($root -eq '.') { $dest } else { Join-Path $dest $root }
    if (-not (Test-Path $p)) { continue }
    $count += @(Get-ChildItem $p -Directory -ErrorAction SilentlyContinue |
      Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') }).Count
  }
  $size = 0
  if (Test-Path $dest) {
    $size = (Get-ChildItem $dest -Recurse -File -Force -ErrorAction SilentlyContinue |
      Measure-Object Length -Sum).Sum
  }
  $rows += [pscustomobject]@{
    repo   = $r.name
    state  = if ($WhatIf) { 'would-clone' } else { 'ok' }
    commit = $commit
    skills = $count
    mb     = [math]::Round($size / 1MB, 1)
  }
}

Write-Host ""
foreach ($r in ($rows | Sort-Object repo)) {
  Write-Host ("{0,-24} {1,-10} {2,-9} {3,3} skills {4,7} MB" -f `
    $r.repo, $r.state, $r.commit, $r.skills, $r.mb)
}
$total = ($rows | Measure-Object skills -Sum).Sum
$bytes = ($rows | Measure-Object mb -Sum).Sum
Write-Host ("repos: {0}   skill bundles: {1}   size: {2} MB" -f $rows.Count, $total, [math]::Round($bytes,1))
Write-Host "Next: pwsh tools/harvest.ps1" -ForegroundColor Cyan
