#!/usr/bin/env pwsh
# Proves every vendored skill is an unmodified copy of its upstream.
#
# verbatim entries : rebuild upstream with only the name: line swapped, compare bytes
# composed entries : re-extract each excerpt from its source and compare sha256
#
# Read-only. Exit 1 on any failure.
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '_common.ps1')

$hub = Get-HubRoot
$skillsDir = Join-Path $hub 'skills'
$loaded = Read-Repos (Join-Path $hub 'repos.toml')
$index = Get-SkillIndex $loaded.repos
$manifest = Read-Manifest (Join-Path $hub 'manifest.yml')
$merged = @($manifest | Where-Object { $_.status -eq 'merged' })
$fail = 0

function Get-BodyText([string]$file) {
  $raw = [System.IO.File]::ReadAllText($file)
  $m = [regex]::Match($raw, '\A---\r?\n.*?\r?\n---\r?\n', 'Singleline')
  if ($m.Success) { return $raw.Substring($m.Length) }
  return $raw
}

function Get-Section([string]$body, [string]$heading) {
  $esc = [regex]::Escape($heading)
  $m = [regex]::Match($body, "(?m)^$esc\s*$")
  if (-not $m.Success) { return $null }
  $level = ([regex]::Match($heading, '^(#+)')).Groups[1].Value.Length
  $start = $m.Index
  $after = $start + $m.Length
  # Next heading of the same or a higher level, ignoring anything inside a fenced
  # block. Keep this identical to compose.ps1: they must extract the same bytes or
  # verify reports drift on sections compose extracted correctly.
  # Track offsets through the split separators. The old `+ 1` assumed LF and
  # drifted one char per line on CRLF sources, silently cutting the tail of a
  # section. Keep this identical to compose.ps1.
  $parts = [regex]::Split($body.Substring($after), '(\r?\n)')
  $pos = $after
  $inFence = $false
  for ($i = 0; $i -lt $parts.Count; $i += 2) {
    $line = $parts[$i]
    if ($line -match '^\s*(```|~~~)') { $inFence = -not $inFence }
    elseif (-not $inFence -and $line -match ('^#{1,' + $level + '}\s')) {
      return $body.Substring($start, $pos - $start).TrimEnd()
    }
    $pos += $line.Length
    if ($i + 1 -lt $parts.Count) { $pos += $parts[$i + 1].Length }
    if ($pos -gt $body.Length) { break }
  }
  return $body.Substring($start).TrimEnd()
}

function Get-Sha256([string]$text) {
  [System.BitConverter]::ToString(
    [System.Security.Cryptography.SHA256]::Create().ComputeHash(
      [System.Text.Encoding]::UTF8.GetBytes($text))).Replace('-','').ToLower()
}

Write-Host "=== skills-hub verify ===" -ForegroundColor Cyan
Write-Host "sources root: $($loaded.sourcesRoot)"
Write-Host "manifest entries: $($manifest.Count)   merged: $($merged.Count)"

if ($merged.Count -gt 0 -and -not (Test-Path $loaded.sourcesRoot)) {
  Write-Host ""
  Write-Host "Sources root not found, so no body can be proven. This is a setup problem," -ForegroundColor Red
  Write-Host "not a content problem. Fix the path and re-run:" -ForegroundColor Yellow
  Write-Host "  `$env:SKILLS_HUB_SOURCES = '<path to the 9 repos>'" -ForegroundColor Yellow
  Write-Host "  (or sources_root in repos.toml)" -ForegroundColor Yellow
  exit 2
}

