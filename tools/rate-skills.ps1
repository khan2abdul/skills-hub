#!/usr/bin/env pwsh
# Scores every shipped skill out of 10 and writes RATING.md + RATING.json.
#
# Two halves, because "is this a good skill" and "was this the best skill
# available" are different questions:
#
#   craft      (75%)  is the shipped text well made? structure, procedure,
#                     gates, references, portability, size.
#   selection  (25%)  did we take the strongest source for the job? A skill whose
#                     dropped candidate is 12x larger loses points here.
#
# The split exists because a well-made copy of the wrong skill is still wrong,
# and 72 upstream skills lost their slot without a recorded reason.
#
# Every dimension reports the evidence it counted, so a score can be argued
# with. RATING.json carries machine-actionable fixes; tools/apply-rating.ps1
# reads it. Skill bodies are never edited - only files around the body.
#
#   rate-skills.ps1            -> write RATING.md + RATING.json
#   rate-skills.ps1 -WhatIf    -> print the scoreboard, write nothing
param([switch]$WhatIf)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '_common.ps1')
. (Join-Path $PSScriptRoot '_rubric.ps1')

$RubricVersion = 2
$CraftShare = 0.75

# Craft weights sum to 100.
$Weights = [ordered]@{
  structure = 15; procedure = 20; gates = 15
  references = 20; portability = 15; size = 15
}
$DimHelp = @{
  structure   = 'frontmatter parses, name matches dir, description usable'
  procedure   = 'numbered steps and headings - does it say what to do'
  gates       = 'STOP/MUST/NEVER and verification language'
  references  = 'files the body names exist in the skill dir'
  portability = 'no absolute paths or uninstalled vendor helpers'
  size        = 'big enough to be a procedure, small enough to load'
}
$RelRef = [regex]'(?<![\w/])((?:references|scripts|assets|templates|examples)/[A-Za-z0-9_.\-/]+)'

# Get-Frontmatter / Get-Grade / Get-SizeBand come from _rubric.ps1. They used to be
# duplicated here, which is how this tool kept reporting polish-the-ui's description
# as 1 char long after the shared parser learned to read YAML block scalars.

# ---------------------------------------------------------------- inputs

$hub = Get-HubRoot
$skillsDir = Join-Path $hub 'skills'
if (-not (Test-Path $skillsDir)) { Write-Host "no skills/ directory" -ForegroundColor Red; exit 2 }

$cov = Get-SkillCoverage
$index = $cov.index
$shipped = $cov.shipped
$ignored = $cov.ignored

# canonical -> candidate upstream names, from the manifest
$cands = @{}
foreach ($s in $cov.manifest) { $cands[$s.name] = @($s.candidates) }

