#!/usr/bin/env pwsh
# The scoring core, shared by rate-skills.ps1 and compare-skills.ps1.
#
# Both tools must score the same way, or "our skill is 7.3 and the original is
# 9.1" would be a comparison between two different rulers. Every function here
# takes plain text and returns numbers plus the evidence behind them.
#
# No side effects, no file writes, no dependency on the skill directory layout
# beyond what is passed in.

# A "gate" is any explicit stop/accept/verify criterion - not just the four
# shouty words. "Definition of done", "acceptance criteria" and plain "criteria"
# are exactly what a gate is, and were being missed: break-into-tasks writes
# "definition of done" and "acceptance" and scored gates 6/10 for not saying
# STOP. Counting the requirement, not the capitalisation.
$GatePatterns = @('\bSTOP\b', '\bMUST\b', '\bNEVER\b', '(?i)\bdo not\b', '(?i)\bbefore you\b',
                  '(?i)\bverif(y|ication|ied)\b', '(?i)\bevidence\b', '(?i)\bcheck\b', '(?i)\bgate\b',
                  '(?i)\bcriteria\b', '(?i)\bdefinition of done\b', '(?i)\bacceptance\b',
                  '(?i)\bstop when\b', '(?i)\bdone when\b', '(?i)\bexit criteri')
$HostKeys = @('preamble-tier', 'allowed-tools', 'triggers', 'hooks', 'model', 'tools')
# Path reference ending in a filename character, not a sentence's full stop:
# "see references/foo.md." must capture "references/foo.md", not "...md."
$RelRef = [regex]'(?<![\w/])((?:references|scripts|assets|templates|examples)/[A-Za-z0-9_.\-/]*[A-Za-z0-9_\-/])'
$PortabilityPatterns = @(
  @{ p = '~/\.claude/skills/';     why = 'hard-coded ~/.claude/skills path' }
  @{ p = 'gstack/bin/';            why = 'calls a gstack helper the hub does not ship' }
  @{ p = '[A-Za-z]:\\\\[Uu]sers\\\\'; why = 'hard-coded Windows user path' }
)

function Get-Frontmatter([string]$text) {
  $m = [regex]::Match($text, '\A---\r?\n(.*?)\r?\n---\r?\n?', 'Singleline')
  if (-not $m.Success) { return @{ keys = @{}; body = $text } }
  $keys = @{}
  $lines = $m.Groups[1].Value -split "`r?`n"
  for ($i = 0; $i -lt $lines.Count; $i++) {
    $km = [regex]::Match($lines[$i], '^([A-Za-z][A-Za-z0-9_-]*):\s*(.*)$')
    if (-not $km.Success) { continue }
    $key = $km.Groups[1].Value
    $val = $km.Groups[2].Value.Trim()
    # A YAML block scalar (| or >) puts the real text on the following indented
    # lines. Reading only the "|" line reports a 1-char description and makes a
    # well-described skill look unnamed.
    if ($val -match '^[|>][+-]?$') {
      $block = @()
      for ($j = $i + 1; $j -lt $lines.Count; $j++) {
        if ($lines[$j] -match '^\s+\S' -or $lines[$j] -match '^\s*$') { $block += $lines[$j].Trim() }
        else { break }
      }
      $val = ($block -join ' ').Trim()
      $i = $j - 1
    } else {
      # plain or quoted scalar that continues on the next indented line
      for ($j = $i + 1; $j -lt $lines.Count; $j++) {
        if ($lines[$j] -match '^\s+\S') { $val += ' ' + $lines[$j].Trim() }
        else { break }
      }
      $i = $j - 1
    }
    $keys[$key] = $val.Trim('"').Trim("'")
  }
  @{ keys = $keys; body = $text.Substring($m.Length) }
}

function Get-Grade([double]$score) {
  if ($score -ge 9) { 'A' } elseif ($score -ge 8) { 'B' } elseif ($score -ge 7) { 'C' }
  elseif ($score -ge 6) { 'D' } else { 'F' }
}

function Get-SizeBand([int]$chars) {
  if ($chars -lt 1500) { return @{ s = 2; why = "$chars chars - stub, not a procedure" } }
  if ($chars -lt 3000) { return @{ s = 6; why = "$chars chars - thin" } }
  if ($chars -le 20000) { return @{ s = 10; why = "$chars chars - in range" } }
  if ($chars -le 45000) { return @{ s = 7; why = "$chars chars - heavy" } }
  @{ s = 4; why = "$chars chars - context bomb" }
}

