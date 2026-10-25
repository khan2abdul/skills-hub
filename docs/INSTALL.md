# Install

One line installs everything: the 42 skills, the writing style, and the links
each AI tool reads.

**Runtime:** the hub needs Python 3.11+. `diagram-the-system` also needs Node.js
18+ and Chrome, Chromium or Edge for its browser gate.

## Windows

```powershell
irm https://raw.githubusercontent.com/khan2abdul/skills-hub/main/install.ps1 | iex
```

## Linux and macOS

```sh
curl -fsSL https://raw.githubusercontent.com/khan2abdul/skills-hub/main/install.sh | sh
```

## What the installer does

Four steps. The installer itself writes no style text; it hands every write to
`bootstrap.py`, so all three platforms run the same code.

| Step | Action |
|---|---|
| 1 | Find Python 3.11 or newer. |
| 2 | If it is missing, offer to install it for your user only. No admin. |
| 3 | Download the hub to `%LOCALAPPDATA%\skills-hub` (Windows) or `~/.local/share/skills-hub` (Linux, macOS). |
| 4 | Run `bootstrap.py`, which prints each path it writes and asks once. |

The installer needs no administrator rights on Windows or macOS. Linux may ask
for your password only if you choose to install Python with your package
manager.

## What gets written

| Tool | Style file | Skills |
|---|---|---|
| Claude Code | `~/.claude/CLAUDE.md` (between markers) | `~/.claude/skills/` |
| Codex | `~/.codex/AGENTS.md` (between markers) | `~/.agents/skills/` (shared with Cursor) |
| Gemini CLI | `~/.gemini/GEMINI.md` (between markers) | — |
| DSH | `~/.dsh/AGENTS.md` (between markers) | none: reports `wired` or `not wired` for `customSkillDirs` |
| Kilo | `~/.kilocode/rules/writing-style.md` (whole file) | adds the hub to `skills.paths` in `~/.config/kilo/kilo.json` |
| Cline | `~/Documents/Cline/Rules/writing-style.md` (whole file) | `~/.cline/skills/` |
| Kiro | `~/.kiro/steering/writing-style.md` (whole file) | `~/.kiro/skills/` |
| Windsurf | `~/.codeium/windsurf/memories/writing-style.md` (whole file) | — |
| Cursor | none: one manual paste, printed at the end | `~/.cursor/skills/` and `~/.agents/skills/` |

A `block` target keeps your own text and only manages the lines between the
markers. A `file` target is owned whole by the hub.

## The other commands

```sh
python tools/bootstrap.py --check       # report drift, exit 1 if any
python tools/bootstrap.py --dry-run     # print the plan, write nothing
python tools/bootstrap.py --update      # re-apply every target and re-link
python tools/bootstrap.py --uninstall   # remove only what this tool wrote
python tools/bootstrap.py --only cursor,kiro
python tools/bootstrap.py --all         # every known tool, installed or not
```

## Cursor needs one paste

Cursor keeps User Rules in its settings, not in a file the installer can write.
The run prints the style text and the click path:

```
Cursor Settings -> Rules -> User Rules
```

`--check` reports this as `manual`, not as drift, so it does not fail the run.

## Uninstall

```sh
python tools/bootstrap.py --uninstall
```

It removes only what it can prove it wrote:

- The managed block is cut out; your text above and below it stays.
- A `writing-style.md` the hub wrote is deleted. One you wrote, or one you added
  text to, is kept and reported as `kept`.
- A skill entry is removed only when it is a link into the hub. A real folder of
  your own stays, even at a skill name.
- The Kilo config and the hub folder are never deleted.

## Maintainer flow

The installer never runs this. It is for changing the hub itself.

```sh
python tools/refresh.py
```

It clones the nine sources, rebuilds the bodies, proves each one against its
upstream, then rewrites `COVERAGE.md`, `RATING.md`, `RATING.json` and `SKILLS.md`.

A machine with no `repos/` can still install. It cannot prove the bodies until
`refresh.py` runs, and `verify.py` says so rather than failing silently.

## Keeping up to date

[CHANGELOG.md](../CHANGELOG.md) records what changed in each version. Read it
before you upgrade an install. A line marked **re-run** means you must run
`python tools/bootstrap.py --update` after pulling the new version, because the
target paths or the style text changed.
