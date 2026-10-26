# Cline

> **Runtime note:** the hub needs Python 3.11+. `diagram-the-system` also needs Node.js 18+ and Chrome, Chromium or Edge for its browser gate.

> Paste this whole file into Cline's chat and say: **"set this up for me."**

## What Cline reads

Cline has **native skills**, so `bootstrap.py` links all 43 into
`~/.cline/skills/`. It also writes the writing style into the global rules
folder.

| Scope | Path | Loading |
|---|---|---|
| Skills | `~/.cline/skills/` | name and description always; body on demand |
| Project skills | `.cline/skills/`, `.clinerules/skills/`, `.claude/skills/` | same, per repo |
| Project rules | `.clinerules/` or `.cline/rules/` | always, unless `paths:` narrows it |
| Project rules (single) | `.clinerules` file | older style, always on |
| Global rules | the Documents folder's `Cline/Rules/` | always on |
| Other rule files | `.cursorrules`, `.windsurfrules`, `AGENTS.md`, `~/.agents/AGENTS.md` | always, when present |

On each request Cline sees the name and description of every skill. The body
loads only when the skill is triggered.

Cline's own numbers: about **100 tokens per skill** for that list. All 43 cost
about 4,300 tokens. Cline asks that a body stay under 5,000 tokens when it
loads. The largest hub body is 32 KB, so it costs more than that. A body costs
nothing until it loads.

That is the trade-off this page turns on: a skill is cheap at rest. A rule is
not.

## The translation rule

Cline joins every rule into the context, so ten rule files of skill bodies is
thousands of tokens on every request, in every project.

**Link all 43 skills. Add 2–3 rules at most.**

A linked skill costs its description. A rule costs its whole body, every time.

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

One command links the 43 skills and writes the global style file:

```bash
python "$hub/tools/bootstrap.py" --only cline
```

It prints every path it writes, and asks once before it writes.

Then check what it left:

```bash
python "$hub/tools/bootstrap.py" --only cline --check
```

The style file goes in the folder the shell calls Documents. `--check` prints
that full path, so read the line and do not assume `%USERPROFILE%\Documents`. On
Windows, OneDrive Known Folder Move changes the answer.

The hub owns `writing-style.md` in full. Any other rule file you keep in that
folder is left alone.

### Optional: rules that are always on

Do this only when you want 2–3 skill bodies in context for every request in a
repo. The 43 linked skills cover the rest.

```bash
New-Item -ItemType Directory -Force -Path ".clinerules" | Out-Null

# keep this list small — these load on every request
$always = @('write-less-code','prove-it-works','trim-my-output')

foreach ($n in $always) {
  $src = "$hub/skills/$n/SKILL.md"
  if (-not (Test-Path $src)) { Write-Warning "missing $n"; continue }
  $raw  = [System.IO.File]::ReadAllText($src)
  $body = [regex]::Replace($raw, '\A---\r?\n.*?\r?\n---\r?\n', '', 'Singleline')
  Set-Content ".clinerules/$n.md" $body -Encoding UTF8
}
```

Do not write an index file. Cline already lists every linked skill with its
description, so an index says the same thing twice.

### Keep a rule off most requests

A rule in `.clinerules/` can carry `paths:` frontmatter. Cline then activates it
only when a matching file is in context:

```markdown
---
paths:
  - "src/components/**"
---
# React components

When you change a component, keep the props typed and the state local.
```

A rule with no frontmatter is always on. That is the default, and the reason a
big rule file costs you on every request.

## Verify

```bash
python "$hub/tools/bootstrap.py" --only cline --check
```

It must print `OK` twice: once for `writing-style.md`, once for
`~/.cline/skills (43 skills)`. Then look in Cline:

| Where | What to see |
|---|---|
| Scale icon, left of the model selector, then **Rules** | `writing-style.md`, toggled on |
| Same icon, then **Skills** | 43 skills, toggled on |
| Chat input, type `/` | the skill names, for example `/write-less-code` |

## Recommended subset

- **Skills:** all 43. Leave them on.
- **Rules:** `write-less-code`, `prove-it-works`, `trim-my-output`.

If the list cost matters, turn off the skills you never use in the Skills tab. A
skill that is off costs nothing.

## Invoking it with `/`

The hub's rule is that every skill is reachable as `/<name>`. Cline has that
mechanism: type `/` in the chat input, then pick the skill. Cline loads that
`SKILL.md` and follows it.

A skill that is off in the Skills tab does not appear in `/`. When a name is
missing, check the toggle first.

See [invoking-with-slash.md](invoking-with-slash.md) for the full matrix and for
what to do when `/<name>` does not appear.

## Notes

- `.clinerules/` as a **directory** is the current format. `.cline/rules/` works
  the same way. A single `.clinerules` **file** is legacy.
- Cline also reads `.cursorrules`, `.windsurfrules` and `AGENTS.md`. That text
  enters the context too, so a repo with an old `.cursorrules` pays twice.
- Cline follows links in a skills folder: it accepts a directory, or a junction
  or symlink whose target is a directory. So `bootstrap.py` links and does not
  copy. Checked against 4.1.25.
- The skills parser is lenient. It takes `name` from the folder name when that
  key is absent. It ignores unknown keys such as `argument-hint`. The docs say
  `name` must match the directory name, and every hub skill does.
- Global rules live outside the repo. They are a good shared baseline, but they
  do not travel with the project, so a teammate will not get them.
- Global rules go in the folder the shell calls Documents. On Windows that is
  `[System.Environment]::GetFolderPath('MyDocuments')`. OneDrive Known Folder
  Move changes the answer. A write to `%USERPROFILE%\Documents` then lands in a
  folder Cline never reads.
