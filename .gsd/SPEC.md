# SPEC: write-clearly

Status: draft, awaiting approval
Written: 2026-10-24
Owner: Abdul
Module id: `write-clearly`
Revision: 3 (vendor-verified targets; skills by link on every tool that reads them)

## Objective

A new person wants 41 skills and 1 writing style inside the AI tool they already
use. They should not read a setup page, edit a path, or clone nine upstream
repos. One command does it.

## Verified vendor facts

Measured 2026-10-24. These replace the repo's assumptions, and three of them
contradict what `setup/` says today.

| Tool | Native user-level skills folder | Always-on style file | Source |
|---|---|---|---|
| Cursor | `~/.cursor/skills/`, `~/.agents/skills/`, and it reads `~/.claude/skills/` | User Rules = app UI only. Project `AGENTS.md` and `.cursor/rules/*.mdc` are files. | cursor.com/docs/skills, /docs/rules |
| Kiro | `~/.kiro/skills/` | `~/.kiro/steering/*.md` | kiro.dev/docs/skills, /docs/steering |
| Claude Code | `~/.claude/skills/` | `~/.claude/CLAUDE.md` | existing `setup/` |
| Cline | `~/.cline/skills/` | `~/Documents/Cline/Rules/` | docs.cline.bot/customization/skills |
| Codex CLI | `~/.agents/skills/` (symlinks followed) | `~/.codex/AGENTS.md` | learn.chatgpt.com/docs/build-skills |
| Kilo Code | `skills.paths` in `kilo.json` | `~/.kilocode/rules/` | existing `setup/` |
| Windsurf | none | `~/.codeium/windsurf/memories/` | existing `setup/` |
| Gemini CLI | none | `~/.gemini/GEMINI.md` | existing `setup/` |
| DeepSeek Harness | `customSkillDirs` in the profile patch | `~/.dsh/AGENTS.md` | existing `setup/` |

Three corrections the repo must carry:

1. **Cursor has native skills.** `setup/cursor.md` says "Cursor has **no skills
   directory**". That is now false. It reads four user-level folders.
2. **Kiro has native skills.** `setup/kiro.md` says "Kiro uses steering
   documents, not skills". It now has `~/.kiro/skills/`.
3. **Cline has native skills.** `setup/cline.md` sells `.clinerules/` only.
   `~/.cline/skills/` now exists.

One shared folder does most of the work: `~/.agents/skills/` is read by both
Cursor and Codex. Writing there once covers two tools.

Measured on this machine:

| Fact | Value |
|---|---|
| `~/.cursor` | absent: Cursor not installed |
| `~/.claude/skills` | present |
| `~/.dsh`, `~/.gemini`, `~/.config/kilo` | present |
| `~/.codex`, `~/.kiro`, `~/.kilocode`, `~/.codeium` | absent |
| Directory junction without admin | works (`mklink /J`, exit 0) |

## How skills get written

**One physical copy, linked in.** The hub's `skills/` folder stays the only copy
of the 41 bodies. Every tool gets a directory junction (Windows) or symlink
(POSIX) from its skills folder to `<hub>/skills/<name>`.

Why a link and not a copy:

- A copy duplicates 4.7 MB into nine folders, and a re-run must reconcile nine
  trees.
- A link means `--update` refreshes one folder and every tool sees the new body
  immediately.
- Codex documents that it follows symlinked skill folders. Cursor, Kiro and Cline
  scan the directory, so a junction or symlink is a directory to them.

A junction needs no admin on Windows. A copy is the fallback when a link fails:
the run reports `linked` or `copied` per tool, so a silent fallback cannot hide.

**Where each link goes:**

| Tool | Link target |
|---|---|
| Cursor | `~/.cursor/skills/<name>`, plus `~/.agents/skills/<name>` once |
| Codex CLI | `~/.agents/skills/<name>` (same link as Cursor) |
| Kiro | `~/.kiro/skills/<name>` |
| Claude Code | `~/.claude/skills/<name>` |
| Cline | `~/.cline/skills/<name>` |
| Kilo Code | `skills.paths` entry pointing at `<hub>/skills`, in `~/.config/kilo/kilo.json` |
| DeepSeek Harness | detect `customSkillDirs`; report, never edit YAML |
| Windsurf, Gemini | no skill mechanism: inline core bodies in the style block |

`~/.agents/skills/` is written once and shared. It is the cheapest target in the
set.

## How the writing style gets written

Three kinds, per target:

- `block`: shared file the user also edits. Markers, replace-in-place.
- `file`: file bootstrap owns whole. No markers.
- `print`: no file path. Print the text and the UI steps. Cursor User Rules.

| Tool | Style target | Kind |
|---|---|---|
| Kiro | `~/.kiro/steering/writing-style.md` | `file` |
| Claude Code | `~/.claude/CLAUDE.md` | `block` |
| Kilo Code | `~/.kilocode/rules/writing-style.md` | `file` |
| Codex CLI | `~/.codex/AGENTS.md` | `block` |
| DeepSeek Harness | `~/.dsh/AGENTS.md` | `block` |
| Gemini CLI | `~/.gemini/GEMINI.md` | `block` |
| Windsurf | `~/.codeium/windsurf/memories/writing-style.md` | `file` |
| Cline | `~/Documents/Cline/Rules/writing-style.md` | `file` |
| Cursor | none | `print` |
| Claude Code | plus `~/.claude/CLAUDE.md`, already above |

Managed region, in every `block` target:

```
<!-- skills-hub:writing-style:start -->
...style body...
<!-- skills-hub:writing-style:end -->
```

## How Cursor is handled

Four separate mechanisms. This is the most complex tool, so it gets its own rule.

1. **Skills: automatic.** Link all 41 into `~/.cursor/skills/`. Cursor documents
   discovery at startup, `/` invocation, and on-demand bodies. Nothing more to
   do. Because Cursor also reads `~/.agents/skills/` and `~/.claude/skills/`, a
   machine that already has Claude Code has Cursor skills for free.
2. **Style, per project: automatic.** Cursor reads `AGENTS.md` at the project
   root, and nested ones. Bootstrap writes a project file only when run with
   `--project`, because a user-level run must not write into the current
   directory.
3. **Style, global: one paste, once.** Cursor User Rules live in
   Customize → Rules, an app setting with no documented file. Bootstrap prints
   the exact text and the exact click path. `--check` reports `manual`. This is
   the one place a human must act.
4. **Everything else: not file-backed.** Cloud Agents do not copy local skills,
   so a user who uses Cursor in the cloud must either sync skills in the app or
   rely on project `AGENTS.md`. The README states this limit.

Why not write `~/Documents/Cursor/rules` or an internal DB: neither is
documented, and an undocumented path breaks silently on the next release. One
paste is honest, cheap, and verifiable by eye.

## The one command

```
Windows:       irm https://raw.githubusercontent.com/khan2abdul/skills-hub/main/install.ps1 | iex
Linux / macOS: curl -fsSL https://raw.githubusercontent.com/khan2abdul/skills-hub/main/install.sh | sh
```

### What runs, in order

`install.ps1` is PowerShell and it is the whole entry point. It does four things,
then hands off once.

| Step | Runs | Why |
|---|---|---|
| 1 | `Find-Python` | Probes `python`, then `py -3` for version 3.11+. |
| 2 | `Add-Python` | `winget install --scope user --id Python.Python.3.12`, after asking. No admin. |
| 3 | `Get-Hub` | Downloads the zip to `%LOCALAPPDATA%\skills-hub`, or reuses it. |
| 4 | `python <hub>\tools\bootstrap.py` | The one hand-off. bootstrap.py does every write. |

The hand-off is a single call. All tool logic lives in `bootstrap.py` so Windows,
Linux and macOS run the same code. `install.ps1` is about 120 lines: probing,
asking, downloading, unpacking, and calling one file.

### The exact PowerShell

```powershell
# 1. Python
$py = Find-Python
if (-not $py) { Add-Python; $py = Find-Python }

# 2. Hub
Get-Hub

# 3. Hand off. Every write happens here.
& $py.Exe @($py.Prefix) "$HubDir\tools\bootstrap.py"
```

### How the tool is chosen

`bootstrap.py` decides. `install.ps1` passes `--all`, `--only`, or nothing.

| Invocation | Result |
|---|---|
| `bootstrap.py` | detect the tools present, skip the absent ones |
| `bootstrap.py --all` | write every target, installed or not |
| `bootstrap.py --only cursor,kiro` | only those two |

Detection is measured, not guessed. Verified on this machine:

