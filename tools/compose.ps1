#!/usr/bin/env pwsh
# Builds a composed skill from compose/<name>.yml.
# Every excerpt is copied verbatim from its upstream SKILL.md; sha256 of each is
# recorded so verify.ps1 can prove no excerpt was paraphrased or hand-edited.
param(
  [Parameter(Mandatory)][string]$Name,
  [switch]$Force,
  [switch]$WhatIf
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '_common.ps1')

$hub = Get-HubRoot
$loaded = Read-Repos (Join-Path $hub 'repos.toml')
$index = Get-SkillIndex $loaded.repos

$specFile = Join-Path (Join-Path $hub 'compose') "$Name.yml"
if (-not (Test-Path $specFile)) { throw "no compose spec: $specFile" }
# Read as UTF-8 explicitly: Get-Content -Raw uses the ANSI codepage under
# PowerShell 5.1, which mangles any non-ASCII character in a section heading
# (an em-dash became "a-EUR-?" and the section was never found).
$spec = [System.IO.File]::ReadAllText($specFile, [System.Text.Encoding]::UTF8)

$desc = ([regex]::Match($spec, '(?m)^description\s*=\s*"(.+)"\s*$')).Groups[1].Value
$srcs = ([regex]::Match($spec, '(?m)^sources\s*=\s*\[(.*)\]')).Groups[1].Value
$sourceRepos = @($srcs -split ',' | ForEach-Object { $_.Trim().Trim('"') } | Where-Object { $_ })

# parse [[include]] blocks
$includes = @()
foreach ($blk in [regex]::Matches($spec, '(?ms)^\[\[include\]\](.*?)(?=^\[\[include\]\]|\z)')) {
  $b = $blk.Groups[1].Value
  $inc = @{
    skill = ([regex]::Match($b, '(?m)^skill\s*=\s*"(.+?)"')).Groups[1].Value
    title = ([regex]::Match($b, '(?m)^title\s*=\s*"(.+?)"')).Groups[1].Value
    from  = ([regex]::Match($b, '(?m)^from\s*=\s*"(.+?)"')).Groups[1].Value
    # Some upstream skills keep their procedure in a payload file next to
    # SKILL.md (gstack's sections/*.md). `file` quotes that file whole, the same
    # way `whole = true` quotes a body, so the excerpt stays verbatim.
    file  = ([regex]::Match($b, '(?m)^file\s*=\s*"(.+?)"')).Groups[1].Value
    whole = $b -match '(?m)^whole\s*=\s*true'
  }
  if ($inc.skill) { $includes += $inc }
}
if (-not $includes) { throw "no [[include]] blocks in $specFile" }

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
  # block. Without the fence check, "# Good: Each commit is self-contained" (a
  # bash comment in an example) is read as a heading and truncates the section.
  # Track offsets through the split separators. The old `+ 1` assumed LF and
  # drifted one char per line on CRLF sources, silently cutting the tail of a
  # section (code-review's Process ended at "across" instead of "across axes...").
  # Keep this identical to verify.ps1.
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

$out = New-Object System.Text.StringBuilder
$manifestRows = @()

