# Any other agent

> **Runtime note:** the hub needs Python 3.11+. `diagram-the-system` also needs Node.js 18+ and Chrome, Chromium or Edge for its browser gate. `design-to-motion` needs a Figma token, headless Chrome and ffmpeg.

> Paste this whole file into any coding agent and say: **"set this up for me."**

## 0. Find the hub

Everything below uses `$hub`. Resolve it once:

```bash
$hub = $env:SKILLS_HUB
if (-not $hub) {
  $d = Get-Item .
  while ($d -and -not (Test-Path (Join-Path $d.FullName 'skills-hub/tools/verify.py'))) { $d = $d.Parent }
  if ($d) { $hub = Join-Path $d.FullName 'skills-hub' }
}
if (-not $hub -or -not (Test-Path "$hub/skills")) { $hub = Read-Host 'Path to your skills-hub checkout' }
if (-not (Test-Path "$hub/skills")) { throw "no skills/ under $hub" }
```

## First: find out what it reads

Before installing anything, determine the mechanism. Ask the agent, or check its
docs, for which of these it supports:

| Mechanism | Looks like | What to do |
|---|---|---|
| Skill directory | scans `<dir>/<name>/SKILL.md` | point it at `$hub/skills` — no conversion |
| Rules directory | reads every file in `.X/rules/` | convert to that format, keep bodies intact |
| Single context file | `AGENTS.md`, `GEMINI.md`, `CLAUDE.md` | small core inline, rest as path index |
| Extension/plugin | manifest + commands | package the hub as an extension |
| MCP tool | exposes tools to the model | no skills concept — use a context file |

If the agent has a **skill directory**, you are done — just point at it:

```bash
# example: an agent that scans ~/.myagent/skills/
$dst = "$HOME/.myagent/skills"
New-Item -ItemType Directory -Force -Path $dst | Out-Null
Get-ChildItem "$hub/skills" -Directory |
  ForEach-Object { Copy-Item $_.FullName -Destination (Join-Path $dst $_.Name) -Recurse -Force }
```

## Generic conversion: keep the body, swap the wrapper

Every other mechanism reduces to this. **Never edit the body.**

```bash
function ConvertTo-AgentRule {
  param(
    [string]$SkillName,
    [string]$OutFile,
    [string]$Frontmatter = ""   # e.g. "trigger: model_decision`ndescription: ..."
  )
  $src = "$hub/skills/$SkillName/SKILL.md"
  if (-not (Test-Path $src)) { Write-Warning "missing $SkillName"; return }
  $raw  = [System.IO.File]::ReadAllText($src)
  # strip only the SKILL.md frontmatter block
  $body = [regex]::Replace($raw, '\A---\r?\n.*?\r?\n---\r?\n', '', 'Singleline')
  if ($Frontmatter) {
    $out = "---`n$Frontmatter`n---`n`n$body"
  } else {
    $out = $body
  }
  Set-Content -Path $OutFile -Value $out -Encoding UTF8
  Write-Host "wrote $OutFile ($((Get-Item $OutFile).Length) B)"
}

# example
ConvertTo-AgentRule -SkillName 'debug-this-code' -OutFile './rules/debug.md'
```

## Choose the subset by capability, not by count

Installing everything is the failure mode. Pick one per phase you actually use:

| Phase | Pick one |
|---|---|
| Understand | `interview-me-properly` or `discuss-on-new-idea` |
| Spec | `write-the-spec` |
| Slice | `break-into-tasks` |
| Build | `build-it-test-first` |
| Debug | `debug-this-code` |
| Review | `review-my-code` |
| Prove | `prove-it-works` |
| Restrain | `write-less-code` or `trim-my-output` |

## Verify the result

```bash
Get-ChildItem "$hub/skills" -Directory | ForEach-Object {
  $f = Join-Path $_.FullName 'SKILL.md'
  $ok = Test-Path $f
  "{0,-34} {1}" -f $_.Name, $(if ($ok) { 'vendored' } else { 'MISSING' })
}
```

Then confirm with the agent: ask it to name its loaded rules. If it cannot, the
install did not take.

## Rules that hold for every tool

1. **Body text is never edited.** Only the wrapper for that tool changes.
2. **Always-on content is paid on every turn.** Keep it under ~3 skills.
3. **A missing file is silent.** Every tool fails by loading nothing, not by
   erroring. Always verify by asking the agent what it loaded.
4. **Names are the interface.** If a user cannot guess the skill name from the
   task, the name is wrong, not the docs.

## Invoking it with `/`

The hub's rule is that every skill is reachable as `/<name>`. Because this tool has no `/<name>`, the hub keeps the body and changes the wrapper.

This tool depends on the tool. Find out what it reads first, then apply the same rule: the body does not change, only the wrapper.

See [invoking-with-slash.md](invoking-with-slash.md) for the full matrix and for
what to do when `/<name>` does not appear.
