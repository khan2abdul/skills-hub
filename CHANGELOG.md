# Changelog

Every change that a user of this repo can notice gets a line here. The format is
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## How to add an entry

1. Add the line under `## [Unreleased]`, in the right group.
2. Write it for the person who installs the hub, not for the person who wrote the
   patch. Say what changed and what they must do, if anything.
3. When a batch of work is ready to ship, rename `## [Unreleased]` to the new
   version and date, then add a fresh empty `## [Unreleased]` above it.

Groups, in this order: `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`,
`Security`.

A line that changes behaviour for an existing install MUST say so, because the
hub writes into files the user owns. Use the words **re-run** or **no action**.

## [Unreleased]

## [0.1.0] - 2026-10-23

The first version: one-command install of the 41 skills and the writing style.

### Added

- **41 skills**, one per capability, harvested from nine upstream repos and
  published under verb-first names. 17 are verbatim copies, 23 are compositions
  of verbatim excerpts, and 1 is authored (`route-to-the-right-skill`).
  Every body has a `PROVENANCE.md` with a per-block sha256.
- **The writing style** in `style/WRITING-STYLE.md`, as the only copy. The hub
  writes it into each tool: a marked block for Claude Code, Codex, Gemini CLI and
  DSH, and a whole file for Kilo, Cline, Kiro and Windsurf.
- **Skill links.** `~/.claude/skills`, `~/.agents/skills`, `~/.cline/skills`,
  `~/.cursor/skills` and `~/.kiro/skills` hold junctions into the hub, so a tool
  loads a body only when it uses it. Nothing copies 41 skill bodies.
- **`install.ps1`** and **`install.sh`**: find Python 3.11+, offer to install it
  for the current user only, download the hub, then hand off once to
  `bootstrap.py`. Neither asks for admin and neither writes style text itself.
- **`bootstrap.py`** with `--check`, `--dry-run`, `--update`, `--uninstall`,
  `--only`, `--all` and `--home`. Every write prints the path first and asks once.
- **`tools/refresh.py`**: the maintainer flow in one command. Clone, harvest,
  verify, coverage, rate, catalog. It stops at the first failure.
- **`tools/verify.py`** now proves the writing style too, and prints
  `OK: writing style is consistent`.
- **Docs.** `docs/INSTALL.md`, plus one install page per tool in `setup/`.

### Fixed

- `--uninstall` could delete a `writing-style.md` the user had edited. Ownership
  is now proved from the text before any delete, and an edit makes the file the
  user's.
- Install then uninstall changed the trailing bytes of a file it managed. The
  round trip now returns the file byte for byte.
- `--update` wrote without asking. It now passes the same confirm gate as any
  other write, and refuses when there is no terminal.
- `Path.is_junction` needs Python 3.12, but the hub promises 3.11. On 3.11 every
  skill link read as "not ours", so a repair could miss it.
- `install.sh` read the confirm answer from stdin, but `curl … | sh` makes stdin
  the script itself, so it could eat its own lines.

### Known limits in this version

- Cursor keeps User Rules in its settings, not in a file. The run prints the text
  and the click path, and `--check` reports `manual` rather than drift.
- Cline's target is hardcoded as `Documents/Cline/Rules/`. A non-English Windows
  profile may put that folder elsewhere.
- A machine with no `repos/` can install, but cannot prove the skill bodies until
  `refresh.py` runs.
- Install then uninstall deletes a style file the user created empty. Nothing on
  disk records which run made a file.
