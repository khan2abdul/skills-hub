# Shared path resolution. Dot-source this; do not hardcode paths anywhere else.
#
# Resolution order for the sources root:
#   1. $env:SKILLS_HUB_SOURCES            (explicit override, wins)
#   2. sources_root in repos.toml         (relative to the hub, or absolute)
#   3. <hub>/../setupskills               (default sibling layout)
#
# A repo's `path` may be absolute or relative to the resolved sources root.

function Get-HubRoot {
  Split-Path $PSScriptRoot -Parent
}

function Read-Repos([string]$file, [switch]$Strict) {
  $repos = @(); $cur = $null; $sourcesRoot = $null
  foreach ($line in Get-Content $file) {
    $t = $line.Trim()
    if ($t -match '^sources_root\s*=\s*"?([^"]*)"?$') { $sourcesRoot = $Matches[1]; continue }
    if ($t -eq '[[repo]]') { if ($cur) { $repos += $cur }; $cur = @{} }
    elseif ($cur -and $t -match '^(\w+)\s*=\s*(.+)$') {
      $k = $Matches[1]; $v = $Matches[2].Trim()
      if ($v -match '^\[(.*)\]$') {
        $v = @($Matches[1] -split ',' | ForEach-Object { $_.Trim().Trim('"') } | Where-Object { $_ })
      } else { $v = $v.Trim('"') }
      $cur[$k] = $v
    }
  }
  if ($cur) { $repos += $cur }

  $root = Resolve-SourcesRoot -Declared $sourcesRoot -Strict:$Strict
  foreach ($r in $repos) {
    if ($r.path -and -not [System.IO.Path]::IsPathRooted($r.path)) {
      $r.path = [System.IO.Path]::GetFullPath((Join-Path $root $r.path))
    }
  }
  @{ repos = $repos; sourcesRoot = $root }
}

function Resolve-SourcesRoot([string]$Declared, [switch]$Strict) {
  $hub = Get-HubRoot
  if ($env:SKILLS_HUB_SOURCES) { return [System.IO.Path]::GetFullPath($env:SKILLS_HUB_SOURCES) }
  $declaredPath = $null
  if ($Declared) {
    $declaredPath = if ([System.IO.Path]::IsPathRooted($Declared)) { $Declared } else { Join-Path $hub $Declared }
    $declaredPath = [System.IO.Path]::GetFullPath($declaredPath)
    # a declared root that exists always wins
    if (Test-Path $declaredPath) { return $declaredPath }
  }
  # -Strict is for tools that WRITE to the declared location (clone-repos). Falling
  # back to a discovered folder there would clone into the wrong tree, so never guess.
  if ($Strict -and $declaredPath) { return $declaredPath }
  # discovery: walk up looking for a sibling directory that actually holds repos.
  # A path that merely exists but is empty must not win, or a stray empty folder
  # up the tree would silently hide every real source.
  $d = Get-Item $hub
  while ($d) {
    foreach ($cand in @('setupskills', 'skills-sources')) {
      $p = Join-Path $d.FullName $cand
      if ((Test-Path $p) -and (Get-ChildItem $p -Directory -ErrorAction SilentlyContinue)) { return $p }
    }
    $d = $d.Parent
  }
  # last resort: the declared value even if missing, so the error message is useful
  if ($Declared) {
    $p = if ([System.IO.Path]::IsPathRooted($Declared)) { $Declared } else { Join-Path $hub $Declared }
    return [System.IO.Path]::GetFullPath($p)
  }
  return [System.IO.Path]::GetFullPath((Join-Path $hub '..' 'setupskills'))
}

function Read-Manifest([string]$file) {
  $skills = @(); $cur = $null
  foreach ($line in Get-Content $file) {
    $t = $line.Trim()
    if ($t -eq '[[skill]]') { if ($cur) { $skills += $cur }; $cur = @{ candidates = @(); composed = @() } }
    elseif ($cur) {
      if ($t -match '^name\s*=\s*"(.+)"')        { $cur.name = $Matches[1] }
      elseif ($t -match '^status\s*=\s*"(.+)"')  { $cur.status = $Matches[1] }
      elseif ($t -match '^chosen\s*=\s*"?(.*?)"?$') { $cur.chosen = $Matches[1] }
      elseif ($t -match '^candidates\s*=\s*\[(.*)\]') {
        $cur.candidates = @($Matches[1] -split ',' | ForEach-Object { $_.Trim().Trim('"') } | Where-Object { $_ })
      }
      elseif ($t -match '^composed\s*=\s*\[(.*)\]') {
        $cur.composed = @($Matches[1] -split ',' | ForEach-Object { $_.Trim().Trim('"') } | Where-Object { $_ })
      }
    }
  }
  if ($cur) { $skills += $cur }
  $skills
}

