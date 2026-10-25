# skills-hub

One canonical skill per capability, harvested from 10 repos cloned into `repos/`
(+19 catalogued sources), published under names a human can actually ask for.

**Core guarantee: no skill text is ever edited.** A shipped skill is either a
verbatim copy (only the `name:` line changes) or a composition of verbatim
excerpts with per-block sha256 proofs. `tools/verify.py` proves both on every run.

**Self-contained.** The 10 source repos live inside the hub at `repos/`, cloned
from `repos.toml` URLs. No absolute paths in tools, specs, or docs. See [Paths](#paths).

**Status:** all 42 capabilities shipped - 18 verbatim copies, 23 compositions, plus
1 authored (`route-to-the-right-skill`, the parent router)
(`debug-this-code` scores 37/37 on the rubric). `hub.py` reports `HUB HEALTHY`.

If you just want the skills on your machine, read [Install](#install) and stop
there. Everything from [Build](#build-changing-the-hub-itself) onward is for
changing the hub itself.

## Install

Two groups of people use this repo, and they want different things.

| You want | Go to | Needs |
|---|---|---|
| The 42 skills and the writing style in my AI tools | [One command](#one-command) | Python 3.11+ (Node >=18 + browser for `diagram-the-system`) |
| To change a skill, add a repo, or fix the tooling | [Build](#build-changing-the-hub-itself) | a clone, and `repos/` |

### One command

```powershell
# Windows
irm https://raw.githubusercontent.com/khan2abdul/skills-hub/main/install.ps1 | iex
```

```sh
# Linux and macOS
curl -fsSL https://raw.githubusercontent.com/khan2abdul/skills-hub/main/install.sh | sh
```

The installer finds Python 3.11+, offers to install it for your user only, puts
the hub in `%LOCALAPPDATA%\skills-hub` (Windows) or
`~/.local/share/skills-hub` (Linux, macOS), then hands off once to
`bootstrap.py`. That last step prints every path it will write and asks once.
Nothing needs admin. See [docs/INSTALL.md](docs/INSTALL.md) for the per-tool
detail and the Cursor paste step.

### Day to day

Run these from the installed hub folder:

```sh
python tools/bootstrap.py --check        # is everything still in place? exit 1 if not
python tools/bootstrap.py --dry-run      # print the plan, write nothing
python tools/bootstrap.py --update       # re-apply every target and re-link
python tools/bootstrap.py --uninstall    # remove only what this tool wrote
```

`--check` is the one to put in a habit. It reports three states and only two of
them are failures:

| State | Means | Fails the run? |
|---|---|---|
| `OK` | in place and current | no |
| `manual` | Cursor, needs the one paste | no |
| `DRIFT` | changed or missing | yes, exit 1 |

### What changes for you

- **Your own text is safe.** A `block` target keeps everything outside its
  markers. A `file` target is replaced only when its text is the hub's body; add
  your own line and the hub calls it yours and leaves it alone.
- **Uninstall is conservative.** It deletes a style file only when it can prove
  it wrote that text, and removes a skill entry only when it is a link into the
  hub. A real folder of yours stays, even at a skill name.
- **`--update` asks first.** It never writes unseen. With no terminal it refuses
  and tells you to pass `--yes`.
- **Editing a file the hub owns invites drift.** If you edit a `file` target, the
  hub reports `kept` and stops managing it. That is deliberate, and it means your
  text survives. To put the file back under management, move your text elsewhere,
  delete the file, and run `--update`. The hub then writes its body again.

### Requirements

Python 3.11 or newer (dict ordering, `tomllib`, `X | None` annotations).
Standard library only - nothing to `pip install`. Every tool starts with
`#!/usr/bin/env python3`, so on Linux and macOS it also runs directly once the
exec bit is set.

`diagram-the-system` is the one runtime exception: it ships a Node.js CLI and
needs Node.js 18+ plus Chrome, Chromium or Edge for its browser gate. Its
207-file payload is about 17.3 MB because it includes rendered examples; the
`--no-link` copy fallback copies that too.

```bash
chmod +x tools/*.py
./tools/hub.py
```

On Windows use `python tools/hub.py`, or `py -3 tools/hub.py` where `python` is
not on `PATH`. The tools force stdout to UTF-8, so a cp1252 console will not
crash on the arrows and box characters in the reports.

## Why

Ten repos ship 188 skill bundles with heavy overlap - five debuggers, nine token
tools, three "prove it works". Each is fine alone; together they collide and the
agent picks arbitrarily. This hub keeps one winner per capability, records exactly
where every line came from, and reports when upstream moves.

## The 42 skills

**[SKILLS.md](SKILLS.md) is the catalog**: what each skill does, the upstream
repo and skill it came from, and - for compositions - the exact sections that
were combined.

| Phase | Skills |
|---|---|
| Understand | `interview-me-properly`, `discuss-on-new-idea`, `explore-this-repo`, `research-this-topic` |
| Define | `write-the-spec`, `write-the-domain-glossary`, `design-the-interface`, `document-the-decision`, `write-the-docs` |
| Visualise | `diagram-the-system` |
| Plan | `break-into-tasks`, `review-the-plan`, `set-the-quality-bar` |
| Build | `build-it-test-first`, `build-in-small-steps`, `write-less-code`, `simplify-this-code`, `split-across-agents`, `isolate-this-branch` |
| Finish | `finish-the-experience` |
| Debug | `debug-this-code`, `debug-the-stubborn-one`, `fix-this-bug` |
| Review | `review-my-code`, `receive-code-review`, `check-my-security`, `audit-the-whole-repo`, `prove-it-works`, `test-every-surface` |
| UI | `check-my-ui`, `polish-the-ui`, `make-it-accessible`, `make-it-fast` |
| Operate | `make-it-observable`, `ship-it`, `guard-the-dangerous-stuff`, `hand-off-to-next-session` |
| Meta | `watch-my-context`, `trim-my-output`, `route-to-the-right-skill`, `write-a-new-skill`, `deslop-the-writing` |

## Build: changing the hub itself

An install does not need `repos/`. Changing the hub does, because every skill
body is proved against its upstream. So this flow is separate from the install.

```bash
git clone https://github.com/khan2abdul/skills-hub.git
cd skills-hub
python3 tools/refresh.py          # clone, harvest, verify, coverage, rate, catalog
```

`refresh.py` is the whole flow in one command, and it stops at the first failure
so a catalog is never built from unverified bodies. The steps it runs:

```bash
python3 tools/clone_repos.py      # clone/refresh the 9 sources into repos/
python3 tools/harvest.py          # drift, broken refs, skills with no decision
python3 tools/verify.py           # the guarantee: prove every body
python3 tools/coverage.py         # write COVERAGE.md
python3 tools/rate_skills.py      # write RATING.md + RATING.json
python3 tools/catalog.py          # write SKILLS.md
```

`clone_repos.py` is shallow by default (`--depth 1`): the hub only needs current
file contents to vendor from. Full history would be ~1.5 GB for gstack alone.

To inspect a tool's install page:

```bash
python3 tools/hub.py --tools          # list every install page
python3 tools/hub.py --setup cursor   # print one page to paste into that agent
```

### Before you open a pull request

```bash
python3 tools/test_bootstrap.py    # 127 tests, temp homes only, never your real one
python3 tools/verify.py            # must print both OK lines, exit 0
python3 tools/hub.py               # must print HUB HEALTHY
```

`python3 tools/hub.py` rewrites `RATING.json` as a side effect. If you did not
mean to change a rating, run `git checkout -- RATING.json` before you commit.

## Changelog and versioning

[CHANGELOG.md](CHANGELOG.md) is the record of what changed and when. The project
uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html) and the format is
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

Version numbers move like this:

| Change | Version |
|---|---|
| A new skill, a new target tool, a new flag | minor (`0.1.0` -> `0.2.0`) |
| A fix that changes behaviour, or a change a user must act on | patch (`0.1.0` -> `0.1.1`) |
| A rename, or a removal of a flag or a file | major (`0.x` -> `0.(x+1)` until 1.0.0) |

There are no git tags yet. When a version is ready to ship, add the tag that
matches the heading in `CHANGELOG.md`.

## Layout

```
skills-hub/
├── repos.toml          # 10 cloned + 19 reference sources (paths relative)
├── manifest.yml        # 42 capabilities -> candidates -> chosen | composed
├── style/              # WRITING-STYLE.md: the only copy of the style text
├── CHANGELOG.md        # what changed, and the version it changed in
├── COVERAGE.md         # generated: every upstream skill, shipped / rejected / dropped
├── RATING.md           # generated: every shipped skill scored /10, with fixes
├── RATING.json         # generated: same, machine-readable, consumed by apply-rating
├── SKILLS.md           # generated: what every skill does, where it came from
├── ignore.txt          # 123 upstream skills deliberately not selected
├── MASTER_ROUTING.md   # phase router for always-on context
├── install.ps1         # one-line installer, Windows
├── install.sh          # one-line installer, Linux and macOS
├── repos/              # the 9 upstream repos, cloned here (gitignored)
├── compose/            # <name>.yml: which excerpts make up a composed skill
├── skills/             # shipped skills
│   └── <canonical>/
│       ├── SKILL.md        # verbatim, or verified-verbatim excerpts
│       └── PROVENANCE.md   # repo, path, commit, per-block sha256
├── setup/              # one install page per agent tool
└── tools/
    ├── hub.py          # entry point for the maintainer flow
    ├── bootstrap.py    # install the style and link the 42 skills into each tool
    ├── refresh.py      # clone, harvest, verify, coverage, rate, catalog
    ├── clone_repos.py  # clone/refresh repos/ from repos.toml
    ├── harvest.py      # read-only drift report
    ├── coverage.py     # write COVERAGE.md from PROVENANCE.md
    ├── rate_skills.py  # score every skill /10 -> RATING.md + RATING.json
    ├── catalog.py      # write SKILLS.md: what each skill does and where it came from
    ├── apply_rating.py # apply body-preserving fixes, then verify
    ├── vendor.py       # verbatim copy; name: line only
    ├── compose.py      # build from compose/<name>.yml
    ├── evaluate.py     # score skills against a rubric
    ├── verify.py       # prove every body against upstream, and the style
    ├── hubcommon.py    # shared path resolution and config parsing
    ├── test_bootstrap.py   # the suite: temp homes only
    └── mutation_check.py   # edit bootstrap.py on purpose; a surviving mutant is a missing test
```

`repos/` is 236 MB shallow-cloned, versus 1.9 GB in the old external folder
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

Everything resolves at runtime. The tools are Python, so the hub root is found
from the file's own location, not from a shell variable:

| What | Resolution order |
|---|---|
| Hub root | `tools/` lives one level under it, so the parent of the running tool's folder |
| Sources root | `$SKILLS_HUB_SOURCES` -> `sources_root` in `repos.toml` (default `repos`) -> walk up for a sibling `setupskills`/`skills-sources` that actually holds repos |
| Repo path | relative to the sources root, or absolute |
| Target home | `--home DIR` if given, else the current user's home |

`bootstrap.py` also takes `--dir DIR` to use another hub folder as the source.

The default is now `repos/`, inside the hub, so a fresh clone of this repo needs
one command to become self-sufficient. The `setupskills` fallback is kept only so
a pre-existing external checkout still resolves without re-downloading.

`clone_repos.py` resolves strictly: it never falls back to a discovered folder,
because a write tool that guesses would clone 10 repos into the wrong tree. If the
declared root is missing you get one clear message and exit code 2.

## The commands

```bash
python3 tools/harvest.py    # drift, broken refs, skills with no decision (read-only)
python3 tools/coverage.py   # write COVERAGE.md: 188 upstream -> shipped / rejected / dropped
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

## What `bootstrap.py` writes, per tool

This table is the source of truth. It matches `TOOLS` in
[tools/bootstrap.py](tools/bootstrap.py).

| Tool | Style | Skill links |
|---|---|---|
| Claude Code | `~/.claude/CLAUDE.md`, between markers | `~/.claude/skills/` |
| Codex CLI | `~/.codex/AGENTS.md`, between markers | `~/.agents/skills/` (shared) |
| Gemini CLI | `~/.gemini/GEMINI.md`, between markers | none |
| DeepSeek Harness | `~/.dsh/AGENTS.md`, between markers | none; reports wired or not |
| Kilo Code | `~/.kilocode/rules/writing-style.md`, whole file | `skills.paths` in `~/.config/kilo/kilo.json` |
| Cline | the Documents folder's `Cline/Rules/writing-style.md`, whole file | `~/.cline/skills/` |
| Cursor | none: one manual paste | `~/.cursor/skills/` and `~/.agents/skills/` |
| Kiro | `~/.kiro/steering/writing-style.md`, whole file | `~/.kiro/skills/` |
| Windsurf | `~/.codeium/windsurf/memories/writing-style.md`, whole file | none |

`block` keeps your own text and manages only the lines between the markers.
`file` is owned whole by the hub, and is replaced only when its text is still the
hub's body. `print` writes no file: Cursor keeps User Rules in its settings, so
the run prints the text and the click path, and `--check` reports `manual`.

Six tools get skill links: Claude Code, Codex, Cline, Cursor, Kiro, and the shared
`~/.agents/skills`. Codex and Cursor both read that shared folder, so it is
written once. A tool loads a skill body only when it uses it.

Gemini CLI, DeepSeek Harness and Windsurf get the writing style only, because
`bootstrap.py` does not link skills into them. DeepSeek Harness needs
`customSkillDirs` in its profile patch; [setup/deepseek-harness.md](setup/deepseek-harness.md)
explains that one, and how `includeDefaultRoots: false` retires the old roots.

Each `setup/` page is self-contained: paste the whole file into that agent and say
"set this up for me."

Installing is not the same as loading. `bootstrap.py` never puts a skill body
into always-on context; the style block is the only text that costs every turn.

## Design rules

- **Skill text is immutable.** Verbatim, or verified excerpts. One named exception: `mode: authored`, which records its own body hash instead. `route-to-the-right-skill` is the only entry that uses it, and only because no upstream body could route to this hub's 42 names.
- **One capability, one name.** If two names could fire on the same request, merge them.
- **Verb-first names that say the job:** `debug-this-code`, `write-the-spec`.
- **Provenance is mandatory.** A body with no PROVENANCE.md cannot be audited.
- **Score before you claim better.** `evaluate.py` exists so "improved" is a number.
- **Ignore loudly.** Every rejected skill gets a line in `ignore.txt`.
- **Always-on costs every turn.** Per tool, keep the always-loaded set to ~3 skills.

## Licensing and network

Vendored skills keep their upstream licenses. `diagram-the-system` is
Apache-2.0; its `LICENSE`, `LICENSE-MIT`, `NOTICE` and
`THIRD_PARTY_NOTICES.md` ship inside `skills/diagram-the-system/`. The hub's own
code does not yet declare a license.

`diagram-the-system`'s `finalize` performs a bounded update check against
`tt-a1i.github.io`; it never installs anything, and an unavailable check does not
block delivery.