$rows = @()
foreach ($d in (Get-ChildItem $skillsDir -Directory | Sort-Object Name)) {
  $file = Join-Path $d.FullName 'SKILL.md'
  if (-not (Test-Path $file)) { continue }
  $name = $d.Name
  $text = [System.IO.File]::ReadAllText($file)
  $findings = New-Object System.Collections.ArrayList
  $fixes = New-Object System.Collections.ArrayList

  # All six craft dimensions come from the shared rubric so that this tool and
  # compare-skills.ps1 cannot disagree about the same file.
  $craft0 = Get-CraftScore -Text $text -Name $name -SkillDir $d.FullName
  $body = $craft0.body
  $fm = @{ keys = $craft0.keys }
  $dims = $craft0.dims; $ev = $craft0.evidence
  $missing = $craft0.missing

  # ---- body that cannot run here: it is frontmatter plus instructions to call
  # scripts the hub does not ship. Prose and bullets do not make it executable.
  $depScripts = $craft0.depScripts
  $hasHooks = $craft0.hasHooks
  if ($craft0.notExecutable) {
    $why = if ($hasHooks) { "hooks plus $($depScripts.Count) helper script(s) the hub does not ship" }
           else { "body is $($body.Trim().Length) chars; the skill is its frontmatter" }
    [void]$findings.Add([pscustomobject]@{ id = 'EMPTY-BODY'; severity = 'high'; auto = $false
      message = "$why - the skill does nothing in this install"
      suggest = 're-vendor a prose skill for this capability, or drop the entry' })
  }

  # ---- broken references: copy the file from upstream, body untouched
  # The upstream skills this body was built from. The manifest's `composed` list
  # is authoritative and is what verify.ps1 re-hashes against. Get-ShippedSources
  # cannot answer this: it maps each upstream skill to ONE canonical name, so when
  # two skills compose the same upstream (frontend-ui-engineering feeds both
  # check-my-ui and polish-the-ui) only the first keeps the link. Reading sources
  # from that map made composed skills look single-sourced, which then sent them
  # down the "compare against every candidate" branch below and penalised them for
  # not beating unrelated skills.
  $me = @($cov.manifest | Where-Object { $_.name -eq $name })
  $sources = if ($me.Count -and @($me[0].composed).Count) { @($me[0].composed) }
             else { @($shipped.Keys | Where-Object { $shipped[$_] -eq $name }) }
  foreach ($r in $missing) {
    $src = $null
    foreach ($sname in $sources) {
      if (-not $index.ContainsKey($sname)) { continue }
      $srcdir = $index[$sname].dir
      $cand = Join-Path $srcdir ($r -replace '/', '\')
      if (Test-Path $cand) { $src = $cand; break }
      # upstream may keep the payload at the repo root (gstack ships scripts/ and
      # bin/ there, not inside each skill dir), so walk up a bounded number of levels
      $probe = $srcdir
      for ($up = 0; $up -lt 4 -and $probe; $up++) {
        $probe = Split-Path $probe -Parent
        if (-not $probe) { break }
        $try = Join-Path $probe ($r -replace '/', '\')
        if (Test-Path $try) { $src = $try; break }
      }
      if ($src) { break }
      $found = Get-ChildItem $srcdir -Recurse -File -Filter (Split-Path $r -Leaf) -ErrorAction SilentlyContinue |
        Select-Object -First 1
      if ($found) { $src = $found.FullName; break }
    }
    [void]$findings.Add([pscustomobject]@{ id = 'REF-MISSING'; severity = 'high'; auto = ($null -ne $src)
      message = "body names ``$r`` but the skill does not ship it"; suggest = '' })
    if ($src) {
      [void]$fixes.Add([pscustomobject]@{
        kind = 'payload'; skill = $name; ref = $r
        source = $src.Substring($hub.Length).TrimStart('\', '/')
        target = (Join-Path $name ($r -replace '/', '\'))
        finding = 'REF-MISSING'
      })
    }
  }

  # ---- vendor helpers that are not installed
  $helpers = @([regex]::Matches($body, 'gstack/bin/([A-Za-z0-9_.\-]+)') |
    ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique)
  if ($helpers.Count) {
    [void]$findings.Add([pscustomobject]@{ id = 'VENDOR-HELPER'; severity = 'high'; auto = $false
      message = "calls $($helpers.Count) gstack helper(s) the hub does not install; vendor bin/ or drop the calls"
      suggest = 'vendor gstack bin/ for this skill, or re-vendor a prose-only alternative' })
  }

  $craft = 0.0; $wsum = 0
  foreach ($k in $Weights.Keys) { $craft += $Weights[$k] * $dims[$k]; $wsum += $Weights[$k] }
  $craft = $craft / $wsum

  # ---- selection: was this the strongest source for the job?
  # Scored on CRAFT, not byte count. Size was a bad proxy: `spec` is 18x larger
  # than `to-spec` and scores 6.9 vs 8.4, and 7 of the 8 candidates this used to
  # flag as "larger, so you chose wrong" score LOWER than the skill we shipped.
  # A bigger body that writes worse is not a better source.
  $better = @()
  foreach ($c in @($cands[$name])) {
    if (-not $c) { continue }
    if ($shipped.ContainsKey($c) -or $ignored.ContainsKey($c) -or $c -eq $name) { continue }
    if (-not $index.ContainsKey($c)) { continue }
    $cf = $index[$c].file
    $cs = Get-CraftScore -Text ([System.IO.File]::ReadAllText($cf)) -Name $c -SkillDir (Split-Path $cf -Parent)
    $better += [pscustomobject]@{
      name  = $c
      chars = (Get-Item $cf).Length
      craft = [Math]::Round((Get-CraftAverage $cs.dims $Weights), 2)
    }
  }
  $better = @($better | Sort-Object craft -Descending)
  $sel = 10; $selNote = 'no candidate scores higher'
  $selProblem = $false
  # A composed skill already absorbed its candidates. Judge it on craft: if it
  # writes at least as well as the best source it used, the choice was right.
  $isComposed = @($sources).Count -gt 1
  if ($isComposed) {
    $bestSrc = 0; $bestName = ''
    foreach ($sname in $sources) {
      if (-not $index.ContainsKey($sname)) { continue }
      $sf = $index[$sname].file
      $ss = Get-CraftScore -Text ([System.IO.File]::ReadAllText($sf)) -Name $sname -SkillDir (Split-Path $sf -Parent)
      $sc = Get-CraftAverage $ss.dims $Weights
      if ($sc -gt $bestSrc) { $bestSrc = [Math]::Round($sc, 2); $bestName = $sname }
    }
    if ($craft -ge $bestSrc - 0.05) {
      $sel = 10; $selNote = "composed from $($sources.Count) sources, craft matches best source ($bestName $bestSrc)"
    } else {
      $sel = 7; $selNote = "composition craft $craft is below its best source ($bestName $bestSrc)"
      $selProblem = $true
    }
  }
  # A very large body costs context even when it is the best available: it is not
  # a wrong choice, but it is not a 10 either.
  elseif ($text.Length -gt 45000) {
    $sel = 8; $selNote = "largest body in the hub ($($text.Length)c); right choice, heavy to load"
    $selProblem = $true
  }
  elseif ($better.Count) {
    $gap = [Math]::Round($better[0].craft - $craft, 1)
    if ($gap -ge 1.0) {
      $sel = 4
      $selNote = "candidate '$($better[0].name)' writes better (craft $($better[0].craft) vs $craft)"
      $selProblem = $true
    } elseif ($gap -ge 0.3) {
      $sel = 7; $selNote = "candidate '$($better[0].name)' writes slightly better (craft $($better[0].craft) vs $craft)"
      $selProblem = $true
    } else {
      $sel = 10; $selNote = "no candidate writes better (best is $($better[0].name) at $($better[0].craft) vs $craft)"
    }
  }
  # Only a real selection problem is a finding; "-1 for being smaller" is noise.
  if ($selProblem) {
    [void]$findings.Add([pscustomobject]@{ id = 'BIGGER-CANDIDATE'; severity = 'medium'; auto = $false
      message = $selNote
      suggest = "pwsh tools/compose.ps1 -Name $name   # add its sections, or re-vendor from it" })
  }

  if ($text -match '(?m)^disable-model-invocation:\s*true') {
    [void]$findings.Add([pscustomobject]@{ id = 'SLASH-ONLY'; severity = 'medium'; auto = $false
      message = "model cannot select this skill; only /$name runs it"
      suggest = 'decide: human-invoked by design, or drop that line in the compose spec' })
  }

  $score = [Math]::Round($CraftShare * $craft + (1 - $CraftShare) * $sel, 1)

  $rows += [pscustomobject]@{
    name = $name; score = $score; grade = (Get-Grade $score)
    craft = [Math]::Round($craft, 1); selection = $sel; selection_note = $selNote
    chars = $text.Length; dimensions = $dims; evidence = $ev
    findings = @($findings); fixes = @($fixes)
  }
}

if (-not $rows) { Write-Host 'no skills found' -ForegroundColor Red; exit 2 }

# Guard: a report that silently skips a skill is worse than no report.
$dirs = @(Get-ChildItem $skillsDir -Directory | Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') }).Count
if ($rows.Count -ne $dirs) { Write-Host "rated $($rows.Count) of $dirs skill dirs" -ForegroundColor Red; exit 1 }

# ---------------------------------------------------------------- plan

$GainByFinding = @{ 'EMPTY-BODY' = 3.0; 'REF-MISSING' = 2.5; 'VENDOR-HELPER' = 2.0
                    'BIGGER-CANDIDATE' = 1.5; 'SLASH-ONLY' = 0.8 }
$plan = @()
foreach ($r in $rows) {
  foreach ($f in $r.findings) {
    $gain = if ($GainByFinding.ContainsKey($f.id)) { $GainByFinding[$f.id] } else { 1.0 }
    $plan += [pscustomobject]@{
      skill = $r.name; finding = $f.id; severity = $f.severity; auto = $f.auto
      gain = $gain; message = $f.message; command = $f.suggest
    }
  }
}
$plan = @($plan | Sort-Object @{ Expression = 'gain'; Descending = $true }, severity, skill)

$scores = @($rows | ForEach-Object { $_.score })
$mean = [Math]::Round(($scores | Measure-Object -Average).Average, 2)
$autoCount = @($plan | Where-Object { $_.auto }).Count

if ($WhatIf) {
  $rows | Sort-Object score -Descending |
    Format-Table @{n='skill';e={$_.name}}, @{n='score';e={$_.score}}, @{n='grade';e={$_.grade}},
                 @{n='craft';e={$_.craft}}, @{n='sel';e={$_.selection}}, @{n='chars';e={$_.chars}} -AutoSize
  Write-Host "WOULD write RATING.md + RATING.json: $($rows.Count) skills, mean $mean/10, $autoCount auto-fixable" -ForegroundColor Cyan
  exit 0
}

# ---------------------------------------------------------------- output

$json = [ordered]@{
  generated = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
  rubric_version = $RubricVersion
  craft_share = $CraftShare
  weights = $Weights
  dim_help = $DimHelp
  summary = [ordered]@{
    count = $rows.Count; mean = $mean
    min = ($scores | Measure-Object -Minimum).Minimum
    max = ($scores | Measure-Object -Maximum).Maximum
    by_grade = @($rows | Group-Object grade | ForEach-Object { @{ grade = $_.Name; count = $_.Count } })
    auto_fixes = $autoCount
  }
  skills = $rows
  plan = $plan
}
[System.IO.File]::WriteAllText((Join-Path $hub 'RATING.json'),
  ($json | ConvertTo-Json -Depth 8), (New-Object System.Text.UTF8Encoding($false)))

$md = New-Object System.Text.StringBuilder
function W([string]$s = '') { [void]$md.AppendLine($s) }

W '# Skill rating'
W ''
W "Every shipped skill scored out of 10 by ``tools/rate-skills.ps1`` (rubric v$RubricVersion)."
W 'Wire: `tools/apply-rating.ps1`. Do not edit by hand - re-run the tool.'
W ''
$grades = ($rows | Group-Object grade | Sort-Object Name | ForEach-Object { "$($_.Name) $($_.Count)" }) -join ', '
W "**Mean $mean/10** over $($rows.Count) skills. Grades: $grades."
W ''
W 'The score has two halves, because "is this a good skill" and "was this the'
W 'best skill available" are different questions:'
W ''
W "- **craft (75%)** - is the shipped text well made?"
W "- **selection (25%)** - did we take the strongest source for the job?"
W ''
W 'A well-made copy of the wrong skill is still the wrong skill. Selection is'
W 'where a wrong-but-well-made choice shows up.'
W ''
W '## Craft dimensions'
W ''
W '| dimension | weight | measures |'
W '|---|---|---|'
foreach ($k in $Weights.Keys) { W "| $k | $($Weights[$k]) | $($DimHelp[$k]) |" }
W ''
W '## Scoreboard'
W ''
W '| # | skill | score | grade | craft | sel | struc | proc | gates | refs | port | size | chars |'
W '|---|---|---|---|---|---|---|---|---|---|---|---|---|'
$i = 0
foreach ($r in ($rows | Sort-Object score -Descending)) {
  $i++
  $d = $r.dimensions
  W ("| $i | ``$($r.name)`` | **$($r.score)** | $($r.grade) | $($r.craft) | $($r.selection) | " +
     "$($d['structure']) | $($d['procedure']) | $($d['gates']) | $($d['references']) | " +
     "$($d['portability']) | $($d['size']) | $($r.chars) |")
}
W ''

W '## How to improve'
W ''
W 'Ranked by score gain. `auto` fixes are applied by `pwsh tools/apply-rating.ps1 -Apply`;'
W '`no` ones need a decision from you.'
W ''
W '| # | skill | finding | gain | auto | what to do |'
W '|---|---|---|---|---|---|'
$i = 0
foreach ($p in $plan) {
  $i++
  $how = if ($p.command) { $p.command } else { $p.message }
  W "| $i | ``$($p.skill)`` | $($p.finding) | +$($p.gain) | $(if ($p.auto) { 'yes' } else { 'no' }) | $how |"
}
W ''

$worst = @($rows | Sort-Object score | Where-Object { $_.findings.Count -gt 0 } | Select-Object -First 8)
if ($worst.Count) {
  W '## Why the weakest skills are weak'
  W ''
  foreach ($r in $worst) {
    W "### ``$($r.name)`` - $($r.score)/10 ($($r.grade))"
    W ''
    W "- selection $($r.selection)/10 - $($r.selection_note)"
    foreach ($k in $Weights.Keys) {
      if ($r.dimensions[$k] -lt 10) { W "- **$k $($r.dimensions[$k])/10** - $(($r.evidence[$k]) -join '; ')" }
    }
    foreach ($f in $r.findings) { W "- ``$($f.id)`` $($f.message)" }
    W ''
  }
}

[System.IO.File]::WriteAllText((Join-Path $hub 'RATING.md'),
  $md.ToString(), (New-Object System.Text.UTF8Encoding($false)))

Write-Host "wrote RATING.md + RATING.json" -ForegroundColor Green
Write-Host "  $($rows.Count) skills, mean $mean/10, $autoCount auto-fixable"
Write-Host "  weakest: $(($rows | Sort-Object score | Select-Object -First 1).name)" -ForegroundColor Yellow
exit 0

