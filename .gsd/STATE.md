# State

Current: M002 Archify added (2026-10-25). 42 skills, 188 upstream, HUB HEALTHY.

Milestone: M001 - one-command install of 41 skills plus the writing style
Slice: S06 of 6 (M001 complete)
Status: S05 and S06 built. Review gate pending on the S05+S06 diff.

## S05: uninstall and update

`--uninstall` removes only what the tool can prove it made.

| What | Rule | Test |
|---|---|---|
| `block` target | Cut out between the markers; every other byte stays. A file that held only the block is deleted. | `test_uninstall_removes_the_block_and_keeps_user_text` |
| `file` target | Deleted only when `_is_our_body` proves the hub wrote it. | `test_uninstall_deletes_a_style_file_the_tool_wrote` |
| a user's `writing-style.md` | Kept, byte-identical. | `test_uninstall_keeps_a_user_file_with_the_same_name` |
| a `file` the user added to | Kept: a rewrite would delete their text. | `test_uninstall_keeps_a_file_the_user_added_to` |
| skill link into the hub | Removed. | `test_uninstall_removes_only_junctions_into_the_hub` |
| junction to another folder | Kept: `_inside` decides, not `_is_ours`. | `test_uninstall_keeps_a_junction_pointing_outside_the_hub` |
| a real directory | Kept: `_is_ours` is what stops the delete, since `_inside` would accept it. | `test_unlink_skills_never_removes_a_real_directory` |
| Kilo JSON, hub folder | Never deleted. | `test_uninstall_keeps_the_kilo_json` |

`--update` is `--all` with the confirm already answered: it re-applies every
target and re-links, so a stale link or a drifted block is repaired in one pass.

## S06: installers, verify, refresh, docs

- `install.ps1` and `install.sh`: find Python 3.11+, offer to install it for the
  user only, fetch the hub, hand off once to `bootstrap.py`. Neither writes style
  text and neither elevates. `install.ps1` parses with 0 errors and carries the
  dot-source guard; `install.sh` passes `bash -n` and asks on `/dev/tty`, so the
  documented `curl … | sh` path does not eat its own script.
- `verify.py` prints `OK: writing style is consistent` and checks every installed
  `block` target against `style/`. An absent target is SKIP, not drift. The
  no-`repos/` path now says installing does not need that folder.
- `tools/refresh.py`: clone, harvest, verify, coverage, rate, catalog. Stops at the
  first failure, so a catalogue is never built from unverified bodies. Never runs
  from the installer.
- `docs/INSTALL.md` written. `README.md` quick start is now the one-line install;
  the old maintainer flow moved to its own section.
- The `setup/` pages for Cursor, Kiro and Cline already said "native skills" in
  the pre-existing working diff; that claim is now true, because S03 linked them.
  `setup/README.md` no longer says Cursor has no skills dir, and the Kiro
  frontmatter sentence no longer contradicts the line below it.

### Evidence

- `python tools/test_bootstrap.py` -> 127 tests OK.
- Mutation check, S05 group -> all 7 caught.
- Live uninstall into a temp home: markers gone, `KEEP ABOVE` and `KEEP BELOW`
  kept, four `file` targets deleted, `kilo.json` kept, 0 junctions left, `skills/`
  still 41. A foreign junction survived (`0 removed, 1 kept`).
- Live round trip: install, `--check` OK exit 0, `--update` 9 unchanged,
  `--uninstall` 13 removed, user file byte-identical, `skills/` still 41.
- `python tools/verify.py` -> both OK lines, exit 0.
- `python tools/hub.py` -> HUB HEALTHY, 41 skills.

## Review gate (review-my-code, S05+S06)

Two axes ran on the real code. Both found the same data-loss defect, from
opposite sides.

