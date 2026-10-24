# M001: One-command install of 41 skills plus the writing style

**Vision:** A person on a new machine runs one line and gets all 41 hub skills
plus one writing style inside each AI tool they use. No clone step, no path
editing, no reading nine setup pages. The style lives once in the repo, and the
maintainer flow stays separate.

## Success Criteria

- A machine with no Python and no hub installs both from one line, with no admin
  rights on Windows or macOS, and prints a per-target result.
- All 41 skills are discoverable in Cursor, Kiro, Claude Code, Cline, Codex and
  Kilo Code after install, without copying a second physical tree.
- The writing style is present in every detected tool, and `--check` exits 1
  after any installed copy is edited by hand.
- A second run writes no bytes and needs no network.
- `--uninstall` leaves every file it did not create byte-identical.
- The user's existing `~/.dsh/AGENTS.md` style section becomes one managed block,
  with no duplicated copy beside it.
- `python tools/hub.py` still prints `HUB HEALTHY`.

## Key Risks / Unknowns

- **The user's live rules file already contains the style text, unmarked.** A
  naive append duplicates it; a naive replace deletes hand-written rules above
  it. This is the only case that can damage existing user content. Retired by
  S01.
- **Skills must be one physical copy.** A copy per tool means nine trees that
  drift, and `--update` cannot refresh them together. A link that fails silently
  (Windows without Developer Mode) would leave a tool with no skills. Retired by
  S03.
- **Three setup pages state the opposite of vendor docs.** Cursor, Kiro and Cline
  pages say their tool has no skills directory. A wrong page makes the install
  look broken. Retired by S06.
- **Detection cannot use `Get-Command`.** Measured: only `dsh` resolves on
  `PATH`; the other eight are config folders. A binary-based check detects
  nothing. Retired by S02.

## Proof Strategy

- Untracked-file safety → retire in S01 by proving a real unmarked style section
  becomes one managed block, and the rules above it stay byte-identical.
- One-copy skills → retire in S03 by proving each detected tool's skills folder
  holds a junction to `<hub>/skills`, and a link failure reports `copied`.
- Stale setup pages → retire in S06 by proving no page claims a tool lacks
  skills that its vendor docs list.
- Detection accuracy → retire in S02 by running detection on this machine and
  matching the measured five-present/four-absent result.

## Verification Classes

- Contract verification: `tools/test_bootstrap.py` unit tests on a temp home;
  `verify.py` style check; `Parser::ParseFile` and `bash -n` on the installers.
- Integration verification: a real run into a temp home, and a real run against
  this machine's live profile for the DSH untracked case.
- Operational verification: second-run idempotence, `--update` replacing a stale
  hub, `--uninstall` removing only owned files.
- UAT / human verification: Cursor shows the 41 skills and accepts the pasted
  User Rule; each tool restarted and asked to name a skill.

## Milestone Definition of Done

- All six slice deliverables are complete.
- The link engine, the marker engine and the installer call each other correctly.
- `install.ps1` exists and is exercised end-to-end into a temp home.
- Success criteria are re-checked against live behaviour, not just file contents.
- `python tools/test_bootstrap.py` passes and touches no real profile.

## Requirement Coverage

- Covers: style source, marker engine, eight style targets, six skill targets,
  detection, confirm prompt, installers, uninstall, verify check, setup fixes.
- Partially covers: Cursor global style, which is one manual paste by design.
- Leaves for later: Cursor Cloud Agent skill sync.
- Orphan risks: a localised Windows `Documents` folder may move Cline's target.
  Bootstrap prints the resolved path, so the miss is visible; no slice can fix it.

## Slices

- [x] **S01: Style source, marker engine, DSH target** `risk:high` `depends:[]`
  > After this: `bootstrap.py --only dsh` turns the unmarked style section in a
  > temp-home copy of `AGENTS.md` into one managed block, keeps every line above
  > and below it byte-identical, and a second run writes 0 bytes.
- [x] **S02: Detection, plan, confirm, four block targets** `risk:medium` `depends:[S01]`
  > After this: a bare `bootstrap.py --detect` lists the five tools present on
  > this machine and skips the four absent ones, and a confirmed run writes one
  > style block into Claude, Codex, Kilo and Gemini targets.
- [x] **S03: Skill links, Kilo JSON, DSH detect** `risk:high` `depends:[S02]`
  > After this: each detected tool's skills folder holds 41 junctions into
  > `<hub>/skills`, `~/.agents/skills` is written once and shared, the Kilo JSON
  > gains a validated `skills.paths`, and DSH reports `wired` or `not wired`
  > without editing YAML.
