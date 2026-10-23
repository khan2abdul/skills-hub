# Windsurf

> Paste this whole file into Windsurf's Cascade and say: **"set this up for me."**

## What Windsurf reads

| Path | Behaviour |
|---|---|
| `.windsurf/rules/*.md` | project rules, activated per `trigger` |
| `~/.codeium/windsurf/memories/` | global memories |
| `.windsurfrules` (root) | legacy, always-on |

Rules use frontmatter:

```markdown
---
trigger: manual | always_on | model_decision | glob
globs: ["**/*.ts"]
description: One line shown to the model
---
```

`model_decision` is the closest thing to a skill: the model sees the
`description` and loads the body only when it decides it is relevant.

## The translation rule

Use `model_decision` for most skills. That gives you lazy loading without a
native skills directory — and it is exactly the contract a `SKILL.md`
`description` was written for.

## 0. Find the hub

Everything below uses `$hub`. Resolve it once (idempotent - safe to re-run):

```powershell
$hub = $env:SKILLS_HUB
if (-not $hub) {
  $d = Get-Item .
  while ($d -and -not (Test-Path (Join-Path $d.FullName 'skills-hub/tools/verify.ps1'))) { $d = $d.Parent }
  if ($d) { $hub = Join-Path $d.FullName 'skills-hub' }
}
if (-not $hub -or -not (Test-Path "$hub/skills")) { $hub = Read-Host 'Path to your skills-hub checkout' }
"hub: $hub"
if (-not (Test-Path "$hub/skills")) { throw "no skills/ under $hub" }
```

## Install

```powershell
New-Item -ItemType Directory -Force -Path ".windsurf/rules" | Out-Null

# always-on: keep tiny
$always = @('write-less-code','prove-it-works')

# model-decided: the rest, loaded only when relevant
$onDemand = @('debug-this-code','write-the-spec','break-into-tasks','build-it-test-first',
              'review-my-code','trim-my-output','check-my-ui','simplify-this-code')

foreach ($n in ($always + $onDemand)) {
  $src = "$hub/skills/$n/SKILL.md"
  if (-not (Test-Path $src)) { Write-Warning "missing $n"; continue }
  $raw  = [System.IO.File]::ReadAllText($src)
  $body = [regex]::Replace($raw, '\A---\r?\n.*?\r?\n---\r?\n', '', 'Singleline')  # strip skill frontmatter
  $desc = (Select-String -Path $src -Pattern '^description:' | Select-Object -First 1).Line -replace '^description:\s*',''
  $trig = if ($always -contains $n) { 'always_on' } else { 'model_decision' }
  $out  = "---`ntrigger: $trig`ndescription: $desc`n---`n`n$body"
  Set-Content ".windsurf/rules/$n.md" $out -Encoding UTF8
}
```

This wraps the body in Windsurf frontmatter. The body text is unchanged.

## Verify

```powershell
Get-ChildItem ".windsurf/rules" -Filter *.md | ForEach-Object {
  $t = (Select-String -Path $_.FullName -Pattern '^trigger:' | Select-Object -First 1).Line
  "{0,-32} {1}" -f $_.Name, $t
}
```

In Windsurf, open Cascade → Rules to confirm activation.

## Recommended subset

- **always_on**: `write-less-code`, `prove-it-works`
- **model_decision**: everything else you use regularly

## Invoking it with `/`

The hub's rule is that every skill is reachable as `/<name>`. Because this tool has no `/<name>`, the hub keeps the body and changes the wrapper.

This tool has no slash mechanism. It reads rules, so the skill body is loaded by topic rather than by an explicit `/` trigger.

See [invoking-with-slash.md](invoking-with-slash.md) for the full matrix and for
what to do when `/<name>` does not appear.

## Notes

- `model_decision` costs one `description` line per rule; `always_on` costs the
  whole body. Never put 20 rules on `always_on`.
- `.windsurfrules` is legacy and always-on. Do not create it in new repos.
- Windsurf rule files are capped in total size (roughly 6k characters each, 12k
  across all rules). Check current docs if a rule silently fails to load.