| # | Severity | Finding | Fix |
|---|---|---|---|
| 1 | Critical | `_is_our_body` accepted a user file that quoted the body and added a paragraph, so `--uninstall` deleted their text | ownership now also requires the file not to grow past the body's line count; a revision keeps the count, an addition raises it |
| 2 | Critical | `apply_block` wrote a separator that varied with the file's ending, so `remove_block` could not invert it; trailing bytes changed | fixed `nl + nl` separator, and removal now takes back exactly that plus the one newline after the block |
| 3 | Critical | `_is_ours` used `Path.is_junction`, which needs 3.12; on the promised 3.11 every junction read "not ours" and a second `--update` could crash | read the reparse tag directly when the attribute is absent |
| 4 | Critical | `install.sh` used `read` on stdin, but `curl … \| sh` makes stdin the script, so it ate its own lines | ask on `/dev/tty`, and fail closed with no terminal |
| 5 | Required | `--update` set `args.yes = True`, so a repair wrote without the confirm gate | the confirm is now passed through; proved it refuses with no terminal |
| 6 | Required | `--dry-run --uninstall` skipped the skill loop, so the plan hid 41 removals | the plan now counts the links a real run would remove |
| 7 | Required | `install.ps1` had no dot-source guard, so dot-sourcing ran a real install | guard added before the first top-level step |
| 8 | Required | README quick start was the maintainer flow, not the install line | install line first, maintainer flow in its own section |
| 9 | Required | `setup/README.md` still said Cursor has no skills dir | corrected to `.cursor/skills/` |
| 10 | Optional | uninstall report had no column separator (`would removeclaude`) | space added |
| 11 | Nit | unused `stat` import, repeated `import os as _os` | removed |
| 12 | Nit | `mutation_check.py` used `Path.read_text`, against the hub's own rule | now uses `C.read_text` / `C.write_text` |

Declined: `--update` re-downloading the hub. The spec line it rests on says a link
means `--update` refreshes one folder and every tool sees the new body; a new test
`test_update_carries_a_new_body_to_every_tool` proves that end to end. Fetching a
new zip is the installer's job and needs the network.

Known limit: install then uninstall deletes a file that the user created empty.
Nothing on disk records which run made a file, and an empty file left behind is
worse than one removed, so the code takes the second option.

## Review gate (review-my-code, S04)

Two axes ran on the real code. Both found the same data-loss defect, from
opposite sides, plus a plan that hid writes.

| # | Axis | Finding | Fix |
|---|---|---|---|
| 1 | Both, Critical | `apply_file` treated any file holding a style fingerprint as ours, then rewrote it whole. Proved: a user file quoting one rule was destroyed. A `file` target has no markers, so the overwrite deletes text outside the body. | ownership is `_is_our_body`: the body, or an older revision of it, and nothing else; anything else is `kept` |
| 2 | Spec, Critical | `--all` printed every tool as `not detected ... skipped`, then wrote eight style files. The gate asks consent for the plan, so those writes were never approved. | `plan_lines` follows what the run will write, not what detection found |
| 3 | Spec | `--check` reported a user file as `DRIFT` and said "re-run to fix", a fix the run refuses to make. | reports `kept ... left alone`, exit 0 |
| 4 | Spec | No test pinned the fingerprint false positive. | `test_a_user_file_quoting_the_style_is_kept`, `test_plan_matches_what_all_writes` |
| 5 | Standards | Dead branch: `wanted` never holds a `print` row, so its `print` guard was unreachable. | removed |
| 6 | Standards | `cursor_wanted` duplicated the `print` test under a tool name; a second print row would never print. | one `paste` list drives both |
| 7 | Standards | A present, unselected Cursor was reported `no writable target`, which is false. | `not selected` |
| 8 | Standards | The line-ending rule was re-derived at three sites. | `_newline` helper |
| 9 | Standards | No test reached `apply_file`'s `replaced` branch. | `test_a_stale_body_is_replaced` |

