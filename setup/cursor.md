# Cursor

> **Runtime note:** the hub needs Python 3.11+. `diagram-the-system` also needs Node.js 18+ and Chrome, Chromium or Edge for its browser gate.

> Paste this whole file into Cursor's chat and say: **"set this up for me."**

## What Cursor reads

Cursor has **native skills**. It reads four user-level folders, and
`bootstrap.py` links all 43 skills into them:

| Type | Path | When it loads |
|---|---|---|
| Skills | `~/.cursor/skills/` | on demand, by name |
| Skills, shared | `~/.agents/skills/` | on demand; Codex reads it too |
| Skills, inherited | `~/.claude/skills/` | on demand, when Claude Code is set up |
| Project rules | `.cursor/rules/*.mdc` | per `globs` / `alwaysApply` |
| User rules | Cursor Settings → Rules | every request |
| Legacy | `.cursorrules` (root) | every request, deprecated |

The writing style goes in **User Rules**, which is an app setting with no
documented file. `bootstrap.py` prints the text and the click path; that one
paste is the only manual step.

Modern rules format is **MDC**: markdown with YAML frontmatter.

```markdown
---
description: When debugging any failure
globs: ["**/*.ts", "**/*.tsx"]
alwaysApply: false
---
<body>
```

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

## The translation rule

A skill is on-demand; a Cursor rule with `alwaysApply: true` is always on. **Do
not copy all 43 skills as always-on rules** — you would spend the whole context
window on trigger text.

Two valid strategies:

### A. On-demand reference (recommended)

Keep the bodies out of `.cursor/rules`, and add one small index rule that tells
Cursor to read a skill file when its topic comes up.

```bash
New-Item -ItemType Directory -Force -Path ".cursor/rules" | Out-Null

$head = @(
  '---'
  'description: Skill index for this repo'
  'alwaysApply: true'
  '---'
  '# Skills'
  ''
  'Skill bodies live in $hub/skills/<name>/SKILL.md.'
  'When a task matches one of these, read that file before acting. Do not improvise the procedure.'
  ''
)
$index = $head -join "`n"

Get-ChildItem "$hub/skills" -Directory | ForEach-Object {
  $f = Join-Path $_.FullName 'SKILL.md'
  if (Test-Path $f) {
    $desc = (Select-String -Path $f -Pattern '^description:' | Select-Object -First 1).Line
    $desc = $desc -replace '^description:\s*',''
    $index += "- $($_.Name) - $desc`n"
  }
}
Set-Content ".cursor/rules/skills-index.mdc" $index -Encoding UTF8
```

### B. Selected always-on rules

Convert only the handful you want permanently in context:

```bash
$want = @('write-less-code','prove-it-works','trim-my-output','debug-this-code')
New-Item -ItemType Directory -Force -Path ".cursor/rules" | Out-Null

foreach ($n in $want) {
  $src = "$hub/skills/$n/SKILL.md"
  if (-not (Test-Path $src)) { Write-Warning "missing $n"; continue }
  $raw = [System.IO.File]::ReadAllText($src)
  $body = [regex]::Replace($raw, '\A---\r?\n.*?\r?\n---\r?\n', '', 'Singleline')  # strip skill frontmatter
  $desc = (Select-String -Path $src -Pattern '^description:' | Select-Object -First 1).Line -replace '^description:\s*',''
  $mdc = "---`ndescription: $desc`nalwaysApply: true`n---`n`n$body"
  Set-Content ".cursor/rules/$n.mdc" $mdc -Encoding UTF8
}
```

This **wraps** the body in MDC frontmatter. It never edits the body text.

## Verify

```bash
Get-ChildItem ".cursor/rules" -Filter *.mdc | ForEach-Object {
  $head = Get-Content $_.FullName -TotalCount 4
  "{0,-34} {1}" -f $_.Name, ($head -match 'alwaysApply').Count
}
```

Open Cursor → Settings → Rules to confirm they are listed.

## Recommended subset for always-on

`write-less-code`, `prove-it-works`, `trim-my-output`, `debug-this-code`

Everything else: strategy A, read on demand.

## Invoking it with `/`

The hub's rule is that every skill is reachable as `/<name>`. Because this tool has no `/<name>`, the hub keeps the body and changes the wrapper.

This tool has no slash mechanism. It reads `.cursor/rules/*.mdc` by glob or `alwaysApply`, so the skill body is loaded by topic rather than by an explicit `/` trigger.

See [invoking-with-slash.md](invoking-with-slash.md) for the full matrix and for
what to do when `/<name>` does not appear.

## Notes

- `alwaysApply: true` on 10 rules will crowd out your actual code. Prefer `globs`
  so a rule only loads for matching files.
- Cursor does not understand `SKILL.md` frontmatter keys like
  `disable-model-invocation` — strip them when converting to MDC.
- `.cursorrules` is deprecated; do not create it in new repos.