- [x] **S04: Four owned-file targets, Cursor print** `risk:low` `depends:[S02]`
  > After this: Kiro, Kilo rules, Cline and Windsurf each hold the body in a file
  > with no markers, and Cursor prints the paste text plus the click path and
  > reports `manual` in `--check`.
- [x] **S05: Uninstall and update** `risk:high` `depends:[S03,S04]`
  > After this: `--uninstall` removes only junctions whose target is inside the
  > hub and only blocks it created, leaving a user file beside them
  > byte-identical; `--update` refreshes the hub and re-links.
- [x] **S06: Installers, verify check, refresh, setup fixes** `risk:medium` `depends:[S03,S05]`
  > After this: `install.ps1` on a clean temp profile installs Python path, hub
  > and style end-to-end after one confirm; `verify.py` prints
  > `OK: writing style is consistent`; `refresh.py` runs the maintainer flow; the
  > Cursor, Kiro and Cline pages no longer claim their tools lack skills.

## Horizontal Checklist

Checked after S06, against the real code. An item is `[x]` only when it is proven
on this machine. A limit is left `[ ]` and named, never ticked with a caveat.

- [x] Every active requirement re-read against new code — still satisfied?
      All six slices re-read. The requirements that had drifted are recorded in
      STATE.md under the S05+S06 review gate, with the fix for each.
- [ ] No write path can delete a real directory or a user's own text.
      Holds for text and for directories: `test_unlink_skills_never_removes_a_real_directory`
      passes, and `_is_our_body` keeps a file with one line of the user's own.
      One exception remains: install then uninstall deletes a style file the user
      created **empty**, because nothing on disk records which run made a file.
      The code chooses removal over leaving an empty file behind.
- [x] Every write is atomic: temp file beside the target, then replace.
      `atomic_write` uses `tempfile.mkstemp(dir=path.parent)` then `os.replace`.
- [x] Removal only ever touches what the tool can prove it created.
      `unlink_skills` checks `_is_ours` then `_inside`; `remove_block` needs both
      marker lines present; `apply_file` needs `_is_our_body`.
- [ ] Windows path handling verified for `%LOCALAPPDATA%`, `%APPDATA%` and
      `~/Documents` under a non-English locale.
      `%LOCALAPPDATA%` is used by both installers and proven on this machine.
      The `%APPDATA%` and `~/Documents` parts are not proven: Cline's target is
      hardcoded as `Documents/Cline/Rules/`, so a localised profile may differ.
      Not verified on this machine.
- [x] Permissions: no step needs admin; the two confirm prompts exist.
      `install.ps1` and `install.sh` never elevate; `install.sh` prints `sudo`
      advice only. Prompts: the installer's Python offer, and `bootstrap.py`'s
      "Apply this?" gate.
- [x] Network failure during download leaves no partial hub.
      `install.ps1` cleans `$tmp` and `$zip` in `finally` and exits 1.
      `install.sh` sets `trap 'rm -rf "$tmp"' EXIT` and checks the unpacked hub
      before handing off.
- [x] `hub.py` health still passes after every slice.
      `HUB HEALTHY`, 41 skills: 17 verbatim, 23 composed, 1 authored.

## Boundary Map

### S01 → S02

Produces:
- `style/WRITING-STYLE.md`, the only copy of the body text.
- `apply_block(existing, block) -> str`: replace between markers, append when
  absent, return the input unchanged when equal.
- `--only <names>` and `--check` exit-code contract: 0 clean, 1 drift, 2 setup.

Consumes:
- nothing (first slice)

### S01 → S03

Produces:
- The atomic write helper, one temp file beside the target then replace.
- The target table shape: tool, path, kind, skill wiring.

Consumes:
- nothing

### S02 → S03

Produces:
- `--detect` output: one row per tool with `present` or `absent`.
- The confirm prompt contract: print the plan, ask, write nothing without `y`.

Consumes:
- the marker engine and `--only` from S01

### S02 → S04

Produces:
- The `block` kind, proven on four real targets.

Consumes:
- detection and the plan printer from S02

### S03 → S05

Produces:
- The link record: which junctions the tool created, so uninstall can remove
  exactly those and nothing else.
- `link_or_copy(src, dst) -> "linked" | "copied"`.
- Kilo JSON merge that validates before writing.

Consumes:
- the target table and atomic write

### S04 → S05

Produces:
- The `file` kind and its ownership rule: a `writing-style.md` the tool wrote may
  be deleted; anything else may not.

Consumes:
- the marker engine and `block` kind

### S03, S05 → S06

Produces:
- A working `bootstrap.py` with install, check, update and uninstall.

Consumes:
- every prior slice's contracts
