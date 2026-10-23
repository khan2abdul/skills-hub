# Cline

> Paste this whole file into Cline's chat and say: **"set this up for me."**

## What Cline reads

| Scope | Path | Notes |
|---|---|---|
| Project rules | `.clinerules/` directory | every `.md` inside is loaded |
| Project rules (single) | `.clinerules` file | older style |
| Global rules | `~/Documents/Cline/Rules/` | Windows: `%USERPROFILE%\Documents\Cline\Rules` |

Cline loads **all** rule content. There is no frontmatter-driven lazy loading and
no skill catalog — `.clinerules/` content is prepended to context.

## The translation rule

This is the tool where over-installing hurts most. Cline concatenates rules, so
10 full skill bodies is thousands of tokens on every request.

**Install 2–3. Reference the rest by path.**

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
New-Item -ItemType Directory -Force -Path ".clinerules" | Out-Null

# keep this list small — these load on every request
$always = @('write-less-code','prove-it-works','trim-my-output')

foreach ($n in $always) {
  $src = "$hub/skills/$n/SKILL.md"
  if (-not (Test-Path $src)) { Write-Warning "missing $n"; continue }
  $raw  = [System.IO.File]::ReadAllText($src)
  $body = [regex]::Replace($raw, '\A---\r?\n.*?\r?\n---\r?\n', '', 'Singleline')  # strip skill frontmatter
  Set-Content ".clinerules/$n.md" $body -Encoding UTF8
}
```

Add an index so Cline knows the rest exist without loading them:

```bash
$head = @(
  '# Available procedures'
  ''
  'Full skill bodies live in $hub/skills/<name>/SKILL.md.'
  'When a task matches, read that file first, then follow it.'
  ''
)
$idx = ($head -join "`n") + "`n"

Get-ChildItem "$hub/skills" -Directory | ForEach-Object {
  $f = Join-Path $_.FullName 'SKILL.md'
  if (Test-Path $f) {
    $d = (Select-String -Path $f -Pattern '^description:' | Select-Object -First 1).Line
    $d = $d -replace '^description:\s*',''
    $idx += "- $($_.Name) - $d`n"
  }
}
Set-Content ".clinerules/_index.md" $idx -Encoding UTF8
```

## Verify

```bash
Get-ChildItem ".clinerules" | ForEach-Object {
  "{0,-32} {1,6} B" -f $_.Name, $_.Length
}
```

Then in Cline, open the Rules panel and confirm the files are attached.

## Recommended subset

`write-less-code`, `prove-it-works`, `trim-my-output`

Everything else: path reference only.

## Invoking it with `/`

The hub's rule is that every skill is reachable as `/<name>`. Because this tool has no `/<name>`, the hub keeps the body and changes the wrapper.

This tool has no slash mechanism. It reads rules, so the skill body is loaded by topic rather than by an explicit `/` trigger.

See [invoking-with-slash.md](invoking-with-slash.md) for the full matrix and for
what to do when `/<name>` does not appear.

## Notes

- `.clinerules` as a **directory** is the current format; a single
  `.clinerules` **file** is legacy. Prefer the directory.
- Cline has no `name:` matching requirement, so the body can be used as-is once
  frontmatter is stripped.
- Global rules live outside the repo — useful for a shared baseline, but they do
  not travel with the project, so a teammate will not get them.
