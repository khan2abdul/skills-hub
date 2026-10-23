#!/usr/bin/env pwsh
# Vendors a skill under a canonical name WITHOUT touching its body.
#
# Two modes, chosen by the manifest entry:
#   chosen    -> verbatim copy; only the frontmatter `name:` line changes
#   composed  -> the body is assembled from named sections of several upstream
#                skills, each quoted verbatim and attributed. Every quoted block
#                is hash-checked against its source at verify time.
#
#   vendor.ps1 -Skill debug-this-code
#   vendor.ps1 -Skill debug-this-code -From diagnosing-bugs
#   vendor.ps1 -All -WhatIf
param(
  [string]$Skill = "",
  [string]$From = "",
  [switch]$All,
  [switch]$Force,
  [switch]$WhatIf
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '_common.ps1')

$hub = Get-HubRoot
$loaded = Read-Repos (Join-Path $hub 'repos.toml')
$index = Get-SkillIndex $loaded.repos
$manifest = Read-Manifest (Join-Path $hub 'manifest.yml')

$targets = if ($All) { @($manifest) } else { @($manifest | Where-Object { $_.name -eq $Skill }) }
if (-not $targets) { throw "no manifest entry named '$Skill'. Run tools/harvest.ps1 to see valid names." }

$done = 0; $skipped = 0; $errors = @()

foreach ($s in $targets) {
  $canonical = $s.name
  $outDir = Join-Path (Join-Path $hub 'skills') $canonical

  # ---- composed mode ----
  if (@($s.composed).Count -gt 0) {
    $specFile = Join-Path (Join-Path $hub 'compose') "$canonical.yml"
    if (-not (Test-Path $specFile)) { $errors += "$canonical : composed entry has no compose/$canonical.yml"; continue }
    if ((Test-Path $outDir) -and -not $Force) { Write-Host "SKIP  $canonical (exists, use -Force)" -ForegroundColor Yellow; $skipped++; continue }
    $res = & (Join-Path $PSScriptRoot 'compose.ps1') -Name $canonical -WhatIf:$WhatIf -Force:$Force
    if ($LASTEXITCODE -ne 0 -or $res -eq $false) { $errors += "$canonical : compose failed"; continue }
    $done++; continue
  }

  # ---- verbatim mode ----
  $sourceName = if ($From) { $From } else { $s.chosen }
  if (-not $sourceName) { $sourceName = @($s.candidates)[0] }
  if (-not $sourceName) { $errors += "$canonical : no chosen source and no candidates"; continue }
  if (-not $index.ContainsKey($sourceName)) { $errors += "$canonical : upstream '$sourceName' not found on disk"; continue }

  $src = $index[$sourceName]
  $script:srcIndex = $index
  if ((Test-Path $outDir) -and -not $Force) { Write-Host "SKIP  $canonical (exists, use -Force)" -ForegroundColor Yellow; $skipped++; continue }

  $raw = [System.IO.File]::ReadAllText($src.file)
  $m = [regex]::Match($raw, '\A(---\r?\n)(.*?)(\r?\n---\r?\n)', 'Singleline')
  if (-not $m.Success) { $errors += "$canonical : '$sourceName' has no YAML frontmatter"; continue }

  $yaml2 = [regex]::Replace($m.Groups[2].Value, '(?m)^name:\s*.*$', "name: $canonical", 1)
  if ($yaml2 -eq $m.Groups[2].Value -and $m.Groups[2].Value -notmatch '(?m)^name:\s*') {
    $errors += "$canonical : '$sourceName' frontmatter has no name: line"; continue
  }
  $newRaw = $m.Groups[1].Value + $yaml2 + $m.Groups[3].Value + $raw.Substring($m.Length)

  if ($WhatIf) {
    Write-Host ("WOULD {0,-24} <- {1,-32} mode=verbatim name-line-only" -f $canonical, $sourceName) -ForegroundColor Cyan
    $done++; continue
  }

  New-Item -ItemType Directory -Force -Path $outDir | Out-Null
  [System.IO.File]::WriteAllText((Join-Path $outDir 'SKILL.md'), $newRaw, (New-Object System.Text.UTF8Encoding($false)))
  foreach ($item in Get-ChildItem $src.dir -Force -ErrorAction SilentlyContinue) {
    if ($item.Name -eq 'SKILL.md') { continue }
    Copy-Item $item.FullName -Destination (Join-Path $outDir $item.Name) -Recurse -Force -ErrorAction SilentlyContinue
  }

  $srcHash = (Get-FileHash $src.file -Algorithm SHA256).Hash
  $repoRoot = ($loaded.repos | Where-Object { $_.name -eq $src.repo }).path
  $commit = ''
  if ($repoRoot -and (Test-Path (Join-Path $repoRoot '.git'))) { $commit = (& git -C $repoRoot rev-parse HEAD 2>$null) }
  $rel = $src.file.Substring($repoRoot.Length).TrimStart('\','/') -replace '\\','/'

  $prov = @"
# Provenance

- canonical: $canonical
- mode: verbatim
- upstream: $sourceName
- repo: $($src.repo)
- path: $rel
- commit: $commit
- upstream SKILL.md sha256: $srcHash
- body changed: no
- change: frontmatter ``name:`` rewritten from ``$sourceName`` to ``$canonical``; every other byte preserved
- other candidates considered: $(@($s.candidates | Where-Object { $_ -ne $sourceName }) -join ', ')
- vendored: $(Get-Date -Format 'yyyy-MM-dd')
"@
  Set-Content -Path (Join-Path $outDir 'PROVENANCE.md') -Value $prov -Encoding UTF8
  Write-Host "OK    $canonical <- $sourceName ($($src.repo))" -ForegroundColor Green
  $done++
}

Write-Host ""
Write-Host "vendored: $done  skipped: $skipped  errors: $($errors.Count)"
if ($errors) { $errors | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }; exit 1 }
Write-Host "Now run tools/verify.ps1 to re-prove every body." -ForegroundColor Cyan