# Scores the craft half only. Selection needs manifest context, so the caller
# adds it. $Name/$ExpectedName let a shipped skill be judged on whether its
# frontmatter name still matches its directory after the rename.
function Get-CraftScore {
  param(
    [Parameter(Mandatory)][string]$Text,
    [Parameter(Mandatory)][string]$Name,
    [string]$SkillDir = ''
  )
  $fm = Get-Frontmatter $Text
  $body = $fm.body
  $dims = @{}; $ev = @{}

  # ---- structure
  $s = 0; $e = @()
  if ($fm.keys['name'] -eq $Name) { $s += 4; $e += 'name matches directory' }
  else { $e += "name mismatch: '$($fm.keys['name'])'" }
  $desc = $fm.keys['description']
  if ($desc) {
    $s += 3
    if ($desc.Length -ge 80 -and $desc.Length -le 1024) { $s += 3; $e += "description $($desc.Length) chars (usable)" }
    else { $e += "description $($desc.Length) chars (want 80-1024)" }
  } else { $e += 'no description' }
  if ($Text -match '(?m)^disable-model-invocation:\s*true') { $e += 'slash-only: model cannot choose it'; $s -= 2 }
  $dims['structure'] = [Math]::Max(0, [Math]::Min(10, $s)); $ev['structure'] = $e

  # ---- procedure
  $steps = ([regex]::Matches($body, '(?m)^\s*\d+\.\s+\S')).Count
  $heads = ([regex]::Matches($body, '(?m)^#{2,3}\s+\S')).Count
  $bullets = ([regex]::Matches($body, '(?m)^\s*[-*]\s+\S')).Count
  $p = if ($steps -ge 6) { 10 } elseif ($steps -ge 3) { 8 } elseif ($steps -ge 1) { 5 } else { 1 }
  if ($heads -ge 4) { $p += 2 } elseif ($heads -ge 2) { $p += 1 }
  if ($bullets -ge 5) { $p += 1 }
  $dims['procedure'] = [Math]::Min(10, $p)
  $ev['procedure'] = @("$steps numbered steps, $heads headings, $bullets bullets")

  # ---- gates
  $hits = @($GatePatterns | Where-Object { $body -match $_ }).Count
  $dims['gates'] = if ($hits -ge 5) { 10 } elseif ($hits -eq 4) { 8 } elseif ($hits -eq 3) { 6 }
                   elseif ($hits -eq 2) { 4 } elseif ($hits -eq 1) { 2 } else { 0 }
  $ev['gates'] = @("$hits gate/verification markers")

  # ---- references (needs a dir to check against; without one, assume present)
  $refs = @($RelRef.Matches($body) | ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique)
  $missing = @()
  if ($SkillDir) {
    foreach ($r in $refs) {
      if (-not (Test-Path (Join-Path $SkillDir ($r -replace '/', '\'))) -and
          -not (Test-Path (Join-Path $SkillDir (Split-Path $r -Leaf)))) { $missing += $r }
    }
  }
  if ($refs.Count -eq 0) { $dims['references'] = 8; $ev['references'] = @('names no resource files') }
  else {
    $present = $refs.Count - $missing.Count
    $dims['references'] = [int][Math]::Round(10 * $present / $refs.Count)
    $e = @("$present/$($refs.Count) referenced files present")
    if ($missing.Count) { $e += 'missing: ' + ($missing -join ', ') }
    $ev['references'] = $e
  }

  # ---- portability
  $issues = @()
  foreach ($pp in $PortabilityPatterns) {
    $n = ([regex]::Matches($body, $pp.p)).Count
    if ($n -gt 0) { $issues += "$($pp.why) ($n x)" }
  }
  $hostK = @($HostKeys | Where-Object { $fm.keys.ContainsKey($_) })
  if ($hostK.Count) { $issues += 'host-specific frontmatter: ' + ($hostK -join ', ') }
  $dims['portability'] = [Math]::Max(0, 10 - 3 * $issues.Count)
  $ev['portability'] = if ($issues.Count) { $issues } else { @('no absolute paths or vendor helpers') }

  # ---- size
  $band = Get-SizeBand $Text.Length
  $dims['size'] = $band.s; $ev['size'] = @($band.why)

  # ---- a body that cannot run here: hooks calling scripts we do not ship
  $depScripts = @([regex]::Matches($body, '([\w.\-]+\.sh)\b') | ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique)
  $hasHooks = $Text -match '(?mi)^\s*hooks:'
  $notExecutable = $false
  if (($body.Trim().Length -lt 300 -and $Text -match '(?mi)^\s*(hooks|allowed-tools):') -or
      ($hasHooks -and $depScripts.Count -gt 0)) {
    $notExecutable = $true
    $dims['procedure'] = [Math]::Min($dims['procedure'], 2)
    $dims['gates'] = [Math]::Min($dims['gates'], 2)
    $dims['portability'] = [Math]::Min($dims['portability'], 2)
    $ev['procedure'] += 'not executable in this install'
  }

  @{ dims = $dims; evidence = $ev; body = $body; keys = $fm.keys
     refs = $refs; missing = $missing; notExecutable = $notExecutable
     hasHooks = $hasHooks; depScripts = $depScripts }
}

function Get-CraftAverage($Dims, $Weights) {
  $sum = 0.0; $w = 0
  foreach ($k in $Weights.Keys) { $sum += $Weights[$k] * $Dims[$k]; $w += $Weights[$k] }
  [Math]::Round($sum / $w, 1)
}
