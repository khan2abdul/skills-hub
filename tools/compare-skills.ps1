#!/usr/bin/env pwsh
# Compares every shipped skill against the upstream original it was fetched
# from, using ONE rubric for both sides. Answers three questions the plain
# rating cannot:
#
#   fidelity  did we copy it faithfully?        body bytes, payload files, frontmatter
#   gap       what does the original have that ours does not?
#   ceiling   what would it take to reach 10?
#
# The ceiling question matters because our copies are verbatim: when the shipped
# skill scores 6, the original also scores 6. The defect is not in our copy, it
# is in the choice of source. Only composing a stronger source can move it.
#
#   compare-skills.ps1            -> write COMPARISON.md
#   compare-skills.ps1 -WhatIf    -> print the table, write nothing
param([switch]$WhatIf)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '_common.ps1')
. (Join-Path $PSScriptRoot '_rubric.ps1')

$Weights = [ordered]@{ structure = 15; procedure = 20; gates = 15
                       references = 20; portability = 15; size = 15 }
$CraftShare = 0.75

$hub = Get-HubRoot
$skillsDir = Join-Path $hub 'skills'
$cov = Get-SkillCoverage
$index = $cov.index
$shipped = $cov.shipped
$ignored = $cov.ignored
$cands = @{}
foreach ($s in $cov.manifest) { $cands[$s.name] = @($s.candidates) }

function Get-RenamedUpstream([string]$raw, [string]$newName) {
  # Mirror vendor.ps1 exactly: rewrite name: only inside the frontmatter block.
  # [regex]::Replace's 4th positional arg is RegexOptions, not a count - pass 1
  # there and every name: in the file (including code-fence examples) is replaced.
  $m = [regex]::Match($raw, '\A(---\r?\n)(.*?)(\r?\n---\r?\n)', 'Singleline')
  if (-not $m.Success) { return $raw }
  $yaml2 = [regex]::Replace($m.Groups[2].Value, '(?m)^name:\s*.*$', "name: $newName", 'None')
  $m.Groups[1].Value + $yaml2 + $m.Groups[3].Value + $raw.Substring($m.Length)
}

