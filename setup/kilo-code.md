# Kilo Code

> **Runtime note:** the hub needs Python 3.11+. `diagram-the-system` also needs Node.js 18+ and Chrome, Chromium or Edge for its browser gate.

> Paste this whole file into Kilo Code's chat and say: **"set this up for me."**

## What Kilo Code reads

Kilo Code 7.8+ loads native skills. Point `skills.paths` at the hub and every
`skills/<name>/SKILL.md` becomes available on demand; only the name and
description cost context until the model invokes the body.

```json
{
  "skills": {
    "paths": ["<hub>/skills"]
  }
}
```

Merge that into `~/.config/kilo/kilo.json` (global) or `./kilo.json` (project),
replacing `<hub>` with the path from step 0. This loads all 42 hub skills,
including `finish-the-experience`, `deslop-the-writing`, `test-every-surface`
and the updated `review-my-code`.

Do not also copy the same bodies into rules; that doubles the context cost.
Older Kilo versions without native skills use the mode-scoped rules fallback
below.

## Legacy fallback: mode-scoped rules

Use this only if `skills.paths` is unavailable. Rules under `.kilocode/rules/`
are always loaded; mode-scoped rules only load when that mode is active, which
is the cheapest way to get skill-like behaviour without native skills.

Kilo Code's modes map almost 1:1 onto skill categories:

| Mode | Skills that belong there |
|---|---|
| `code` | `build-it-test-first`, `build-in-small-steps`, `finish-the-experience` |
| `debug` | `debug-this-code`, `prove-it-works`, `test-every-surface` |
| `architect` | `write-the-spec`, `break-into-tasks`, `review-the-plan` |
| `ask` | `research-this-topic`, `deslop-the-writing` |
| `orchestrator` | `split-across-agents`, `hand-off-to-next-session` |

One to three per mode. The mode scoping does the real work - resist adding more.

## 0. Find the hub

Everything below uses `$hub`. Resolve it once (idempotent - safe to re-run):

```bash
$hub = $env:SKILLS_HUB
if (-not $hub) {
  $d = Get-Item .
  while ($d -and -not (Test-Path (Join-Path $d.FullName 'skills-hub/tools/verify.py'))) { $d = $d.Parent }
  if ($d) { $hub = Join-Path $d.FullName 'skills-hub' }
}
if (-not $hub -or -not (Test-Path "$hub/skills")) { $hub = Read-Host 'Path to your skills-hub checkout' }
"hub: $hub"
if (-not (Test-Path "$hub/skills")) { throw "no skills/ under $hub" }
```

## Install (legacy rules)

Only for Kilo versions without `skills.paths`. With native skills, the JSON
above is the whole install.

```bash
$map = @{
  'code'         = @('build-it-test-first','build-in-small-steps','finish-the-experience')
  'debug'        = @('debug-this-code','prove-it-works','test-every-surface')
  'architect'    = @('write-the-spec','break-into-tasks','review-the-plan')
  'ask'          = @('research-this-topic','deslop-the-writing')
  'orchestrator' = @('split-across-agents','hand-off-to-next-session')
}

foreach ($mode in $map.Keys) {
  $dir = ".kilocode/rules-$mode"
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
  foreach ($n in $map[$mode]) {
    $src = "$hub/skills/$n/SKILL.md"
    if (-not (Test-Path $src)) { Write-Warning "missing $n"; continue }
    $raw  = [System.IO.File]::ReadAllText($src)
    $body = [regex]::Replace($raw, '\A---\r?\n.*?\r?\n---\r?\n', '', 'Singleline')  # strip skill frontmatter
    Set-Content "$dir/$n.md" $body -Encoding UTF8
  }
}
```

Global baseline (all modes, every project):

```bash
New-Item -ItemType Directory -Force -Path "$HOME/.kilocode/rules" | Out-Null
$src = "$hub/skills/write-less-code/SKILL.md"
$raw = [System.IO.File]::ReadAllText($src)
$body = [regex]::Replace($raw, '\A---\r?\n.*?\r?\n---\r?\n', '', 'Singleline')
Set-Content "$HOME/.kilocode/rules/write-less-code.md" $body -Encoding UTF8
```

## Verify

```bash
$j = Get-Content "$HOME/.config/kilo/kilo.json" -Raw | ConvertFrom-Json
"skills path: $($j.skills.paths -join ', ')"
$root = $j.skills.paths[0]
"skills found: $(@(Get-ChildItem $root -Directory | Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') }).Count)"
```

Expect the hub path and 42. Restart or reload Kilo; the skill picker should list
all 42. If you used the legacy rules fallback, open the Rules panel and confirm
they appear under the right mode.

## Invoking it with `/`

Native skills are model-invoked: ask for the job and the description selects the
skill. If you want an explicit `/name`, add a command shim in
`.kilo/command/<name>.md` (project) or `~/.config/kilo/command/<name>.md`
(global):

```markdown
---
description: <what it does>
---
Use the <skill-name> skill on: $ARGUMENTS
```

The hub does not ship shims; the 42 skill names are the interface.
See [invoking-with-slash.md](invoking-with-slash.md) for the full matrix.

## Notes

- Native skills are on-demand; rules are always loaded. Prefer `skills.paths`.
- If you use the legacy fallback, copy one to three per mode. More is not lazy
  loading.
- Kilo Code also reads `AGENTS.md`. Keep it short; put procedures in skills.
- If skills do not appear, check the JSON path and restart/reload Kilo.
