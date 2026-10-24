# Continue - S04 / four owned-file targets and the Cursor print

Read this file, then `.gsd/STATE.md`. That is enough to start. You do not need
the previous conversation.

## Last action

S03 was completed, reviewed with `review-my-code` on two axes, and marked `[x]`.
Its final state: 66 tests pass, all 19 mutants are caught, `hub.py` reports
`HUB HEALTHY`, 41 skill directories are intact, and a live run linked 41
junctions into each of `~/.claude/skills`, `~/.cursor/skills` and
`~/.agents/skills`.

## Next action

Run the `route-to-the-right-skill` skill first, then `build-it-test-first` for
S04. Write the failing tests in `tools/test_bootstrap.py` for the four `file`
targets, then add the writer to `tools/bootstrap.py`.

## What S04 must build

From `.gsd/milestones/M001/M001-ROADMAP.md`, slice S04, `risk:low`,
`depends:[S02]`:

| Tool | Path | Kind |
|---|---|---|
| Kiro | `~/.kiro/steering/writing-style.md` | `file` |
| Kilo Code | `~/.kilocode/rules/writing-style.md` | `file` |
| Windsurf | `~/.codeium/windsurf/memories/writing-style.md` | `file` |
| Cline | `~/Documents/Cline/Rules/writing-style.md` | `file` |
| Cursor | no path | `print` |

The demo line to meet: Kiro, Kilo rules, Cline and Windsurf each hold the body
in a file with no markers, and Cursor prints the paste text plus the click path
and reports `manual` in `--check`.

## The ownership rule that matters

`file` means the hub owns the whole file. SPEC section "How the writing style
gets written" says a `file` target has no markers. That creates the S05 contract
in the roadmap: a `writing-style.md` the tool wrote may be deleted, and anything
else may not.

So S04 must be able to tell "a file the hub wrote" from "a file you wrote with
the same name". S03 already solved the same shape of problem for skill folders
with `_same_content`. Reuse that idea, do not invent a second mechanism.

## Why this order

S03 is the dependency, and it is finished and reviewed. S04 is `risk:low`
because a wrong write creates one small file instead of editing text a user also
edits.

## Open threads

- `--check` reports `manual` for Cursor. Nothing prints the paste text yet.
- S04 adds four paths to `TOOLS` rows that currently hold `rel: None`. Detection
  already reports kiro, cline and windsurf, so only the write path is missing.
- Windsurf and Gemini have no skill mechanism. Windsurf gets the style file only;
  Gemini already has a `block` target.

## Do not

- Do NOT edit any file under `skills/`. Skill text is immutable; `verify.py`
  enforces it.
- Do NOT use `Path.read_text` or `Path.write_text`. Use `C.read_text` and
  `C.write_text` from `tools/hubcommon.py`; `.gitattributes` has `* -text` and
  line endings must never be rewritten.
- Do NOT run `Remove-Item -Recurse` or `Copy-Item -Recurse` on a junction.
  `cmd /c rmdir` or `os.rmdir` only. A `Copy-Item` on a junction once created
  1,022 nested folders inside `skills/`. See the incident note in `STATE.md`.
- Do NOT let `mutation_check.py` run while you edit `bootstrap.py`. It rewrites
  that file and restores it. A concurrent edit corrupts both.
- Do NOT add a `--detect` flag. It was dead and was deleted.

## The process gate the user expects

After the build, in this order: tests, then `mutation_check.py`, then
`review-my-code` on the real diff, then a live run, then the report with the
`=== SKILL RECEIPT ===` block. Skipping the review was a prior miss.

## Current facts on this machine

Present: `~/.claude`, `~/.dsh`, `~/.gemini`, `~/.config/kilo/kilo.json`,
`~/.cline`. Absent: Cursor, Kiro, Codex, Windsurf. So the four `file` targets
cannot be proven live against real tool folders. Prove them against a temporary
home with `--home`, which is what the existing tests do.