| Tool | Signal that fires | This machine |
|---|---|---|
| claude | `~/.claude` | FOUND |
| kilo | `~/.config/kilo/kilo.json` | FOUND |
| gemini | `~/.gemini` | FOUND |
| dsh | `~/.dsh` | FOUND |
| cline | `~/.cline` | FOUND |
| cursor | `~/.cursor` or `%LOCALAPPDATA%\Programs\Cursor\Cursor.exe` | absent |
| kiro | `~/.kiro` or `%LOCALAPPDATA%\Programs\Kiro\Kiro.exe` | absent |
| codex | `~/.codex` or `%APPDATA%\npm\codex.cmd` | absent |
| windsurf | `~/.codeium` or `%LOCALAPPDATA%\Programs\Windsurf` | absent |

No binary on `PATH` was found for any of the nine except `dsh`. Detection must
use config folders, not `Get-Command`, or it would find nothing.

### Permission: the user confirms before a write

The script never writes silently. Two gates:

1. **Before Python is installed.** It prints the exact winget command and asks
   `y/N`.
2. **Before any tool config is written.** `bootstrap.py --detect` prints the
   full plan, the script shows it, and asks `y/N`. A `--dry-run` run skips the
   question entirely.

The plan reads like this:

```
This will write:
  claude    ~/.claude/skills/           41 skills (link)
  claude    ~/.claude/CLAUDE.md         writing style (block)
  kilo      ~/.config/kilo/kilo.json    skills.paths
  kilo      ~/.kilocode/rules/          writing style (file)
  gemini    ~/.gemini/GEMINI.md         writing style (block)
  dsh       ~/.dsh/AGENTS.md            writing style (block)
  cline     ~/.cline/skills/            41 skills (link)
  cline     ~/Documents/Cline/Rules/    writing style (file)
  cursor    not detected                skipped
  ...
Apply this? [y/N]
```

### Proof the pieces work

Run on 2026-10-24 against the real repo and this machine:

| Check | Result |
|---|---|
| `Parser::ParseFile` on `install.ps1` | parse OK, 0 errors |
| Dot-source the script | silent, no side effect |
| `Find-Python` | detected `python` 3.14 |
| `Get-Hub` download and unpack | 1.9 MB, 41 skills present |
| Second `Get-Hub` | `Hub already present`, no network |
| Delete guard on a non-hub folder | refused, user file survived |

Two bugs were found by these tests and are now fixed, both worth recording:

1. A local variable named `$args` shadowed PowerShell's automatic variable, so
   detection failed and the script tried a real install. Never name a local
   `$args`.
2. The version probe used inner double quotes. PowerShell strips them when
   forwarding arguments, so Python saw `print(%d.%d % ...)` and exited 1. The
   probe now builds the string with `chr(46)` and has no quotes to strip.

The dot-source guard (`if ($MyInvocation.InvocationName -ne '.')`) is what stops
a test from running a real install.


## What no `repos/` means

The zip has `skills/` and `style/`, not `repos/`. An install copies nothing from
upstream, so it needs no provenance. The limit is stated, not hidden: on such a
machine `verify.py` cannot prove bodies. It exits 2 today; after this change it
adds one line saying installing does not need `repos/` and `tools/refresh.py`
restores the proof.

The maintainer command is separate: `python tools/refresh.py` clones the nine
sources, then runs harvest, verify, coverage, rate, catalog. It never runs from
the installer.

## Commands

```
install.ps1 | install.sh          # Python, zip, bootstrap
python tools/bootstrap.py         # install style + skills
python tools/bootstrap.py --check # report only, exit 1 on drift
python tools/bootstrap.py --dry-run
python tools/bootstrap.py --update
python tools/bootstrap.py --uninstall
python tools/bootstrap.py --project .   # also write ./AGENTS.md and ./.cursor/rules
python tools/bootstrap.py --only cursor,kiro
python tools/bootstrap.py --dir <hub>
python tools/refresh.py           # maintainer: sources + catalog
python tools/test_bootstrap.py
```

Exit codes: `0` clean, `1` drift or refusal, `2` setup problem.

`--uninstall` removes the block, deletes only the `writing-style.md` files it
owns, and removes only junctions whose target is inside the hub. It leaves real
directories, the Kilo JSON, and the hub folder alone.

## Project structure

```
install.ps1, install.sh   # thin: Python, zip, run bootstrap
style/WRITING-STYLE.md    # the one copy of the style text
tools/bootstrap.py        # targets, markers, link-or-copy, install, check, uninstall
tools/refresh.py          # maintainer flow
tools/test_bootstrap.py   # stdlib unittest, temp --home
tools/verify.py           # + style check, + the no-repos hint
setup/*.md                # corrected: Cursor, Kiro, Cline now have skills
docs/INSTALL.md           # the flow, both commands, what gets written
README.md                 # quick start becomes the one line
.gsd/SPEC.md
```