function Get-PayloadDiff([string]$upDir, [string]$shDir) {
  $missing = @(); $differs = @(); $count = 0
  foreach ($f in (Get-ChildItem $upDir -Recurse -File -Force -ErrorAction SilentlyContinue |
                  Where-Object { $_.Name -ne 'SKILL.md' })) {
    $count++
    $rel = $f.FullName.Substring($upDir.Length).TrimStart('\', '/')
    $tgt = Join-Path $shDir $rel
    if (-not (Test-Path $tgt)) { $missing += $rel }
    elseif ((Get-FileHash $f.FullName -Algorithm SHA256).Hash -ne (Get-FileHash $tgt -Algorithm SHA256).Hash) { $differs += $rel }
  }
  @{ count = $count; missing = $missing; differs = $differs }
}

$rows = @()
foreach ($d in (Get-ChildItem $skillsDir -Directory | Sort-Object Name)) {
  $file = Join-Path $d.FullName 'SKILL.md'
  if (-not (Test-Path $file)) { continue }
  $name = $d.Name
  $text = [System.IO.File]::ReadAllText($file)
  $ours = Get-CraftScore -Text $text -Name $name -SkillDir $d.FullName
  $ourCraft = Get-CraftAverage $ours.dims $Weights

  $provText = if (Test-Path (Join-Path $d.FullName 'PROVENANCE.md')) {
    [System.IO.File]::ReadAllText((Join-Path $d.FullName 'PROVENANCE.md')) } else { '' }
  $isComposed = $provText -match '(?m)^- mode:\s*composed'
  # A verbatim skill's PROVENANCE names its upstream directly. The reverse
  # $shipped map keeps only the FIRST canonical per upstream, so a source used
  # by two skills (documentation-and-adrs) left the second one as 'n/a'.
  $upstream = ([regex]::Match($provText, '(?m)^- upstream:\s*(.+?)\s*$')).Groups[1].Value
  $sources = if ($isComposed) {
    @($shipped.Keys | Where-Object { $shipped[$_] -eq $name } | Sort-Object)
  } elseif ($upstream) { @($upstream) } else { @() }
  $primary = if (@($sources).Count) { @($sources)[0] } else { $null }

  # ---- fidelity: for a verbatim copy the body must match the original byte for
  # byte once the frontmatter name: line is rewritten. Anything else is a silent edit.
  $fidelity = 'n/a'
  $bodyDiff = @()
  if (-not $isComposed -and $primary -and $index.ContainsKey($primary)) {
    $upRenamed = Get-RenamedUpstream ([System.IO.File]::ReadAllText($index[$primary].file)) $name
    if ($upRenamed -ceq $text) { $fidelity = 'exact' }
    else {
      $fidelity = 'differs'
      $a = $upRenamed -split "`r?`n"; $b = $text -split "`r?`n"
      for ($i = 0; $i -lt [Math]::Max($a.Count, $b.Count); $i++) {
        $av = if ($i -lt $a.Count) { $a[$i] } else { '<eof>' }
        $bv = if ($i -lt $b.Count) { $b[$i] } else { '<eof>' }
        if ($av -cne $bv) { $bodyDiff += "L$($i + 1): '$av' -> '$bv'" }
      }
    }
  } elseif ($isComposed) { $fidelity = 'composed' }

  # ---- upstream baseline: score the original with the same ruler. Reference
  # checks run against the SHIPPED dir: we are asking "is this original fully
  # usable here", and a payload file we already vendored counts as present.
  $ups = @()
  foreach ($sn in $sources) {
    if (-not $index.ContainsKey($sn)) { continue }
    $uDir = $index[$sn].dir
    $uText = [System.IO.File]::ReadAllText($index[$sn].file)
    $u = Get-CraftScore -Text $uText -Name (Split-Path $uDir -Leaf) -SkillDir $d.FullName
    $pay = Get-PayloadDiff $uDir $d.FullName
    $ups += [pscustomobject]@{
      name = $sn; repo = $index[$sn].repo; dir = $uDir; chars = $uText.Length
      craft = (Get-CraftAverage $u.dims $Weights); dims = $u.dims; evidence = $u.evidence
      payloadUp = $pay.count; payloadMissing = $pay.missing; payloadDiffers = $pay.differs
    }
  }
  $bestUp = if ($ups.Count) { ($ups | Sort-Object craft -Descending)[0] } else { $null }

  # ---- gap: what does the original have that ours does not
  $gaps = @()
  foreach ($u in $ups) {
    if ($u.payloadMissing.Count) {
      $gaps += [pscustomobject]@{ kind = 'payload'; detail = "original ships $($u.payloadMissing.Count) file(s) we do not: $((($u.payloadMissing | Select-Object -First 5) -join ', '))" }
    }
    if (-not $isComposed) {
      foreach ($dim in $Weights.Keys) {
        if ($u.dims[$dim] -gt $ours.dims[$dim]) {
          $gaps += [pscustomobject]@{ kind = "dim:$dim"; detail = "original has $(($u.evidence[$dim]) -join '; ') vs ours $(($ours.evidence[$dim]) -join '; ')" }
        }
      }
    }
  }
  if ($isComposed) {
    # a composition covers more than any one source: only report the loss
    if ($bestUp -and $bestUp.chars -gt $text.Length) {
      $gaps += [pscustomobject]@{ kind = 'truncated'; detail = "composition ($($text.Length)c) is smaller than '$($bestUp.name)' ($($bestUp.chars)c) alone" }
    }
  }
  if ($bodyDiff.Count) {
    $gaps += [pscustomobject]@{ kind = 'body'; detail = "body differs from the original in $($bodyDiff.Count) place(s): $(($bodyDiff | Select-Object -First 3) -join ' | ')" }
  }

  # ---- ceiling: score every alternative the manifest proposed, including the
  # ones that were dropped. If one beats what we shipped, that is the fix.
  $alts = @()
  foreach ($c in @($cands[$name])) {
    if (-not $c -or $c -eq $name) { continue }
    if ($shipped.ContainsKey($c) -and $shipped[$c] -ne $name) { continue }  # used by another skill
    if (-not $index.ContainsKey($c)) { continue }
    if (-not (Get-Command -Name 'Select-Object' -ErrorAction SilentlyContinue)) { }
    $cDir = $index[$c].dir
    $cText = [System.IO.File]::ReadAllText($index[$c].file)
    $cs = Get-CraftScore -Text $cText -Name (Split-Path $cDir -Leaf) -SkillDir $cDir
    $alts += [pscustomobject]@{
      name = $c; repo = $index[$c].repo; chars = $cText.Length
      craft = (Get-CraftAverage $cs.dims $Weights); dims = $cs.dims
      ignored = $ignored.ContainsKey($c)
      shippedElsewhere = $shipped.ContainsKey($c)
    }
  }
  $alts = @($alts | Sort-Object craft -Descending)
  $bestAlt = if ($alts.Count) { $alts[0] } else { $null }

  # ---- what would it take to reach 10
  $ceiling = 10.0
  $verdict = ''
  $actions = @()
  if ($fidelity -eq 'differs' -or $fidelity -eq 'composed' -and $gaps.Count) { }
  if ($fidelity -eq 'differs') {
    $verdict = 'copy is not faithful'
    $actions += 'this is a bug in the hub, not in the source: re-run tools/vendor.ps1 -Skill ' + $name + ' -Force'
  }
  if ($ups.Count -and -not $isComposed) {
    if ([Math]::Abs($bestUp.craft - $ourCraft) -lt 0.05) {
      $verdict = 'faithful copy; the score IS the original score'
    }
  }
  if ($isComposed) { $verdict = 'composition; measured against its own sources' }

  # reachable ceiling = best craft among our own content and any alternative
  $targets = @($ourCraft)
  foreach ($a in $alts) { $targets += $a.craft }
  foreach ($u in $ups) { $targets += $u.craft }
  $reachable = ($targets | Measure-Object -Maximum).Maximum
  $selectionScore = if ($reachable -gt 0) { [Math]::Min(10, $ourCraft / $reachable * 10) } else { 10 }

  if ($bestAlt -and $bestAlt.craft -gt $ourCraft + 0.05) {
    $actions += "re-vendor from '$($bestAlt.name)' (craft $($bestAlt.craft)) instead of '$primary' (craft $ourCraft)"
    $actions += "pwsh tools/vendor.ps1 -Skill $name -Force   # after flipping chosen in manifest.yml"
  }
  foreach ($dim in $Weights.Keys) {
    if ($ours.dims[$dim] -lt 10) {
      $fixer = @($alts | Where-Object { $_.dims[$dim] -gt $ours.dims[$dim] } | Select-Object -First 1)
      if ($fixer.Count) { $actions += "gains $dim ($($ours.dims[$dim]) -> $($fixer[0].dims[$dim])) by composing '$($fixer[0].name)'" }
    }
  }
  if ($ours.notExecutable) {
    $actions += 'not executable here: its hooks call scripts the hub does not ship - replace the source or accept it as read-only guidance'
  }

  $score = [Math]::Round($CraftShare * $ourCraft + (1 - $CraftShare) * $selectionScore, 1)

  $rows += [pscustomobject]@{
    name = $name; score = $score; craft = $ourCraft; selection = [Math]::Round($selectionScore, 1)
    chars = $text.Length; fidelity = $fidelity; composed = $isComposed
    upstream = $bestUp; upstreams = $ups; gaps = @($gaps); alts = $alts
    bestAlt = $bestAlt; verdict = $verdict; actions = @($actions)
    reachable = [Math]::Round($CraftShare * $reachable + (1 - $CraftShare) * 10, 1)
    dims = $ours.dims; evidence = $ours.evidence
  }
}

if (-not $rows) { Write-Host 'no skills found' -ForegroundColor Red; exit 2 }

# --- guard: every shipped skill must appear, or the report hides a gap
$dirs = @(Get-ChildItem $skillsDir -Directory | Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') }).Count
if ($rows.Count -ne $dirs) { Write-Host "compared $($rows.Count) of $dirs skill dirs" -ForegroundColor Red; exit 1 }

$meanOurs = [Math]::Round((($rows | ForEach-Object { $_.craft }) | Measure-Object -Average).Average, 2)
$meanUp = [Math]::Round((($rows | Where-Object { $_.upstream } | ForEach-Object { $_.upstream.craft }) | Measure-Object -Average).Average, 2)
$lossy = @($rows | Where-Object { $_.fidelity -eq 'differs' })
$withAlts = @($rows | Where-Object { $_.bestAlt -and $_.bestAlt.craft -gt $_.craft + 0.05 })

if ($WhatIf) {
  $rows | Sort-Object score |
    Format-Table @{n='skill';e={$_.name}}, @{n='ours';e={$_.craft}}, @{n='orig';e={ if ($_.upstream) { $_.upstream.craft } else { '-' } }},
                 @{n='bestAlt';e={ if ($_.bestAlt) { "$($_.bestAlt.name)=$($_.bestAlt.craft)" } else { '-' } }},
                 @{n='fid';e={$_.fidelity}}, @{n='ceil';e={$_.reachable}} -AutoSize
  Write-Host "WOULD write COMPARISON.md: mean ours $meanOurs vs originals $meanUp, lossy $($lossy.Count), improvable $($withAlts.Count)" -ForegroundColor Cyan
  exit 0
}

# ---------------------------------------------------------------- output
$md = New-Object System.Text.StringBuilder
function W([string]$s = '') { [void]$md.AppendLine($s) }

W '# Shipped vs original'
W ''
W 'Every skill compared against the upstream original it was fetched from, scored'
W 'with the same rubric (`tools/_rubric.ps1`). Wire: `tools/compare-skills.ps1`.'
W ''
W ("**Craft: ours $meanOurs vs originals $meanUp.** Faithfulness: $(@($rows | Where-Object { $_.fidelity -eq 'exact' }).Count) exact, " +
  "$(@($rows | Where-Object { $_.fidelity -eq 'composed' }).Count) composed, $($lossy.Count) lossy.")
W ''
W 'The headline: our copies are verbatim, so a low score is almost never a'
W 'transcription defect. When ours scores 6, the original also scores 6. The'
W 'defect is the **choice of source**, and the only legal fix is to take a better'
W 'one - composing in sections, or re-vendoring from a stronger candidate.'
W ''
W '## Fidelity'
W ''
W '| check | result |'
W '|---|---|'
W "| body byte-identical to original | $(@($rows | Where-Object { $_.fidelity -eq 'exact' }).Count)/$($rows.Count) |"
W "| body differs | $($lossy.Count) |"
W "| payload files missing vs original | $(@($rows | Where-Object { $_.upstream -and $_.upstream.payloadMissing.Count -gt 0 }).Count) skills |"
W "| payload files altered | $(@($rows | Where-Object { $_.upstream -and $_.upstream.payloadDiffers.Count -gt 0 }).Count) skills |"
W ''

W '## Score against the original'
W ''
W '| skill | ours | original | from | fidelity | reachable | gaps |'
W '|---|---|---|---|---|---|---|'
foreach ($r in ($rows | Sort-Object score)) {
  $u = if ($r.upstream) { $r.upstream } else { $null }
  $origS = if ($u) { $u.craft } else { '-' }
  $origN = if ($u) { "``$($u.name)`` ($($u.repo))" } else { '-' }
  W "| ``$($r.name)`` | $($r.craft) | $origS | $origN | $($r.fidelity) | $($r.reachable) | $($r.gaps.Count) |"
}
W ''

W '## Missing pieces'
W ''
$anyGap = @($rows | Where-Object { $_.gaps.Count -gt 0 })
if (-not $anyGap.Count) { W 'None. Every shipped skill carries everything its original carries.' }
foreach ($r in $anyGap) {
  W "### ``$($r.name)`` - $($r.craft)/10 (original $($r.upstream.craft))"
  W ''
  foreach ($g in $r.gaps) { W "- **$($g.kind)** - $($g.detail)" }
  W ''
}

W '## What would make each one a 10'
W ''
W 'Reachable is the ceiling with the material already in `repos/`: our own text'
W 'plus every candidate the manifest proposed. A skill whose reachable equals its'
W 'current score is at its ceiling and cannot be improved without new source material.'
W ''
W '| skill | now | reachable | the move |'
W '|---|---|---|---|'
foreach ($r in ($rows | Sort-Object score)) {
  $move = if ($r.actions.Count) { ($r.actions[0] -replace '\|', '/') } else { 'at ceiling - no better source in repos/' }
  if ($r.actions.Count -gt 1) { $move += " (+$($r.actions.Count - 1) more)" }
  W "| ``$($r.name)`` | $($r.craft) | $($r.reachable) | $move |"
}
W ''

W '## Detail'
W ''
foreach ($r in ($rows | Sort-Object score)) {
  W "### ``$($r.name)`` - $($r.score)/10"
  W ''
  W "fidelity: $($r.fidelity)$(if ($r.verdict) { ' - ' + $r.verdict })"
  W ''
  if ($r.upstreams.Count) {
    W '| source | repo | chars | craft | ' + ($Weights.Keys -join ' | ') + ' |'
    W '|---|---|---|---|' + (($Weights.Keys | ForEach-Object { '---' }) -join '|') + '|'
    foreach ($u in $r.upstreams) {
      $ds = ($Weights.Keys | ForEach-Object { $u.dims[$_] }) -join ' | '
      W "| ``$($u.name)`` | $($u.repo) | $($u.chars) | $($u.craft) | $ds |"
    }
    W ''
    W 'ours: ' + ($Weights.Keys | ForEach-Object { "$_ $($r.dims[$_])" }) -join ', '
    W ''
  }
  if ($r.alts.Count) {
    W 'alternatives the manifest proposed (best first):'
    W ''
    foreach ($a in ($r.alts | Select-Object -First 4)) {
      $tag = if ($a.shippedElsewhere) { 'in use elsewhere' } elseif ($a.ignored) { 'rejected' } else { 'dropped' }
      $arrow = if ($a.craft -gt $r.craft + 0.05) { ' **better than ours**' } else { '' }
      W "- ``$($a.name)`` ($($a.repo), $($a.chars)c) craft $($a.craft) - $tag$arrow"
    }
    W ''
  }
  if ($r.actions.Count) {
    W 'to improve:'
    W ''
    foreach ($a in $r.actions) { W "- $a" }
    W ''
  }
}

[System.IO.File]::WriteAllText((Join-Path $hub 'COMPARISON.md'),
  $md.ToString(), (New-Object System.Text.UTF8Encoding($false)))

Write-Host "wrote COMPARISON.md" -ForegroundColor Green
Write-Host "  craft ours $meanOurs vs originals $meanUp"
Write-Host "  fidelity: $(@($rows | Where-Object { $_.fidelity -eq 'exact' }).Count) exact, $($lossy.Count) lossy" -ForegroundColor $(if ($lossy.Count) { 'Yellow' } else { 'Green' })
Write-Host "  improvable by taking a better source: $($withAlts.Count)"
exit 0
