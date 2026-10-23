# skills-hub

One canonical skill per capability, harvested from 9 repos cloned into `repos/`
(+20 catalogued sources), published under names a human can actually ask for.

**Core guarantee: no skill text is ever edited.** A shipped skill is either a
verbatim copy (only the `name:` line changes) or a composition of verbatim
excerpts with per-block sha256 proofs. `tools/verify.py` proves both on every run.

**Self-contained.** The 9 source repos live inside the hub at `repos/`, cloned
from `repos.toml` URLs. No absolute paths in tools, specs, or docs. See [Paths](#paths).

**Status:** all 41 capabilities shipped - 17 verbatim copies, 23 compositions, plus
1 authored (`route-to-the-right-skill`, the parent router)
(`debug-this-code` scores 37/37 on the rubric). `hub.py` reports `HUB HEALTHY`.

## Why

Nine repos ship 187 skill bundles with heavy overlap - five debuggers, nine token
tools, three "prove it works". Each is fine alone; together they collide and the
agent picks arbitrarily. This hub keeps one winner per capability, records exactly
where every line came from, and reports when upstream moves.

## The 41 skills

**[SKILLS.md](SKILLS.md) is the catalog**: what each skill does, the upstream
repo and skill it came from, and - for compositions - the exact sections that
were combined.

| Phase | Skills |
|---|---|
| Understand | `interview-me-properly`, `discuss-on-new-idea`, `explore-this-repo`, `research-this-topic` |
| Define | `write-the-spec`, `write-the-domain-glossary`, `design-the-interface`, `document-the-decision`, `write-the-docs` |
| Plan | `break-into-tasks`, `review-the-plan`, `set-the-quality-bar` |
| Build | `build-it-test-first`, `build-in-small-steps`, `write-less-code`, `simplify-this-code`, `split-across-agents`, `isolate-this-branch` |
| Finish | `finish-the-experience` |
| Debug | `debug-this-code`, `debug-the-stubborn-one`, `fix-this-bug` |
| Review | `review-my-code`, `receive-code-review`, `check-my-security`, `audit-the-whole-repo`, `prove-it-works`, `test-every-surface` |
| UI | `check-my-ui`, `polish-the-ui`, `make-it-accessible`, `make-it-fast` |
| Operate | `make-it-observable`, `ship-it`, `guard-the-dangerous-stuff`, `hand-off-to-next-session` |
| Meta | `watch-my-context`, `trim-my-output`, `route-to-the-right-skill`, `write-a-new-skill`, `deslop-the-writing` |

## Quick start

```bash
python3 tools/clone_repos.py      # clone/refresh the 9 sources into repos/
python3 tools/hub.py              # health: harvest + verify + coverage + rating + catalog
python3 tools/hub.py --tools       # list install pages
python3 tools/hub.py --setup cursor  # print a page to paste into that agent
```

`clone_repos.py` is shallow by default (`--depth 1`): the hub only needs current
file contents to vendor from. Full history would be ~1.5 GB for gstack alone.

### Requirements

Python 3.11 or newer (dict ordering, `tomllib`, `X | None` annotations).
Standard library only - nothing to `pip install`. Every tool starts with
`#!/usr/bin/env python3`, so on Linux and macOS it also runs directly once the
exec bit is set:

```bash
chmod +x tools/*.py
./tools/hub.py
```

On Windows use `python tools/hub.py`, or `py -3 tools/hub.py` where `python` is
not on `PATH`. The tools force stdout to UTF-8, so a cp1252 console will not
crash on the arrows and box characters in the reports.

## Layout

```
skills-hub/
├── repos.toml          # 9 cloned + 20 reference sources (paths relative)
├── manifest.yml        # 41 capabilities -> candidates -> chosen | composed
├── COVERAGE.md         # generated: every upstream skill, shipped / rejected / dropped
├── RATING.md           # generated: every shipped skill scored /10, with fixes
├── RATING.json         # generated: same, machine-readable, consumed by apply-rating
├── SKILLS.md           # generated: what every skill does, where it came from
├── ignore.txt          # 122 upstream skills deliberately not selected
├── MASTER_ROUTING.md   # phase router for always-on context
├── repos/              # the 9 upstream repos, cloned here (gitignored)
├── compose/            # <name>.yml: which excerpts make up a composed skill
├── skills/             # shipped skills
│   └── <canonical>/
│       ├── SKILL.md        # verbatim, or verified-verbatim excerpts
│       └── PROVENANCE.md   # repo, path, commit, per-block sha256
├── setup/              # one install page per agent tool
└── tools/
    ├── hub.py         # entry point
    ├── clone_repos.py # clone/refresh repos/ from repos.toml
    ├── harvest.py     # read-only drift report
    ├── coverage.py    # write COVERAGE.md from PROVENANCE.md
    ├── rate_skills.py # score every skill /10 -> RATING.md + RATING.json
    ├── catalog.py     # write SKILLS.md: what each skill does and where it came from
    ├── apply_rating.py# apply body-preserving fixes, then verify
    ├── vendor.py      # verbatim copy; name: line only
    ├── compose.py     # build from compose/<name>.yml
    ├── evaluate.py    # score skills against a rubric
    └── verify.py      # prove every body against upstream
```

`repos/` is 187 MB shallow-cloned, versus 1.9 GB in the old external folder
(mostly gstack's untracked `node_modules` and full history). It is gitignored
because it is regenerable from `repos.toml`.

## Two ways to ship a skill

**Verbatim** — one upstream skill wins outright. Only `name:` changes.

```bash
python3 tools/vendor.py --skill write-the-spec
```

**Composed** - no single file is good enough, but several complement each other.
`compose/<name>.yml` lists headings to lift; each excerpt is copied byte-for-byte
and its sha256 recorded. Headings and ordering are the only new material.

```bash
python3 tools/compose.py --name debug-this-code --what-if   # preview
python3 tools/compose.py --name debug-this-code
```

**Authored** — written for this hub, quoting nothing. Used exactly once, for
`route-to-the-right-skill`, because every upstream router named skills this hub
does not ship and the repair was a rewrite rather than a name swap. The entry
declares `mode: authored` and records the sha256 of its own body, so
`verify.py` still catches drift. This is not a loophole: adding a second
authored skill needs a reason of the same kind.

## Is a composed skill actually better?

Don't take it on faith - score it. `tools/evaluate.py` checks 16 debugging
practices that separate a real procedure from vibes: a red-capable loop, ranked
hypotheses, minimise the repro, non-deterministic handling, regression test,
cleanup, injection-safe error handling, and so on.

Measured for `debug-this-code`:

| skill | pts | coverage | chars |
|---|---|---|---|
| **debug-this-code (composed)** | **37/37** | **100%** | 11,570 |
| diagnosing-bugs | 30/37 | 81% | 8,595 |
| systematic-debugging | 24/37 | 65% | 9,366 |
| debugging-and-error-recovery | 24/37 | 65% | 10,165 |
| debug-like-expert | 16/37 | 43% | 8,334 |
| investigate-first | 3/37 | 8% | 473 |

The composition is +23% over the best single file for +35% length. It is
deliberately small: `diagnosing-bugs` supplies the whole procedure, and three
short excerpts add exactly the 7 points it was missing. An earlier draft lifted
14 sections for 16.4k chars and still scored 24/37 - the rubric is what caught
that over-engineering.

## Paths

Everything resolves at runtime:

| What | Resolution order |
|---|---|
| Hub root | `$PSScriptRoot` of the running tool |
| Sources root | `$env:SKILLS_HUB_SOURCES` -> `sources_root` in `repos.toml` (default `repos`) -> walk up for a sibling `setupskills`/`skills-sources` that actually holds repos |
| Repo path | relative to the sources root, or absolute |
| Docs | `$hub = $env:SKILLS_HUB`, else walk up for `skills-hub/tools/verify.py` |

The default is now `repos/`, inside the hub, so a fresh clone of this repo needs
one command to become self-sufficient. The `setupskills` fallback is kept only so
a pre-existing external checkout still resolves without re-downloading.

`clone_repos.py` resolves strictly: it never falls back to a discovered folder,
because a write tool that guesses would clone 9 repos into the wrong tree. If the
declared root is missing you get one clear message and exit code 2.

## The commands

```bash
python3 tools/harvest.py    # drift, broken refs, skills with no decision (read-only)
python3 tools/coverage.py   # write COVERAGE.md: 187 upstream -> shipped / rejected / dropped
python3 tools/catalog.py    # write SKILLS.md: what each skill does and where it came from
python3 tools/vendor.py --all --what-if
python3 tools/evaluate.py   # rubric scores
python3 tools/verify.py     # the guarantee
```

`COVERAGE.md` is the answer to "did we take the best skill from that repo?". It
is generated from `skills/*/PROVENANCE.md`, so it reports what actually shipped,
not what the manifest proposed. Each upstream skill is exactly one of:

| state | meaning |
|---|---|
| shipped | a `PROVENANCE.md` names it; the table says which canonical skill it became |
| rejected | listed in `ignore.txt`, with the reason recorded in `manifest.yml` |
| dropped | neither. **This is the gap** - it needs a decision |

A skill that only appears in a manifest `candidates` list is *dropped*: it was
proposed, lost, and nobody recorded why. `harvest.py` used to count those as
claimed, which is how 72 upstream skills went missing while it reported zero.

## Rating: 0-10 per skill, and what to fix

```bash
python3 tools/rate_skills.py          # write RATING.md + RATING.json
python3 tools/apply_rating.py         # show which fixes it can apply
python3 tools/apply_rating.py --apply  # do it, then re-run verify.py
```

The score has two halves, because "is this a good skill" and "was this the best
skill available" are different questions:

| half | weight | answers |
|---|---|---|
| craft | 75% | structure, procedure, gates, references, portability, size |
| selection | 25% | did we take the strongest source for the job? |

Selection exists because a well-made copy of the wrong skill is still wrong:
a wrong-but-well-made choice only shows up here. `RATING.md` prints the
evidence behind every dimension.

`apply_rating.py` can only do **body-preserving** fixes - copying a missing
reference file from upstream, then re-running `verify.py`. It refuses to touch
a `SKILL.md`, because that is the hub's core guarantee. Everything else is
printed as a TODO for a human decision.

`verify.py` runs two checks:

1. **Verbatim** - rebuilds upstream with only the `name:` line swapped, compares
   bytes. Any edit fails, and the message names the line.
2. **Composed** - re-extracts each excerpt from its source, re-hashes it, and
   asserts the excerpt still appears verbatim in the shipped file.

Both were negative-tested: editing a phrase in a shipped body gives
`EXCERPT ALTERED`; editing the upstream source gives `EXCERPT DRIFT`; either way
exit 1.

## Adding a tenth repo

1. Append a `[[repo]]` to `repos.toml` with `status = "cloned"` and a relative `path`.
2. `python3 tools/harvest.py` - lists its skills that no entry claims.
3. Map them to candidates, or add a `[[skill]]`.
4. Rejected skills go in `ignore.txt` with a reason.

Reference-only repos use `status = "reference"` and are skipped by harvest.

## Installing into a tool

| Tool | Page | Reads |
|---|---|---|
| Claude Code | [setup/claude-code.md](setup/claude-code.md) | `.claude/skills/`, `~/.claude/skills/` |
| Cursor | [setup/cursor.md](setup/cursor.md) | `.cursor/rules/*.mdc` |
| Kiro | [setup/kiro.md](setup/kiro.md) | `.kiro/steering/` |
| Cline | [setup/cline.md](setup/cline.md) | `.clinerules/` |
| Kilo Code | [setup/kilo-code.md](setup/kilo-code.md) | `skills.paths` in `kilo.json` (native), or `.kilocode/rules-*/` (legacy) |
| DeepSeek Harness | [setup/deepseek-harness.md](setup/deepseek-harness.md) | `customSkillDirs` (+ `includeDefaultRoots: false` to retire the defaults) |
| Gemini CLI | [setup/gemini-cli.md](setup/gemini-cli.md) | `GEMINI.md` |
| Codex CLI | [setup/codex-cli.md](setup/codex-cli.md) | `AGENTS.md` |
| Windsurf | [setup/windsurf.md](setup/windsurf.md) | `.windsurf/rules/` |
| Anything else | [setup/generic.md](setup/generic.md) | depends |

Each page is self-contained: paste the whole file into that agent and say
"set this up for me." Every shell example has been run, and the conversion
snippet was executed end-to-end to confirm the body survives unchanged.

Claude Code, dsh, Gemini and Kilo Code 7.8+ have real skill directories. Cursor,
Kiro, Cline, Codex and Windsurf load *rules* - always-on text. Their pages name
a 2-3 skill always-on set for that reason.

## Design rules

- **Skill text is immutable.** Verbatim, or verified excerpts. One named exception: `mode: authored`, which records its own body hash instead. `route-to-the-right-skill` is the only entry that uses it, and only because no upstream body could route to this hub's 41 names.
- **One capability, one name.** If two names could fire on the same request, merge them.
- **Verb-first names that say the job:** `debug-this-code`, `write-the-spec`.
- **Provenance is mandatory.** A body with no PROVENANCE.md cannot be audited.
- **Score before you claim better.** `evaluate.py` exists so "improved" is a number.
- **Ignore loudly.** Every rejected skill gets a line in `ignore.txt`.
- **Always-on costs every turn.** Per tool, keep the always-loaded set to ~3 skills.
