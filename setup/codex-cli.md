# OpenAI Codex CLI

> Paste this whole file into Codex CLI and say: **"set this up for me."**

## What Codex CLI reads

| Scope | Path |
|---|---|
| Project | `AGENTS.md` (root, and nested per directory) |
| Global | `~/.codex/AGENTS.md` |
| Config | `~/.codex/config.toml` |

Codex CLI has no `SKILL.md` discovery. `AGENTS.md` is merged into context; nested
files apply to their subtree.

## The translation rule

`AGENTS.md` files are additive context. Same discipline as Cline and Gemini: a
small core, and a path index for everything else.

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
$core = @('write-less-code','prove-it-works','trim-my-output')
$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine("# Procedures")
[void]$sb.AppendLine()
[void]$sb.AppendLine('Full skill bodies live in `$hub/skills/<name>/SKILL.md`.')
[void]$sb.AppendLine('When a task matches one below, read that file before acting.')
[void]$sb.AppendLine()

foreach ($n in $core) {
  $src = "$hub/skills/$n/SKILL.md"
  if (-not (Test-Path $src)) { Write-Warning "missing $n"; continue }
  $raw  = [System.IO.File]::ReadAllText($src)
  $body = [regex]::Replace($raw, '\A---\r?\n.*?\r?\n---\r?\n', '', 'Singleline')
  [void]$sb.AppendLine("## $n")
  [void]$sb.AppendLine()
  [void]$sb.AppendLine($body.Trim())
  [void]$sb.AppendLine()
}
[System.IO.File]::WriteAllText("./AGENTS.md", $sb.ToString(), (New-Object System.Text.UTF8Encoding($false)))
```

Index the rest:

```powershell
$idx = "`n## Available, not loaded`n`n"
Get-ChildItem "$hub/skills" -Directory | Where-Object { $core -notcontains $_.Name } | ForEach-Object {
  $f = Join-Path $_.FullName 'SKILL.md'
  if (Test-Path $f) {
    $d = (Select-String -Path $f -Pattern '^description:' | Select-Object -First 1).Line -replace '^description:\s*',''
    $idx += "- **$($_.Name)** - $d`n"
  }
}
Add-Content "./AGENTS.md" $idx
```

## Verify

```powershell
"AGENTS.md exists: " + (Test-Path "./AGENTS.md")
"size: " + (Get-Item "./AGENTS.md").Length + " B"
```

In Codex CLI, ask it to summarise the project rules; if it can name them, they loaded.

## Nested AGENTS.md (recommended for monorepos)

Codex merges nested files for the subtree they sit in. Put directory-specific
procedures where they apply:

```
repo/
  AGENTS.md                 # core, applies everywhere
  packages/api/AGENTS.md    # API-only rules
  packages/web/AGENTS.md    # frontend-only rules
```

```powershell
New-Item -ItemType Directory -Force -Path "packages/api" | Out-Null
@"
# API package
Read `$hub/skills/design-the-interface/SKILL.md` before changing endpoints.
"@ | Set-Content "packages/api/AGENTS.md" -Encoding UTF8
```

## Recommended subset

`write-less-code`, `prove-it-works`, `trim-my-output`

## Invoking it with `/`

The hub's rule is that every skill is reachable as `/<name>`. Because this tool has no `/<name>`, the hub keeps the body and changes the wrapper.

This tool has no slash mechanism. It reads `AGENTS.md` as context, so the skill body is loaded by topic rather than by an explicit `/` trigger.

See [invoking-with-slash.md](invoking-with-slash.md) for the full matrix and for
what to do when `/<name>` does not appear.

## Notes

- Codex CLI also honours `~/.codex/config.toml` for model and sandbox settings —
  that is separate from rules.
- Nested `AGENTS.md` is the cheapest form of scoping Codex offers. Prefer it over
  one giant root file.
- `AGENTS.md` is a shared convention; if you also use Claude Code, keep `CLAUDE.md`
  a one-line pointer to `AGENTS.md` rather than duplicating content.
