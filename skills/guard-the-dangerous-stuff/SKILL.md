---
name: guard-the-dangerous-stuff
description: Safety guardrails before running a destructive command: recursive deletes, DROP/TRUNCATE, force-push, git reset --hard, kubectl delete, docker prune, and the PowerShell/cmd equivalents. Use before any command that can destroy data, uncommitted work, or production state. Apply the checklist by hand - the upstream hook it shipped with is not installed here, so this is a written procedure, not an automatic intercept.
---

# Guard The Dangerous Stuff

Composed from verbatim excerpts of 7 upstream skills. Each section is
byte-identical to its source; provenance and hashes are in PROVENANCE.md.
Do not paraphrase a section when editing - change the compose spec instead.

## Before you run it

<!-- source: migration |  | sha256: f7c31e0e9f59cd598e54e0c853d978107e62e21029ccc7ab0dc209b6dfbccbec -->

Map current readers, writers, data shape, compatibility window, and ownership before editing.

- Define forward path and rollback path.
- Preserve existing data; make destructive steps explicit and separately authorized.
- Keep mixed-version operation safe where rollout can overlap.
- Sequence expand, migrate, verify, then contract when applicable.
- Make retries idempotent and partial failure observable.
- Verify old and new paths at required transition stages.

Stop after requested stage passes; do not perform later destructive contraction implicitly.

<!-- source: deprecation-and-migration | ## The Deprecation Decision | sha256: bcf3010490169c9151213919bf26cda852095a939546f406c8ee20189cf8f462 -->

## The Deprecation Decision

Before deprecating anything, answer these questions:

```
1. Does this system still provide unique value?
   → If yes, maintain it. If no, proceed.

2. How many users/consumers depend on it?
   → Quantify the migration scope.

3. Does a replacement exist?
   → If no, build the replacement first. Don't deprecate without an alternative.

4. What's the migration cost for each consumer?
   → If trivially automated, do it. If manual and high-effort, weigh against maintenance cost.

5. What's the ongoing maintenance cost of NOT deprecating?
   → Security risk, engineer time, opportunity cost of complexity.
```

<!-- source: careful | ## What's protected | sha256: 64767c8b0aedba6f28e501a5878b6fa9f78a6f2e91b4ebc002300e2aca864397 -->

## What's protected

| Pattern | Example | Risk |
|---------|---------|------|
| `rm -rf` / `rm -r` / `rm --recursive` | `rm -rf /var/data` | Recursive delete |
| `DROP TABLE` / `DROP DATABASE` | `DROP TABLE users;` | Data loss |
| `TRUNCATE` | `TRUNCATE orders;` | Data loss |
| `git push --force` / `-f` | `git push -f origin main` | History rewrite |
| `git reset --hard` | `git reset --hard HEAD~3` | Uncommitted work loss |
| `git checkout .` / `git restore .` | `git checkout .` | Uncommitted work loss |
| `kubectl delete` | `kubectl delete pod` | Production impact |
| `docker rm -f` / `docker system prune` | `docker system prune -a` | Container/image loss |

<!-- source: careful | ## PowerShell and cmd (Windows) | sha256: b7c5bcb1b42d8135e3f93d535e015f4826f35cd744b52cdbb1d5889d71fd2eb0 -->

## PowerShell and cmd (Windows)

The hook also checks the PowerShell tool (Claude Code's main Windows shell)
and any `pwsh`/`powershell`/`cmd` launched from Bash. Matching ignores case,
covers aliases in command position, accepts parameter prefixes (`-r`, `-fo`)
and strips cmd `^` escapes. All rows above apply there too.

| Pattern | Example |
|---------|---------|
| `Remove-Item`/`rm`/`ri`/`del`/`erase`/`rd`/`rmdir` + `-Recurse` or `-Force` | `gci \| ri -r -fo` |
| cmd `rd /s`, `rmdir /s`, `del /s`, `erase /s` | `cmd /c rd /s /q C:\proj` |
| `Format-Volume`, `Clear-Disk`, `Clear-Content`, `[IO.Directory]::Delete`, `[IO.File]::Delete` | `Clear-Disk -Number 1` |
| `-EncodedCommand`, `iex`, `Start-Process` of a shell, `& $cmd` (can't be inspected) | `irm $url \| iex` |

**Best-effort on PowerShell.** String matching can't see a command built at
runtime. For a hard stop, add Claude Code permission deny rules, which parse
PowerShell and its aliases: `"deny": ["PowerShell(Remove-Item *)"]` in
`.claude/settings.json`. The hook runs through `bash`, so Windows needs Git Bash.

<!-- source: careful | ## Safe exceptions | sha256: d29f5f06c335699da907a194259b1d41fd73ce16e68673c164812e6d65e4cef6 -->

## Safe exceptions

These patterns are allowed without warning:
- `rm -rf node_modules` / `.next` / `dist` / `__pycache__` / `.cache` / `build` / `.turbo` / `coverage`

<!-- source: careful | ## HIGH tier (hard deny) | sha256: dcfe7589f3e29f7175cf919c64f4e32df6b0b754d0f48445fbd19a1936be532d -->

## HIGH tier (hard deny)

Two catastrophic shapes are **denied**, not asked: `rm -r`/`-R` of exactly
`/`, `~`, or `$HOME`, and force-push to the repo's **default branch**. SIMPLE
commands only (no `;`, `&&`, `||`, `|`, newline) — compound shapes fall
through to the MEDIUM ask; `--force-with-lease` is never HIGH. A best-effort
advisory hard-stop, not a policy boundary: the escape hatch is ending the
opt-in, session-scoped /careful session.

<!-- source: careful | ## Project patterns (additive only) | sha256: edaf8de1042be573214df41f6a052ce7d59507bd95ab66cf9d7c862b6229b0d5 -->

## Project patterns (additive only)

Add warn rules — one POSIX ERE per line, `#` comments OK — in
`~/.gstack/careful-patterns.txt` (global) or
`~/.gstack/projects/<slug>/careful-patterns.txt` (per-project). Consulted
after the built-in families, so config can only ADD rules, never suppress a
baseline warning. Invalid regex lines are skipped.

To deactivate, end the conversation or start a new one. Hooks are session-scoped.

