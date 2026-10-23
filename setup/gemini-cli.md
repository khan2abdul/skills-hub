# Gemini CLI

> Paste this whole file into Gemini CLI and say: **"set this up for me."**

## What Gemini CLI reads

| Scope | Path |
|---|---|
| Context file | `GEMINI.md` (project root, and nested) |
| Global context | `~/.gemini/GEMINI.md` |
| Extensions | `~/.gemini/extensions/<name>/` with `gemini-extension.json` |

Gemini CLI has no native `SKILL.md` discovery. It reads `GEMINI.md` as always-on
context, and extensions add tools/commands.

## The translation rule

`GEMINI.md` is concatenated context. Treat it like Cline: install a small core,
and point at the hub for the rest.

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
[System.IO.File]::WriteAllText("./GEMINI.md", $sb.ToString(), (New-Object System.Text.UTF8Encoding($false)))
```

Add the index of everything else:

```bash
$idx = "`n## Available, not loaded`n`n"
Get-ChildItem "$hub/skills" -Directory | Where-Object { $core -notcontains $_.Name } | ForEach-Object {
  $f = Join-Path $_.FullName 'SKILL.md'
  if (Test-Path $f) {
    $d = (Select-String -Path $f -Pattern '^description:' | Select-Object -First 1).Line -replace '^description:\s*',''
    $idx += "- **$($_.Name)** - $d`n"
  }
}
Add-Content "./GEMINI.md" $idx
```

## Verify

```bash
"GEMINI.md exists: " + (Test-Path "./GEMINI.md")
"size: " + (Get-Item "./GEMINI.md").Length + " B"
Get-Content "./GEMINI.md" -TotalCount 8
```

In Gemini CLI, run `/memory show` to confirm it is loaded.

## Optional: extension packaging

If you want the hub distributed as an installable extension rather than a
context file, create:

```bash
New-Item -ItemType Directory -Force -Path "$HOME/.gemini/extensions/skills-hub" | Out-Null
@'
{
  "name": "skills-hub",
  "version": "1.0.0",
  "description": "Canonical agent skills"
}
'@ | Set-Content "$HOME/.gemini/extensions/skills-hub/gemini-extension.json" -Encoding UTF8
```

Note: an extension alone does not make `SKILL.md` files discoverable — Gemini CLI
still needs the procedures in `GEMINI.md` or a tool that reads them.

## Recommended subset

`write-less-code`, `prove-it-works`, `trim-my-output`

## Invoking it with `/`

The hub's rule is that every skill is reachable as `/<name>`. Because this tool has no `/<name>`, the hub keeps the body and changes the wrapper.

This tool has no slash mechanism. It reads `GEMINI.md` as always-on context, so the skill body is loaded by topic rather than by an explicit `/` trigger.

See [invoking-with-slash.md](invoking-with-slash.md) for the full matrix and for
what to do when `/<name>` does not appear.

## Notes

- Nested `GEMINI.md` files are also read; use them for directory-specific rules.
- `GEMINI.md` is prepended, so every byte costs tokens on every turn. Keep the
  core small and reference the rest by path.
- `/memory show` is the fastest way to confirm what actually loaded.
