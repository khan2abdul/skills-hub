#!/usr/bin/env pwsh
# Scores a debugging skill against a fixed rubric of practices that matter.
# Read-only. Gives a defensible answer to "is the composed skill actually better?"
#
# Each rubric item is detected by a pattern the file must contain. Detection is
# intentionally concrete: a skill that merely gestures at "reproduce" without a
# procedure scores lower than one that specifies how.
#
#   evaluate.ps1                 -> score the composed skill + every candidate
#   evaluate.ps1 -File <path>    -> score one file
param([string]$File = "")
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '_common.ps1')

$hub = Get-HubRoot

# name, weight, pattern, why it matters
$rubric = @(
  @{ n='Reproduce before fixing';   w=3; p='(?i)reproducable|reproduce|repro\b';        why='without a red signal you are guessing' }
  @{ n='Refuse symptom fixes';      w=3; p='(?i)root cause|symptom fix|not the symptom'; why='the single most common failure' }
  @{ n='Minimise the repro';        w=2; p='(?i)minimi[sz]e|minimal (repro|case|example)'; why='shrinks the hypothesis space' }
  @{ n='Build a tight loop';        w=3; p='(?i)feedback loop|tight(er)? loop|red-capable'; why='turns debugging from staring into testing' }
  @{ n='Ranked hypotheses (3+)';    w=3; p='(?i)3-5|three to five|ranked hypotheses|multiple hypotheses|several hypotheses'; why='single-hypothesis anchors on the first idea' }
  @{ n='One variable at a time';    w=2; p='(?i)one variable|single (change|variable)';   why='confounded tests prove nothing' }
  @{ n='Targeted instrumentation';  w=2; p='(?i)instrument|targeted log|tag every|prefix'; why='"log everything and grep" is not a method' }
  @{ n='Non-deterministic handling';w=3; p='(?i)non-?deterministic|flaky|intermittent|race'; why='most real bugs are flaky' }
  @{ n='Regression test for bug';   w=3; p='(?i)regression test|failing test|test that (fails|catches)'; why='stops it coming back' }
  @{ n='Verify end-to-end';         w=2; p='(?i)end-to-end|full (test )?suite|re-run';    why='a green unit test is not a fixed bug' }
  @{ n='Cleanup instrumentation';   w=1; p='(?i)remov(e|ing) .*(instrument|log)|cleanup|delete.*prototype'; why='debug code leaks to prod' }
  @{ n='Question architecture';     w=2; p='(?i)architectur(e|al)';                        why='3 failed fixes means the design is wrong' }
  @{ n='Error output untrusted';    w=2; p='(?i)untrusted|do not (execute|follow)|embedded instruction'; why='prompt injection via stack traces' }
  @{ n='Redact secrets';            w=2; p='(?i)redact|<REDACTED>|secret';                 why='debugging leaks credentials' }
  @{ n='Anti-rationalisation';      w=2; p='(?i)rationali[sz]ation|red flag|excuse';        why='names the shortcuts agents take' }
  @{ n='Triage by layer';           w=2; p='(?i)which layer|locali[sz]e|bisect';           why='narrows where to look' }
)

function Get-Score([string]$path) {
  if (-not (Test-Path $path)) { return $null }
  $raw = [System.IO.File]::ReadAllText($path)
  # score the body only: frontmatter description would inflate coverage
  $body = [regex]::Replace($raw, '\A---\r?\n.*?\r?\n---\r?\n', '', 'Singleline')
  $hits = @()
  $got = 0; $max = 0
  foreach ($r in $rubric) {
    $max += $r.w
    if ($body -match $r.p) { $got += $r.w; $hits += $r.n }
  }
  [pscustomobject]@{
    file    = $path
    name    = Split-Path (Split-Path $path -Parent) -Leaf
    chars   = $body.Length
    tokens  = [math]::Round($body.Length / 4)
    score   = $got
    max     = $max
    pct     = [math]::Round(100 * $got / $max)
    covered = $hits.Count
  }
}

$loaded = Read-Repos (Join-Path $hub 'repos.toml')
$index = Get-SkillIndex $loaded.repos

$files = @()
$composed = Join-Path (Join-Path $hub 'skills') 'debug-this-code/SKILL.md'
if (Test-Path $composed) { $files += $composed }

if ($File) {
  $files = @($File)
} else {
  foreach ($n in @('debugging-and-error-recovery','systematic-debugging','diagnosing-bugs','debug-like-expert','investigate-first')) {
    if ($index.ContainsKey($n)) { $files += $index[$n].file }
  }
}

$rows = foreach ($f in $files) { Get-Score $f }

Write-Host "=== rubric: $($rubric.Count) practices, max $($rows[0].max) points ===" -ForegroundColor Cyan
$rows | Sort-Object -Property pct -Descending | Format-Table -AutoSize `
  @{n='skill';e={$_.name}}, @{n='pts';e={"$($_.score)/$($_.max)"}}, `
  @{n='cover%';e={$_.pct}}, @{n='items';e={"$($_.covered)/$($rubric.Count)"}}, `
  @{n='chars';e={$_.chars}}, @{n='~tok';e={$_.tokens}}

# per-item matrix so a win is auditable, not asserted
Write-Host "=== per-practice coverage ===" -ForegroundColor Cyan
$hdr = '{0,-30}' -f 'practice'
foreach ($r in $rows) { $hdr += '{0,10}' -f ($r.name.Substring(0, [Math]::Min(9, $r.name.Length))) }
Write-Host $hdr
$bodies = @{}
foreach ($r in $rows) {
  $raw = [System.IO.File]::ReadAllText($r.file)
  $bodies[$r.name] = [regex]::Replace($raw, '\A---\r?\n.*?\r?\n---\r?\n', '', 'Singleline')
}
foreach ($item in $rubric) {
  $line = '{0,-30}' -f $item.n
  foreach ($r in $rows) { $line += '{0,10}' -f $(if ($bodies[$r.name] -match $item.p) { 'yes' } else { '.' }) }
  Write-Host $line
}