# Which upstream skills are ACTUALLY shipped, read from skills/*/PROVENANCE.md.
# The manifest's `candidates` are proposals: a skill listed as a losing candidate
# was never shipped, so counting it as "claimed" hides real gaps. Provenance is
# the only claim that is backed by a file on disk.
function Get-ShippedSources {
  $skillsDir = Join-Path (Get-HubRoot) 'skills'
  $map = @{}
  if (-not (Test-Path $skillsDir)) { return $map }
  foreach ($d in Get-ChildItem $skillsDir -Directory -ErrorAction SilentlyContinue) {
    $prov = Join-Path $d.FullName 'PROVENANCE.md'
    if (-not (Test-Path $prov)) { continue }
    $txt = Get-Content $prov -Raw
    $names = @()
    if ($txt -match '(?m)^- mode:\s*composed') {
      # the "sources:" line names REPOS; the excerpt table names the skills
      $names = @([regex]::Matches($txt, '(?m)^\|\s*([^|]+?)\s*\|[^|]*\|\s*[0-9a-f]{64}\s*\|') |
        ForEach-Object { $_.Groups[1].Value.Trim() } | Where-Object { $_ })
    } else {
      $u = ([regex]::Match($txt, '(?m)^- upstream:\s*(.+?)\s*$')).Groups[1].Value
      if ($u) { $names = @($u) }
    }
    foreach ($n in $names) { if (-not $map.ContainsKey($n)) { $map[$n] = $d.Name } }
  }
  $map
}

# One record per upstream skill: shipped, ignored, or dropped with no decision.
function Get-SkillCoverage {
  $hub = Get-HubRoot
  $loaded = Read-Repos (Join-Path $hub 'repos.toml')
  $index = Get-SkillIndex $loaded.repos
  $manifest = Read-Manifest (Join-Path $hub 'manifest.yml')
  $shipped = Get-ShippedSources

  $ignored = @{}
  $ignoreFile = Join-Path $hub 'ignore.txt'
  if (Test-Path $ignoreFile) {
    Get-Content $ignoreFile | ForEach-Object {
      $t = $_.Trim()
      if ($t -and -not $t.StartsWith('#')) { $ignored[$t] = $true }
    }
  }

  # canonical name each upstream skill was proposed for (report grouping only)
  $claim = @{}
  foreach ($s in $manifest) {
    foreach ($c in (@($s.candidates) + @($s.composed))) {
      if ($c -and -not $claim.ContainsKey($c)) { $claim[$c] = $s.name }
    }
  }

  $rows = foreach ($n in $index.Keys) {
    $state = if ($shipped.ContainsKey($n)) { 'shipped' }
             elseif ($ignored.ContainsKey($n)) { 'ignored' }
             else { 'dropped' }
    [pscustomobject]@{
      repo      = $index[$n].repo
      skill     = $n
      chars     = (Get-Item $index[$n].file).Length
      state     = $state
      canonical = $shipped[$n]
      claimedBy = $claim[$n]
    }
  }
  @{ rows = @($rows); shipped = $shipped; ignored = $ignored; index = $index; manifest = $manifest }
}

# upstream skill name -> @{ repo; dir; file }
function Get-SkillIndex($Repos) {
  $index = @{}
  foreach ($r in $Repos) {
    if ($r.status -eq 'reference') { continue }
    if (-not $r.path -or -not (Test-Path $r.path)) { continue }
    foreach ($root in $r.roots) {
      $p = if ($root -eq '.') { $r.path } else { Join-Path $r.path $root }
      if (-not (Test-Path $p)) { continue }
      foreach ($d in Get-ChildItem $p -Directory -ErrorAction SilentlyContinue) {
        $f = Join-Path $d.FullName 'SKILL.md'
        if (Test-Path $f) {
          if (-not $index.ContainsKey($d.Name)) { $index[$d.Name] = @{ repo = $r.name; dir = $d.FullName; file = $f } }
        }
      }
    }
  }
  $index
}