foreach ($s in $merged) {
  $name = $s.name
  $dir = Join-Path $skillsDir $name
  $bodyFile = Join-Path $dir 'SKILL.md'
  $provFile = Join-Path $dir 'PROVENANCE.md'

  if (-not (Test-Path $bodyFile)) { Write-Host "MISSING body : $name" -ForegroundColor Red; $fail++; continue }
  if (-not (Test-Path $provFile)) { Write-Host "MISSING prov : $name" -ForegroundColor Red; $fail++; continue }

  $text = [System.IO.File]::ReadAllText($bodyFile)
  if ($text -notmatch '(?m)^name:\s*' + [regex]::Escape($name) + '\s*$') {
    Write-Host "NAME MISMATCH: $name (frontmatter name must equal the directory name)" -ForegroundColor Red; $fail++
  }

  # ---- slash eligibility: every shipped skill must be reachable as /<name> ----
  # Discovery needs a kebab-case name matching the directory, and the invocation
  # policy must permit the user surface. Omitted fields default to permitting their
  # surface, so only an explicit user-invocable: false breaks /<name>.
  # disable-model-invocation: true is fine here - it hides the skill from the model
  # while leaving it user-invocable, which is exactly a slash-only skill.
  $fm = [regex]::Match($text, '\A---\r?\n(.*?)\r?\n---', 'Singleline').Groups[1].Value
  if ($name -notmatch '^[a-z0-9]+(-[a-z0-9]+)*$') {
    Write-Host "NOT SLASHABLE: $name (name must be kebab-case to be discovered)" -ForegroundColor Red; $fail++
  }
  $ui = [regex]::Match($fm, '(?m)^user-invocable:\s*(\S+)')
  if ($ui.Success -and $ui.Groups[1].Value -match '^(?i)(false|no|off|0)$') {
    Write-Host "NOT SLASHABLE: $name (user-invocable is off, so /$name cannot be invoked)" -ForegroundColor Red; $fail++
  }

  # ---- composed mode: re-extract and re-hash each excerpt ----
  if (@($s.composed).Count -gt 0) {
    $specFile = Join-Path (Join-Path $hub 'compose') "$name.yml"
    if (-not (Test-Path $specFile)) { Write-Host "NO spec      : $name" -ForegroundColor Red; $fail++; continue }
    $spec = [System.IO.File]::ReadAllText($specFile, [System.Text.Encoding]::UTF8)

    $blocks = @()
    foreach ($blk in [regex]::Matches($spec, '(?ms)^\[\[include\]\](.*?)(?=^\[\[include\]\]|\z)')) {
      $b = $blk.Groups[1].Value
      $blocks += @{
        skill = ([regex]::Match($b, '(?m)^skill\s*=\s*"(.+?)"')).Groups[1].Value
        from  = ([regex]::Match($b, '(?m)^from\s*=\s*"(.+?)"')).Groups[1].Value
        file  = ([regex]::Match($b, '(?m)^file\s*=\s*"(.+?)"')).Groups[1].Value
        whole = $b -match '(?m)^whole\s*=\s*true'
      }
    }

    # hashes recorded in the shipped body's source comments
    $recorded = @{}
    foreach ($m in [regex]::Matches($text, '<!-- source: (.+?) \| (.*?) \| sha256: ([0-9a-f]{64}) -->')) {
      $recorded[$m.Groups[1].Value + '|' + $m.Groups[2].Value] = $m.Groups[3].Value
    }

    $bad = 0
    foreach ($b in $blocks) {
      if (-not $index.ContainsKey($b.skill)) { Write-Host "  EXCERPT SOURCE GONE: $name <- $($b.skill)" -ForegroundColor Red; $bad++; continue }
      $label = if ($b.file) { "file:$($b.file)" + $(if ($b.from) { "#" + ($b.from -replace '^#+\s*','') } else { '' }) } else { $b.from }
      $srcBody = Get-BodyText $index[$b.skill].file
      $excerpt = if ($b.file) {
        $payload = Join-Path $index[$b.skill].dir ($b.file -replace '/', '\')
        if (-not (Test-Path $payload)) { Write-Host "  PAYLOAD GONE: $name <- $($b.skill) '$($b.file)'" -ForegroundColor Red; $bad++; continue }
        $payloadText = [System.IO.File]::ReadAllText($payload, [System.Text.Encoding]::UTF8)
        if ($b.from) { Get-Section $payloadText $b.from } else { $payloadText.TrimEnd() }
      } elseif ($b.whole) { ($srcBody -replace '(?m)^#\s+.*\r?\n', '').Trim() } else { Get-Section $srcBody $b.from }
      if (-not $excerpt) { Write-Host "  SECTION GONE: $name <- $($b.skill) '$label'" -ForegroundColor Red; $bad++; continue }

      $nowHash = Get-Sha256 $excerpt
      $key = $b.skill + '|' + $label
      if (-not $recorded.ContainsKey($key)) { Write-Host "  NO HASH IN BODY: $name <- $key" -ForegroundColor Red; $bad++; continue }
      if ($recorded[$key] -ne $nowHash) {
        Write-Host "  EXCERPT DRIFT: $name <- $($b.skill) '$label' upstream changed, re-compose" -ForegroundColor Yellow
      }
      if ($text -notmatch [regex]::Escape($excerpt)) {
        Write-Host "  EXCERPT ALTERED: $name <- $($b.skill) '$label' not found verbatim in the shipped body" -ForegroundColor Red
        $bad++
      }
    }
    if ($bad -eq 0) { Write-Host "OK    $name (composed, $($blocks.Count) excerpts all verbatim)" -ForegroundColor Green }
    else { $fail++ }
    continue
  }

  # ---- verbatim mode ----
  $prov = [System.IO.File]::ReadAllText($provFile, [System.Text.Encoding]::UTF8)
  $upstreamName = ([regex]::Match($prov, '(?m)^- upstream:\s*(.+?)\s*$')).Groups[1].Value
  $recordedHash = ([regex]::Match($prov, '(?m)^- upstream SKILL\.md sha256:\s*([0-9a-fA-F]{64})')).Groups[1].Value
  $bodyChanged  = ([regex]::Match($prov, '(?m)^- body changed:\s*(.+?)\s*$')).Groups[1].Value
  if (-not $upstreamName) { Write-Host "NO upstream in PROVENANCE: $name" -ForegroundColor Red; $fail++; continue }

  $verbatimOk = $false
  if ($index.ContainsKey($upstreamName)) {
    $srcRaw = [System.IO.File]::ReadAllText($index[$upstreamName].file)
    $m = [regex]::Match($srcRaw, '\A(---\r?\n)(.*?)(\r?\n---\r?\n)', 'Singleline')
    if ($m.Success) {
      $expected = $m.Groups[1].Value + [regex]::Replace($m.Groups[2].Value, '(?m)^name:\s*.*$', "name: $name", 1) + $m.Groups[3].Value + $srcRaw.Substring($m.Length)
      if ($expected -cne $text) {
        $max = [Math]::Min($expected.Length, $text.Length); $at = $max
        for ($i = 0; $i -lt $max; $i++) { if ($expected[$i] -cne $text[$i]) { $at = $i; break } }
        $line = ($expected.Substring(0, $at) -split "`n").Count
        Write-Host "BODY MODIFIED: $name differs from upstream '$upstreamName' at line ~$line" -ForegroundColor Red
        $fail++
      } else { $verbatimOk = $true }
    } else { Write-Host "NO frontmatter upstream: $upstreamName" -ForegroundColor Red; $fail++ }
  } else {
    Write-Host "UPSTREAM GONE: $name <- '$upstreamName' not on disk (cannot prove body)" -ForegroundColor Red; $fail++
  }

  if ($index.ContainsKey($upstreamName) -and $recordedHash) {
    $nowHash = (Get-FileHash $index[$upstreamName].file -Algorithm SHA256).Hash
    if ($nowHash -ne $recordedHash) { Write-Host "UPSTREAM DRIFT: $name <- '$upstreamName' changed since vendoring" -ForegroundColor Yellow }
  }
  if ($bodyChanged -and $bodyChanged -ne 'no') { Write-Host "BODY DECLARED CHANGED: $name says '$bodyChanged' but policy is name-only" -ForegroundColor Yellow }
  if ($verbatimOk) { Write-Host "OK    $name (verbatim, name: line only)" -ForegroundColor Green }
}

if (Test-Path $skillsDir) {
  $valid = @($merged | ForEach-Object { $_.name })
  foreach ($d in Get-ChildItem $skillsDir -Directory -ErrorAction SilentlyContinue) {
    if ($valid -notcontains $d.Name) { Write-Host "ORPHAN dir   : $($d.Name) vendored but not merged in manifest" -ForegroundColor Yellow }
  }
}

if ($fail -gt 0) { Write-Host "FAILED: $fail problem(s)" -ForegroundColor Red; exit 1 }
Write-Host "OK: every shipped body is proven against upstream" -ForegroundColor Green