## Code style

Match the hub. Stdlib only, Python 3.11, `from __future__ import annotations`,
import `hubcommon as C`, read and write through `C.read_text`/`C.write_text`
because the repo is `-text` on purpose. `main(argv)` returns an int.

Marker engine, the only new logic:

```python
START = "<!-- skills-hub:writing-style:start -->"
END   = "<!-- skills-hub:writing-style:end -->"

def apply_block(existing: str, block: str) -> str:
    """Replace between the markers, append when absent, return unchanged when equal."""
```

Link helper:

```python
def link_or_copy(src: Path, dst: Path) -> str:
    """Create a junction/symlink at dst. Return 'linked', 'copied', or raise."""
```

Windows uses `mklink /J` through `subprocess` because `os.symlink` needs
Developer Mode there. POSIX uses `os.symlink`.

## Testing

`tools/test_bootstrap.py`, stdlib `unittest`, `tempfile` `--home`. No test
touches a real profile.

| Test | Asserts |
|---|---|
| `test_block_append` | Empty home gains the file between markers. |
| `test_block_replace_idempotent` | Second run is byte-identical. |
| `test_block_preserves_user_text` | Text around the markers survives. |
| `test_no_duplicate_block` | Two runs give one start marker. |
| `test_untracked_refused` | Style text without markers is reported, not duplicated. |
| `test_untracked_replaced` | `--replace-untracked` leaves one block. |
| `test_check_exit_codes` | Clean 0, drift 1. |
| `test_uninstall_removes_only_ours` | Block gone, user text stays, links stay. |
| `test_all_targets_written` | Empty home gains every file target. |
| `test_link_falls_back_to_copy` | A blocked link yields `copied` and the files are present. |
| `test_agents_skills_written_once` | One `~/.agents/skills` tree, shared by Cursor and Codex. |
| `test_style_source_missing` | No `style/` exits 2 with one message. |
| `test_atomic_write` | Read-only target errors cleanly, old file intact. |

`verify.py` gains one check: each existing `block` target must equal the style
body. A missing target is `SKIP`.

Shell parse checks: `bash -n install.sh`, and the PowerShell
`Parser::ParseFile` for `install.ps1`.

## Boundaries

**Always:** read the body from `style/WRITING-STYLE.md`; write atomically; keep
every byte outside the managed region; print each resolved path; keep `setup/`
and `README.md` true.

**Ask first:** changing the style text; adding a target; making `verify.py` fail
on a missing target; any `sudo` step.

**Never:** write inside `skills/`, `manifest.yml`, or a `PROVENANCE.md`; delete
text outside the markers; edit YAML; hand-merge JSON without validating it;
download an `.exe` from a host other than python.org; run `refresh.py` from the
installer; remove a real directory during uninstall.

## Success criteria

1. On a machine with no Python and no hub, one line installs both and prints a
   per-target result, with no admin on Windows or macOS.
2. A machine with Python finishes in under 30 seconds on a warm network.
3. A second run writes no bytes, touches no network, prints `unchanged`.
4. `--check` exits 0 clean and 1 after any installed block is edited.
5. `--uninstall` leaves every file it did not create byte-identical.
6. `python tools/verify.py` prints `OK: writing style is consistent`, and its
   no-`repos/` failure mentions that installing does not need them.
7. `python tools/refresh.py` clones, verifies, and rewrites `COVERAGE.md`,
   `RATING.md`, `RATING.json`, `SKILLS.md`.
8. `python tools/test_bootstrap.py` passes 13 tests without touching a real
   profile.
9. `python tools/hub.py` still prints `HUB HEALTHY`.
10. Cursor shows all 41 skills after install, and the pasted User Rule is
    one paste, not eight.

## Open questions

None blocking.

Recorded limits:

- Cursor User Rules need one manual paste. No documented file path exists.
- Cursor Cloud Agents do not copy local skills.
- A localised Windows `Documents` folder may move Cline's target; the run prints
  the resolved path.
- A machine with no `repos/` cannot prove bodies until `refresh.py` runs.

## Further notes

The style text also lives in `~/.dsh/AGENTS.md` today, hand-written. The hub file
becomes the only copy. Bootstrap reports that file as unmanaged and does not
duplicate it; `--replace-untracked` wraps it in place.

Three `setup/*.md` pages claim their tool has no skills directory. They are
wrong now. Correcting them is part of this change, not a follow-up.