foreach ($inc in $includes) {
  if (-not $index.ContainsKey($inc.skill)) { throw "include '$($inc.skill)' not found on disk" }
  $file = $index[$inc.skill].file
  $body = Get-BodyText $file
  $label = if ($inc.file) { "file:$($inc.file)" + $(if ($inc.from) { "#" + ($inc.from -replace '^#+\s*','') } else { '' }) } else { $inc.from }
  $excerpt = if ($inc.file) {
    $payload = Join-Path $index[$inc.skill].dir ($inc.file -replace '/', '\')
    if (-not (Test-Path $payload)) { throw "file '$($inc.file)' not found in $($inc.skill)" }
    $payloadText = [System.IO.File]::ReadAllText($payload, [System.Text.Encoding]::UTF8)
    if ($inc.from) { Get-Section $payloadText $inc.from } else { $payloadText.TrimEnd() }
  } elseif ($inc.whole) { ($body -replace '(?m)^#\s+.*\r?\n', '').Trim() } else { Get-Section $body $inc.from }
  if (-not $excerpt) { throw "section '$label' not found in $($inc.skill)" }

  $hash = [System.BitConverter]::ToString(
    [System.Security.Cryptography.SHA256]::Create().ComputeHash(
      [System.Text.Encoding]::UTF8.GetBytes($excerpt))).Replace('-','').ToLower()

  # A title is only needed when the excerpt does not already open with its own
  # heading. Emitting both produced "## Red flags" immediately followed by
  # "## Red flags" in ten shipped skills: the composition read as if each
  # section had been pasted twice. The excerpt's own heading is verbatim
  # upstream text and is kept; the spec title then only labels sections whose
  # source has no heading of its own (a `whole = true` body, or a subsection
  # included by a deeper `from`).
  $startsWithHeading = $excerpt -match '^#{1,6}\s'
  if ($inc.title -and -not $startsWithHeading) {
    [void]$out.AppendLine("## $($inc.title)"); [void]$out.AppendLine()
  }
  [void]$out.AppendLine("<!-- source: $($inc.skill) | $label | sha256: $hash -->")
  [void]$out.AppendLine()
  [void]$out.AppendLine($excerpt)
  [void]$out.AppendLine()
  $manifestRows += [pscustomobject]@{ skill = $inc.skill; from = $label; sha256 = $hash; chars = $excerpt.Length }
}

# Title and source count come from the spec, not from a hardcoded string: this
# used to emit "# Debug This Code" and "three upstream skills" into every
# composition, so a second composed skill shipped with the wrong heading.
$title = ([regex]::Match($spec, '(?m)^title\s*=\s*"(.+)"\s*$')).Groups[1].Value
if (-not $title) {
  $title = (($Name -split '-') | ForEach-Object { $_.Substring(0,1).ToUpper() + $_.Substring(1) }) -join ' '
}
$n = @($includes).Count
$header = @"
---
name: $Name
description: $desc
---

# $title

Composed from verbatim excerpts of $n upstream skill$(if ($n -ne 1) { 's' }). Each section is
byte-identical to its source; provenance and hashes are in PROVENANCE.md.
Do not paraphrase a section when editing - change the compose spec instead.
"@

# TrimEnd + explicit blank line: a here-string's last newline is not preserved, so
# relying on it silently glues the first "## heading" onto the preamble line.
$text = $header.TrimEnd() + "`n`n" + $out.ToString()

# Guard: every block must start on its own line after a blank line. Cheap, and it
# catches the class of bug where concatenation eats the separator.
# Two legitimate exceptions, both present in real upstream skills:
#   - a "## Heading" inside a fence is example text, not a heading;
#   - a heading straight after a closing fence needs no blank line, because the
#     fence itself already ends the block. Rejecting that would force us to edit
#     the source, which the hub forbids.
$prev = ''
$inFence = $false
$prevWasFence = $false
foreach ($line in ($text -split "`n")) {
  if ($line -match '^\s*(```|~~~)') {
    $inFence = -not $inFence
    $prev = $line
    $prevWasFence = -not $inFence   # a closing fence, not an opening one
    continue
  }
  if (-not $inFence -and -not $prevWasFence -and $line -match '^#{1,2} ' -and
      $prev -ne '' -and $prev -notmatch '^\s*$') {
    throw "compose produced a heading with no preceding blank line: '$line'"
  }
  $prev = $line
  $prevWasFence = $false
}

if ($WhatIf) {
  Write-Host "WOULD compose $Name ($($manifestRows.Count) sections, $($text.Length) chars)" -ForegroundColor Cyan
  foreach ($r in $manifestRows) { Write-Host ("  {0,-32} {1,6} chars" -f $r.skill, $r.chars) }
  exit 0
}

$dir = Join-Path (Join-Path $hub 'skills') $Name
if ((Test-Path $dir) -and -not $Force) { Write-Host "exists: $dir (use -Force)" -ForegroundColor Yellow; exit 1 }
New-Item -ItemType Directory -Force -Path $dir | Out-Null
[System.IO.File]::WriteAllText((Join-Path $dir 'SKILL.md'), $text, (New-Object System.Text.UTF8Encoding($false)))

$prov = @"
# Provenance

- canonical: $Name
- mode: composed
- body changed: no (every excerpt verbatim; only headings and ordering are new)
- sources: $($sourceRepos -join ', ')
- spec: compose/$Name.yml
- composed: $(Get-Date -Format 'yyyy-MM-dd')

## Excerpts

| upstream skill | section | sha256 | chars |
|---|---|---|---|
$($manifestRows | ForEach-Object { "| $($_.skill) | $($_.from) | $($_.sha256) | $($_.chars) |" } | Out-String)

Each sha256 above is over the exact excerpt text. verify.ps1 re-extracts and
re-hashes to prove the shipped body still matches upstream.
"@
Set-Content -Path (Join-Path $dir 'PROVENANCE.md') -Value $prov -Encoding UTF8

Write-Host "composed $Name ($($manifestRows.Count) sections, $($text.Length) chars)" -ForegroundColor Green
foreach ($r in $manifestRows) { Write-Host ("  {0,-32} {1,6} chars" -f $r.skill, $r.chars) }
exit 0