Declined: merging `apply_block` and `apply_file` (markers, ownership and the
untracked rule differ; a mode flag would hide that), and collapsing `_same_block`
into `_same_body` (they differ in intent, and S01's path is proven as written).

### What S04 added

Kind `file` is the hub's own file, no markers: Kiro, Kilo, Cline, Windsurf.
Kind `print` is Cursor, which has no documented User Rules path, so the run
prints the paste text and the click path and `--check` says `manual`.

The live run into a throwaway home wrote all four files with no markers and LF
endings, printed the Cursor paste, and a second run reported `unchanged`. Hand
editing a written file gave `DRIFT` exit 1, a re-run `replaced`, then `OK`.

### Evidence

- `python tools/test_bootstrap.py` -> 88 tests OK, exit 0.
- `python tools/mutation_check.py <S04 names>` -> all 9 mutants caught, exit 0.
  The full 28-mutant run passed 25 of 25 before the review fixes; the 9 S04
  mutants were re-run after every fix, because a fix can empty a test.
- Live run: four `file` targets at 1877 bytes, 39 line feeds, no markers, all
  byte-identical to `style/WRITING-STYLE.md`. Cursor paste text and click path
  printed. `--check` -> `manual    cursor`, exit 0.
- Ownership, live: user text added to an owned file -> `kept`, addition survived.
  A user file that quotes one rule -> `kept`, text survived.
- `python tools/hub.py` -> HUB HEALTHY, 41 skills.

`mutation_check.py` now takes name substrings, so a slice can be re-checked in
about 25 minutes instead of 77. A killed run leaves a mutant on disk; the tool
restores the file on Ctrl-C, and the S04 run was verified intact afterwards.

## Starting the next session

Open `.gsd/milestones/M001/S04-continue.md` first. For S05, the uninstall rule is
in `_is_our_body`: a `writing-style.md` may be deleted only when that returns
`True`, so a file a person wrote with the same name survives.

## Review gate (review-my-code, S03)

Both axes ran on the real diff. They found the same core defect from opposite
sides, plus eight more. One finding was a bug I had already shipped and believed.

| # | Axis | Finding | Fix |
|---|---|---|---|
| 1 | Standards, Critical | `Path.is_symlink()` is False for a Windows junction, so a second run reported `kept` for every link and **never repaired a stale one**. My idempotence test asserted only the exit code, so it hid this. | `_is_ours` also asks `is_junction`; a stale link is now `repaired` |
| 2 | Both | The consent plan hid every skill write. The gate asked approval for writes it never showed. | `plan_lines` lists every folder, the Kilo JSON and the DSH state |
| 3 | Spec | `--all` wrote no skills and no Kilo JSON, because it selected only the four style rows. | one `selected` set drives every write |
| 4 | Spec | DSH `wired`/`not wired` had no caller. The tests passed because they called it directly. | reported during the run and in the plan |
| 5 | Spec | `--check` could not tell a link from a copy, so the fallback the spec says "cannot hide" was invisible. | check compares target and content |
| 6 | Spec | `--check` never inspected the Kilo JSON. | checks it with `dry_run=True` |
| 7 | Standards | `merge_kilo_json` raised `AttributeError` on `{"skills": []}`, against its own docstring. | refuses a wrong shape, leaves the file alone |
| 8 | Standards | `link_skills` ignored its `src_root` argument. | now walks `src_root` |
| 9 | Standards | Dead `--detect` flag, a stale docstring, two `Path.read_text` calls in tests. | removed and fixed |

### The contradiction the end-to-end run found

`--check` reported a stray copy as drift, but the repair said `kept` and left it.
The tool could report a fault it could not fix. Fixed with `_same_content`: a copy
the hub made is byte-identical to its source, and a folder the user wrote is not.
Now proven live: break a link, `--check` exits 1, `--all` reports `repaired`,
`--check` exits 0.

`--all` also wrote a style file for an undetected tool, which made the next
`--check` expect that tool's skills. One rule now: a selected tool is written,
and its skills follow it.

## Review gate (review-my-code, S02)

Two parallel axes, both run on the real diff. They found five defects, one of
them critical.

| # | Axis | Finding | Fix |
|---|---|---|---|
| 1 | Spec, Critical | A **bare** `bootstrap.py` wrote every detected target with no plan and no prompt. install.ps1 calls exactly that form. Spec: "The script never writes silently." | the plan and the gate now cover every write path, not only `--detect` |
| 2 | Spec, Critical | The gate was skipped when stdin was not a tty, so a piped run wrote unprompted. | fail closed: refuse without a terminal, `--yes` is the explicit opt-out |
| 3 | Spec | Detection only knew the 4 writable targets, so kilo and cline were invisible on a machine that has them. | `TOOLS` holds all nine; `detect()` returns names |
| 4 | Standards | `_force_error` test hook sat in the production `atomic_write` signature. | removed; the test uses a real failure (the target is a directory) |
| 5 | Standards | Tests used `Path.read_text`, against the `hubcommon.read_text` rule in a slice about line endings. | switched to `C.read_text` |

Also fixed: the usage docstring contradicted the gate, and `--yes`/`--dir` were
undocumented.

## Self-inflicted bug caught by the live run

I added `.agents` as a codex detection signal. `~/.agents` is the shared skills
folder, so codex was reported present on a machine with no `~/.codex`. Removed,
with `test_shared_skills_folder_is_not_a_tool_signal` to stop it returning.

## The style file broke its own rule

`WRITING-STYLE.md` used "a floor, not a ceiling" and "compress above the floor".
Rule 10 bans idioms and metaphors, so the file contradicted itself. Rewritten in
plain words. This is the kind of defect no test can find; only reading the
prose against its own rules finds it.

## Decisions

- 2026-10-24: `CHANGELOG.md` uses Keep a Changelog + SemVer and starts at `0.1.0`.
  Every change a user can notice gets a line, and a behaviour change must say
  **re-run** or **no action**. Rejected: date-only entries (no version to name in
  an issue), and git log alone (a new person cannot see what changed).
- 2026-10-24: The README leads with Install, then Build. The two audiences differ:
  a user needs one command, a maintainer needs `repos/` and a green suite.
- 2026-10-24: Style text lives once at `style/WRITING-STYLE.md`. No second copy.
  Rejected: a text constant in the script, and copying the whole file unbounded.
- 2026-10-24: Managed regions use HTML comment markers, so the text is invisible
  in rendered markdown and harmless in every tool.
- 2026-10-24: Skills are linked, not copied. One physical tree, refreshed once.
  Fallback to copy is reported per tool, never silent.
- 2026-10-24: DSH stays detect-only. The hub has no YAML parser and a wrong edit
  to `cordis.patch.yml` changes every session in that profile.
- 2026-10-24: Cursor global style is one manual paste. Cursor documents no file
  path for User Rules; an undocumented path breaks silently on the next release.
- 2026-10-24: The install flow is two audiences, two commands. `install.ps1` for
  a new machine, `tools/refresh.py` for the maintainer. The installer never runs
  the maintainer flow.
- 2026-10-24: `python3` is not on PATH on stock Windows. All docs and scripts use
  `python` or `py -3`. This corrects the current README quick start.
- 2026-10-24: The untracked region is anchored on the `## Writing style` heading.
  A prose-based guess swallowed a later `<!-- 5-stack -->` region and broke its
  marker pairing. Without a heading there is no anchor, so the run refuses
  instead of guessing.
- 2026-10-24: Style heading is `##`, not `#`. It sits under a title heading in
  every target file, so `#` broke the outline.

## Files

- `.gsd/SPEC.md` - approved spec, revision 3
- `.gsd/milestones/M001/M001-ROADMAP.md` - six slices, format-validated
- `style/WRITING-STYLE.md` - the one copy of the style text
- `tools/bootstrap.py` - style block engine, skill links, Kilo JSON, DSH report
- `tools/test_bootstrap.py` - 65 tests, temp home only
- `tools/mutation_check.py` - 18 mutants; a survivor means a missing test
- `setup/cursor.md`, `setup/kiro.md`, `setup/cline.md` - corrected: all three
  now say the tool has native skills, which the spec proved and the pages denied
- `README.md` - the same correction, plus `bootstrap.py` in the tools list

## Test result

- `python tools/test_bootstrap.py` -> 65 tests, OK, exit 0
- `python tools/mutation_check.py` -> all 18 mutants caught, exit 0
- `python tools/hub.py` -> `HUB HEALTHY`, exit 0

Live S03 run into a fake home holding claude, cursor and kilo: 41 junctions into
`.claude/skills`, 41 into `.cursor/skills` and 41 into `.agents/skills` in 6.2
seconds; every one resolves into `<hub>/skills`; the Kilo JSON gained a
`skills.paths` entry and kept its other keys. A second run is `unchanged`. The
copy fallback (`--no-link`) reported `41 copied` and measured 4.7 MB, which is
the spec figure and the reason links matter.

The break-and-repair cycle, run live:

| Step | Result |
|---|---|
| replace one junction with a plain copy | - |
| `--check` | `DRIFT ... has 1 copy or stale link(s)`, exit 1 |
| `--all --yes` | `40 linked, 1 repaired` |
| `--check` | exit 0 |

## Carried forward to S05

- `--uninstall` must remove a junction with `os.rmdir`, not `shutil.rmtree`.
  `Remove-Item -Recurse` refuses a junction in non-interactive PowerShell, which
  this slice hit.
- `link_skills` returns a dict the caller can inspect, but nothing records the
  list of links created. S05 needs that list to remove exactly what it made.
- `--check` cannot see a junction that points outside the hub if its target still
  exists as a folder with different content. It compares resolved paths, so a
  stale link is caught, but a link to a moved hub is only caught by content.

## Incident: a runaway copy inside the hub's own skill tree

My own test command, not the tool, wrote into `skills/write-less-code/`. A
`Copy-Item` of a skill folder onto a junction that pointed at that same folder
copied it into itself, so the copy contained itself and the filesystem recursed.
It stopped at a path limit with 1,022 nested folders and 2 MB of junk.

Deleted after checking the exact path: the real skill was intact (SKILL.md 3,503
bytes), the stray tree was untracked, and `git ls-files` showed no tracked file
inside it. `verify.py` and `hub.py` both pass after the delete, and the hub still
holds 41 skills.

The tool now refuses a destination inside the source (`_inside`), with a test and
a mutant. Two lessons:
- `Remove-Item -Recurse` and `Copy-Item -Recurse` both follow a junction. Any
  destructive command on a link needs `cmd /c rmdir` or `os.rmdir`.
- A copy fallback needs a guard against copying into itself, because a link and a
  copy look the same to `shutil.copytree`.


Live write run on a fake home holding claude, gemini and dsh: claude created,
gemini appended, dsh refused as `untracked`, second run all `unchanged`, check
clean for the two written targets and `DRIFT` for dsh. The dsh 5-stack markers
survived and the prose appears once.

Live proof against a copy of the real `~/.dsh/AGENTS.md` (CRLF, 107 lines,
unmarked style section at line 16):

| Run | Result |
|---|---|
| default | `untracked`, exit 1, file unchanged |
| `--replace-untracked` | `replaced`, exit 0 |
| second run | `unchanged`, byte-identical |
| `--check` | `OK`, exit 0 |
| hand-edit then `--check` | `DRIFT`, exit 1 |
| re-run after drift | `OK`, exit 0 |

Integrity after the live run: 149 CRLF and 0 bare LF, `<!-- 5-stack:start/end -->`
both present, one style block, one copy of the prose. The 18 lost lines are the
old style copy. `hub.py` rewrites `RATING.json` as a side effect; that file was
restored with `git checkout`, because this work must not change ratings.

## Next step

S03: skill links for the six native-skill tools, the Kilo `skills.paths` JSON
merge, and DSH detect-only reporting. The link record must let S05's uninstall
remove exactly what it created.

## Known limits carried forward

- Cursor User Rules need one manual paste.
- Cursor Cloud Agents do not copy local skills.
- A non-English Windows locale may move Cline's `Documents` target.
- A machine with no `repos/` cannot prove bodies until `refresh.py` runs.



## M002: Archify diagram skill (2026-10-25)

Status: added, verified, and catalogued.

- Source: `tt-a1i/archify` at commit `51a291770851ad27a400cca73c753c166b5e0c65`.
- Canonical name: `diagram-the-system` (verbatim; only the `name:` line changed).
- License: Apache-2.0. The payload carries `LICENSE`, `LICENSE-MIT`, `NOTICE`
  and `THIRD_PARTY_NOTICES.md`. The hub root still has no LICENSE file; that is
  a pre-existing gap, now more visible because this payload is Apache-2.0.
- Payload: 207 files, 17.31 MB. The bulk is `examples/` (12.49 MB). The cost is
  documented in `README.md`; the payload stays verbatim.
- Integration: `repos.toml` (10th cloned repo), `manifest.yml`, `MASTER_ROUTING.md`,
  `skills/route-to-the-right-skill/SKILL.md` (authored body hash updated), README,
  `docs/INSTALL.md`, both installers, all setup pages, `CHANGELOG.md`,
  `SKILLS.html`, `tools/skill-page-data.json`, and `COMPARISON.md`.
- Routing: `Visualise` is now a phase in the router, `MASTER_ROUTING.md`,
  `tools/catalog.py`, and the skill page, so the catalog entry has its
  Size/Score/Provenance line instead of landing under `Other`.
- Test fix: `tools/test_bootstrap.py` asserts `diagram-the-system` is present and
  the catalog size matches the manifest's merged+authored entries, so deleting a
  skill cannot silently pass.

Evidence:

| Command | Result |
|---|---|
| `python tools/verify.py` | OK: every shipped body is proven against upstream |
| `python tools/hub.py` | HUB HEALTHY; 42 skills, 188 upstream, 65 shipped |
| `python tools/test_bootstrap.py` | 127 tests, OK, exit 0 (350.998s) |

Known limits: Node.js >= 18 is required to render; `browser-check` needs a
browser. The original test failure was the hard-coded `41 skills` assertion; the
later `ChildProcess.kill` was the shell timeout, not a test failure.
