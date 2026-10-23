# skills-hub

One canonical skill per capability, harvested from 9 repos cloned into `repos/`
(+20 catalogued sources), published under names a human can actually ask for.

**Core guarantee: no skill text is ever edited.** A shipped skill is either a
verbatim copy (only the `name:` line changes) or a composition of verbatim
excerpts with per-block sha256 proofs. `tools/verify.ps1` proves both on every run.

**Self-contained.** The 9 source repos live inside the hub at `repos/`, cloned
from `repos.toml` URLs. No absolute paths in tools, specs, or docs. See [Paths](#paths).

**Status:** all 41 capabilities shipped - 17 verbatim copies, 23 compositions, plus
1 authored (`route-to-the-right-skill`, the parent router)
(`debug-this-code` scores 37/37 on the rubric). `hub.ps1` reports `HUB HEALTHY`.

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

```powershell
pwsh tools/clone-repos.ps1      # clone/refresh the 9 sources into repos/
pwsh tools/hub.ps1              # health: harvest + verify + coverage + rating + catalog
pwsh tools/hub.ps1 -Tools       # list install pages
pwsh tools/hub.ps1 -Setup cursor  # print a page to paste into that agent
```

`clone-repos.ps1` is shallow by default (`--depth 1`): the hub only needs current
file contents to vendor from. Full history would be ~1.5 GB for gstack alone.

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
    ├── hub.ps1         # entry point
    ├── clone-repos.ps1 # clone/refresh repos/ from repos.toml
    ├── harvest.ps1     # read-only drift report
    ├── coverage.ps1    # write COVERAGE.md from PROVENANCE.md
    ├── rate-skills.ps1 # score every skill /10 -> RATING.md + RATING.json
    ├── catalog.ps1     # write SKILLS.md: what each skill does and where it came from
    ├── apply-rating.ps1# apply body-preserving fixes, then verify
    ├── vendor.ps1      # verbatim copy; name: line only
    ├── compose.ps1     # build from compose/<name>.yml
    ├── evaluate.ps1    # score skills against a rubric
    └── verify.ps1      # prove every body against upstream
```

`repos/` is 187 MB shallow-cloned, versus 1.9 GB in the old external folder
(mostly gstack's untracked `node_modules` and full history). It is gitignored
because it is regenerable from `repos.toml`.

## Two ways to ship a skill

**Verbatim** — one upstream skill wins outright. Only `name:` changes.

```powershell
pwsh tools/vendor.ps1 -Skill write-the-spec
```

**Composed** - no single file is good enough, but several complement each other.
`compose/<name>.yml` lists headings to lift; each excerpt is copied byte-for-byte
and its sha256 recorded. Headings and ordering are the only new material.

```powershell
pwsh tools/compose.ps1 -Name debug-this-code -WhatIf   # preview
pwsh tools/compose.ps1 -Name debug-this-code
```

**Authored** — written for this hub, quoting nothing. Used exactly once, for
`route-to-the-right-skill`, because every upstream router named skills this hub
does not ship and the repair was a rewrite rather than a name swap. The entry
declares `mode: authored` and records the sha256 of its own body, so
`verify.ps1` still catches drift. This is not a loophole: adding a second
authored skill needs a reason of the same kind.

## Is a composed skill actually better?

Don't take it on faith - score it. `tools/evaluate.ps1` checks 16 debugging
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
| Docs | `$hub = $env:SKILLS_HUB`, else walk up for `skills-hub/tools/verify.ps1` |

The default is now `repos/`, inside the hub, so a fresh clone of this repo needs
one command to become self-sufficient. The `setupskills` fallback is kept only so
a pre-existing external checkout still resolves without re-downloading.

`clone-repos.ps1` resolves strictly: it never falls back to a discovered folder,
because a write tool that guesses would clone 9 repos into the wrong tree. If the
declared root is missing you get one clear message and exit code 2.

## The commands

```powershell
pwsh tools/harvest.ps1    # drift, broken refs, skills with no decision (read-only)
pwsh tools/coverage.ps1   # write COVERAGE.md: 187 upstream -> shipped / rejected / dropped
pwsh tools/catalog.ps1    # write SKILLS.md: what each skill does and where it came from
pwsh tools/vendor.ps1 -All -WhatIf
pwsh tools/evaluate.ps1   # rubric scores
pwsh tools/verify.ps1     # the guarantee
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
proposed, lost, and nobody recorded why. `harvest.ps1` used to count those as
claimed, which is how 72 upstream skills went missing while it reported zero.

## Rating: 0-10 per skill, and what to fix

```powershell
pwsh tools/rate-skills.ps1          # write RATING.md + RATING.json
pwsh tools/apply-rating.ps1         # show which fixes it can apply
pwsh tools/apply-rating.ps1 -Apply  # do it, then re-run verify.ps1
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

`apply-rating.ps1` can only do **body-preserving** fixes - copying a missing
reference file from upstream, then re-running `verify.ps1`. It refuses to touch
a `SKILL.md`, because that is the hub's core guarantee. Everything else is
printed as a TODO for a human decision.

`verify.ps1` runs two checks:

1. **Verbatim** - rebuilds upstream with only the `name:` line swapped, compares
   bytes. Any edit fails, and the message names the line.
2. **Composed** - re-extracts each excerpt from its source, re-hashes it, and
   asserts the excerpt still appears verbatim in the shipped file.

Both were negative-tested: editing a phrase in a shipped body gives
`EXCERPT ALTERED`; editing the upstream source gives `EXCERPT DRIFT`; either way
exit 1.

## Adding a tenth repo

1. Append a `[[repo]]` to `repos.toml` with `status = "cloned"` and a relative `path`.
2. `pwsh tools/harvest.ps1` - lists its skills that no entry claims.
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
"set this up for me." All 48 PowerShell blocks are parse-checked, and the
conversion snippet was run end-to-end to confirm the body survives unchanged.

Claude Code, dsh, Gemini and Kilo Code 7.8+ have real skill directories. Cursor,
Kiro, Cline, Codex and Windsurf load *rules* - always-on text. Their pages name
a 2-3 skill always-on set for that reason.

## Design rules

- **Skill text is immutable.** Verbatim, or verified excerpts. One named exception: `mode: authored`, which records its own body hash instead. `route-to-the-right-skill` is the only entry that uses it, and only because no upstream body could route to this hub's 41 names.
- **One capability, one name.** If two names could fire on the same request, merge them.
- **Verb-first names that say the job:** `debug-this-code`, `write-the-spec`.
- **Provenance is mandatory.** A body with no PROVENANCE.md cannot be audited.
- **Score before you claim better.** `evaluate.ps1` exists so "improved" is a number.
- **Ignore loudly.** Every rejected skill gets a line in `ignore.txt`.
- **Always-on costs every turn.** Per tool, keep the always-loaded set to ~3 skills.
