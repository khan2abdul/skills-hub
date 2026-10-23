# Claude Code

> Paste this whole file into Claude Code and say: **"set this up for me."**

## What Claude Code reads

Claude Code discovers skills as directories containing `SKILL.md`:

| Scope | Path | Notes |
|---|---|---|
| Project | `<project>/.claude/skills/<name>/SKILL.md` | committed with the repo |
| User | `~/.claude/skills/<name>/SKILL.md` | available in every project |

The `name:` in frontmatter must match the directory name. Claude Code also reads
`CLAUDE.md` at the project root for always-on instructions.

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

Pick one scope. User scope is best if you want these everywhere.

```powershell
# --- user scope: available in every project ---
$dst = "$HOME/.claude/skills"
New-Item -ItemType Directory -Force -Path $dst | Out-Null
Get-ChildItem "$hub/skills" -Directory | ForEach-Object {
  Copy-Item $_.FullName -Destination (Join-Path $dst $_.Name) -Recurse -Force
}
```

```powershell
# --- project scope: committed with this repo only ---
$dst = ".claude/skills"
New-Item -ItemType Directory -Force -Path $dst | Out-Null
Get-ChildItem "$hub/skills" -Directory | ForEach-Object {
  Copy-Item $_.FullName -Destination (Join-Path $dst $_.Name) -Recurse -Force
}
```

Symlink instead of copy if you want live updates (needs Developer Mode on Windows):

```powershell
$dst = "$HOME/.claude/skills"
New-Item -ItemType Directory -Force -Path $dst | Out-Null
Get-ChildItem "$hub/skills" -Directory | ForEach-Object {
  New-Item -ItemType SymbolicLink -Path (Join-Path $dst $_.Name) -Target $_.FullName
}
```

## Verify the install

```powershell
Get-ChildItem "$HOME/.claude/skills" -Directory | ForEach-Object {
  $f = Join-Path $_.FullName 'SKILL.md'
  $n = if (Test-Path $f) { (Select-String -Path $f -Pattern '^name:' | Select-Object -First 1).Line } else { 'MISSING SKILL.md' }
  "{0,-32} {1}" -f $_.Name, $n
}
```

Every row must show a `name:` equal to the directory. Then restart Claude Code
(`/exit`, then relaunch) — skills are scanned at startup.

## Optional: always-on index

Skills are on-demand. If you also want the router always loaded, copy:

```powershell
Copy-Item "$hub/MASTER_ROUTING.md" -Destination "./CLAUDE.md" -Force
```

Keep `CLAUDE.md` short. It is paid for on every single turn.

## Recommended subset

Claude Code handles a large catalog well, but start with these and add on demand:

`interview-me-properly`, `write-the-spec`, `break-into-tasks`,
`build-it-test-first`, `debug-this-code`, `review-my-code`, `prove-it-works`,
`write-less-code`, `trim-my-output`

## Uninstall

```powershell
Get-ChildItem "$HOME/.claude/skills" -Directory |
  Where-Object { Test-Path "$hub/skills/$($_.Name)" } |
  Remove-Item -Recurse -Force
```

## Invoking it with `/`

The hub's rule is that every skill is reachable as `/<name>`. `verify.ps1` fails the build when a skill cannot be invoked that way.

This tool has native skill discovery. `~/.claude/skills/<name>/SKILL.md` is exposed as `/<name>`; no wrapper needed.

See [invoking-with-slash.md](invoking-with-slash.md) for the full matrix and for
what to do when `/<name>` does not appear.

## Notes

- Claude Code reads `SKILL.md` bodies on demand — catalog cost is only the
  `description` line of each skill. Long descriptions cost you on every turn.
- `disable-model-invocation: true` hides a skill from the model but keeps it
  user-invocable via `/name`.
- If a skill seems missing, check the directory name equals the frontmatter
  `name:` and is kebab-case.
