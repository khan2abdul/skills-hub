# Kiro

> Paste this whole file into Kiro's chat and say: **"set this up for me."**

## What Kiro reads

Kiro has **native skills** at `~/.kiro/skills/`, and `bootstrap.py` links all 41
into it. It also reads **steering documents**, which are always-on text:

| Scope | Path | Loading |
|---|---|---|
| Skills | `~/.kiro/skills/` | on demand, by name |
| Workspace steering | `.kiro/steering/*.md` | per frontmatter |
| User steering | `~/.kiro/steering/*.md` | per frontmatter |

Every file in `.kiro/steering/` is loaded on every request. There is no
frontmatter that loads a steering file on demand, so **anything you put there is
always in context.** Use skills for the 41, and steering for the writing style.

## The translation rule

Because Kiro has no lazy loading by default, copying 41 skills into
`.kiro/steering/` will consume your entire context on triggers alone.

Use `manual` inclusion for the ones you want available but not always loaded,
and `always` only for a tiny core.

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

## Install

```bash
New-Item -ItemType Directory -Force -Path ".kiro/steering" | Out-Null

# core: always in context (keep this to 2-4 skills)
$always = @('write-less-code','prove-it-works')

# reference: available, loaded only when you @-mention or Kiro selects them
$manual = @('debug-this-code','write-the-spec','build-it-test-first','review-my-code','trim-my-output')

foreach ($n in ($always + $manual)) {
  $src = "$hub/skills/$n/SKILL.md"
  if (-not (Test-Path $src)) { Write-Warning "missing $n"; continue }
  $raw  = [System.IO.File]::ReadAllText($src)
  $body = [regex]::Replace($raw, '\A---\r?\n.*?\r?\n---\r?\n', '', 'Singleline')  # strip skill frontmatter
  $desc = (Select-String -Path $src -Pattern '^description:' | Select-Object -First 1).Line -replace '^description:\s*',''
  $mode = if ($always -contains $n) { 'always' } else { 'manual' }
  $out  = "---`ninclusion: $mode`ndescription: $desc`n---`n`n$body"
  Set-Content ".kiro/steering/$n.md" $out -Encoding UTF8
}
```

This wraps the body in Kiro steering frontmatter. The body text is unchanged.

## Also create a product/tech steering pair

Kiro's spec workflow expects project steering. These are not from the hub, but
Kiro works far better with them:

```bash
@"
---
inclusion: always
---
# Product

What this product is, who it is for, and what it deliberately is not.
Keep this under 30 lines.
"@ | Set-Content ".kiro/steering/product.md" -Encoding UTF8

@"
---
inclusion: always
---
# Tech

Stack, conventions, and the commands that must pass before "done"
(build, test, lint). Keep this under 30 lines.
"@ | Set-Content ".kiro/steering/tech.md" -Encoding UTF8
```

## Verify

```bash
Get-ChildItem ".kiro/steering" -Filter *.md | ForEach-Object {
  $mode = (Select-String -Path $_.FullName -Pattern '^inclusion:' | Select-Object -First 1).Line
  "{0,-34} {1}" -f $_.Name, $mode
}
```

Then open Kiro → Steering in the sidebar and confirm the files are listed.

## Recommended subset

- **always** (2): `write-less-code`, `prove-it-works`
- **manual** (5–6): `debug-this-code`, `write-the-spec`, `build-it-test-first`,
  `review-my-code`, `trim-my-output`, `break-into-tasks`

## Invoking it with `/`

The hub's rule is that every skill is reachable as `/<name>`. Because this tool has no `/<name>`, the hub keeps the body and changes the wrapper.

This tool has no slash mechanism. It reads steering documents as always-on context, so the skill body is loaded by topic rather than by an explicit `/` trigger.

See [invoking-with-slash.md](invoking-with-slash.md) for the full matrix and for
what to do when `/<name>` does not appear.

## Notes

- Kiro's spec flow (`requirements.md` → `design.md` → `tasks.md`) already covers
  what `write-the-spec` and `break-into-tasks` do. Installing both duplicates the
  procedure — pick one. Prefer Kiro's native spec flow and skip those two skills.
- If a steering file has no frontmatter, Kiro treats it as always-on. That is the
  default trap.
