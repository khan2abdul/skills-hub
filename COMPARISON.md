# Shipped vs original

Every skill compared against the upstream original it was fetched from, scored
with the same rubric (`tools/hubrubric.py`). Wire: `tools/compare_skills.py`.

**Craft: ours 9.67 vs originals 9.42.** Faithfulness: 20 exact, 23 composed, 0 lossy.

The headline: our copies are verbatim, so a low score is almost never a
transcription defect. When ours scores 6, the original also scores 6. The
defect is the **choice of source**, and the only legal fix is to take a better
one - composing in sections, or re-vendoring from a stronger candidate.

## Fidelity

| check | result |
|---|---|
| body byte-identical to original | 20/44 |
| body differs | 0 |
| payload files missing vs original | 5 skills |
| payload files altered | 9 skills |

## Score against the original

| skill | ours | original | from | fidelity | reachable | gaps |
|---|---|---|---|---|---|---|
| `landing-page-design` | 9 | 9 | `landing-page-design` (ai-design-skills) | exact | 9.2 | 0 |
| `design-to-motion` | 9.2 | 9.2 | `design-to-motion` (ai-design-skills) | exact | 9.4 | 0 |
| `explore-this-repo` | 9.4 | 8.4 | `cavecrew` (caveman) | composed | 9.6 | 2 |
| `write-the-spec` | 9.6 | 8.4 | `to-spec` (mattpocock-skills) | composed | 10 | 0 |
| `audit-the-whole-repo` | 9.6 | 9.6 | `review` (gsd-2) | composed | 9.7 | 1 |
| `break-into-tasks` | 9.6 | 9.6 | `decompose-into-slices` (gsd-2) | exact | 9.7 | 0 |
| `build-in-small-steps` | 9.6 | 9.6 | `incremental-implementation` (addy-agent-skills) | exact | 9.7 | 0 |
| `build-it-test-first` | 9.6 | 9.6 | `test-driven-development` (addy-agent-skills) | exact | 9.7 | 0 |
| `check-my-ui` | 9.6 | 9.6 | `browser-testing-with-devtools` (addy-agent-skills) | composed | 9.7 | 1 |
| `design-the-interface` | 9.6 | 9.6 | `documentation-and-adrs` (addy-agent-skills) | composed | 9.7 | 1 |
| `discuss-on-new-idea` | 9.6 | 9.6 | `brainstorming` (superpowers) | composed | 9.7 | 2 |
| `document-the-decision` | 9.6 | 9.6 | `documentation-and-adrs` (addy-agent-skills) | exact | 9.7 | 0 |
| `fix-this-bug` | 9.6 | 9 | `karpathy-guidelines` (andrej-karpathy-skills) | composed | 9.7 | 0 |
| `guard-the-dangerous-stuff` | 9.6 | 9.6 | `deprecation-and-migration` (addy-agent-skills) | composed | 9.7 | 3 |
| `hand-off-to-next-session` | 9.6 | 9.6 | `handoff` (gsd-2) | exact | 9.7 | 0 |
| `interview-me-properly` | 9.6 | 9.6 | `interview-me` (addy-agent-skills) | exact | 9.7 | 0 |
| `isolate-this-branch` | 9.6 | 9.6 | `using-git-worktrees` (superpowers) | exact | 9.7 | 0 |
| `make-it-accessible` | 9.6 | 9.6 | `frontend-ui-engineering` (addy-agent-skills) | composed | 9.7 | 0 |
| `make-it-observable` | 9.6 | 9.6 | `observability-and-instrumentation` (addy-agent-skills) | exact | 9.7 | 0 |
| `polish-the-ui` | 9.6 | 8 | `interface-kit` (julius-skills) | composed | 9.7 | 0 |
| `prove-it-works` | 9.6 | 9.6 | `verification-before-completion` (superpowers) | exact | 9.7 | 0 |
| `receive-code-review` | 9.6 | 9.6 | `receiving-code-review` (superpowers) | exact | 9.7 | 0 |
| `research-this-topic` | 9.6 | 8.4 | `source-driven-development` (addy-agent-skills) | composed | 9.7 | 0 |
| `review-my-code` | 9.6 | 9.2 | `code-review-and-quality` (addy-agent-skills) | composed | 9.7 | 2 |
| `route-to-the-right-skill` | 9.6 | - | - | n/a | 9.7 | 0 |
| `set-the-quality-bar` | 9.6 | 9.6 | `constraint-driven-development` (addy-agent-skills) | exact | 9.7 | 0 |
| `ship-it` | 9.6 | 9.3 | `finishing-a-development-branch` (superpowers) | composed | 9.7 | 0 |
| `simplify-this-code` | 9.6 | 9.3 | `code-simplification` (addy-agent-skills) | composed | 9.7 | 2 |
| `split-across-agents` | 9.6 | 9.3 | `dispatching-parallel-agents` (superpowers) | composed | 9.7 | 1 |
| `trim-my-output` | 9.6 | 9 | `caveman` (caveman) | composed | 9.7 | 1 |
| `write-less-code` | 9.6 | 9.6 | `ponytail` (ponytail) | exact | 9.7 | 0 |
| `write-the-docs` | 9.6 | 9.6 | `context-engineering` (addy-agent-skills) | composed | 9.7 | 1 |
| `write-the-domain-glossary` | 9.6 | 8.7 | `domain-modeling` (mattpocock-skills) | composed | 9.7 | 0 |
| `check-my-security` | 10 | 10 | `security-and-hardening` (addy-agent-skills) | composed | 10 | 0 |
| `debug-the-stubborn-one` | 10 | 10 | `debug-like-expert` (gsd-2) | exact | 10 | 0 |
| `debug-this-code` | 10 | 10 | `diagnosing-bugs` (mattpocock-skills) | composed | 10 | 2 |
| `deslop-the-writing` | 10 | 10 | `deslopify` (julius-skills) | exact | 10 | 0 |
| `diagram-the-system` | 10 | 10 | `archify` (archify) | exact | 10 | 0 |
| `finish-the-experience` | 10 | 10 | `last-20-percent` (julius-skills) | exact | 10 | 0 |
| `make-it-fast` | 10 | 10 | `performance-optimization` (addy-agent-skills) | exact | 10 | 0 |
| `review-the-plan` | 10 | 10 | `junior-to-senior` (julius-skills) | composed | 10 | 0 |
| `test-every-surface` | 10 | 7.8 | `qa-only` (gstack) | composed | 10 | 3 |
| `watch-my-context` | 10 | 10 | `context-canary` (julius-skills) | exact | 10 | 0 |
| `write-a-new-skill` | 10 | 9.6 | `writing-for-agents` (mattpocock-skills) | composed | 10 | 2 |

## Missing pieces

### `audit-the-whole-repo` - 9.6/10 (original 9.6)

- **truncated** - composition (7317c) is smaller than 'review' (8632c) alone

### `check-my-ui` - 9.6/10 (original 9.6)

- **truncated** - composition (11003c) is smaller than 'browser-testing-with-devtools' (13935c) alone

### `debug-this-code` - 10/10 (original 10)

- **payload** - original ships 1 file(s) we do not: agents/openai.yaml
- **payload** - original ships 10 file(s) we do not: condition-based-waiting-example.ts, condition-based-waiting.md, CREATION-LOG.md, defense-in-depth.md, find-polluter.sh

### `design-the-interface` - 9.6/10 (original 9.6)

- **payload** - original ships 3 file(s) we do not: DEEPENING.md, DESIGN-IT-TWICE.md, agents/openai.yaml

### `discuss-on-new-idea` - 9.6/10 (original 9.6)

- **payload** - original ships 7 file(s) we do not: builder-check-prompt.md, visual-companion.md, scripts/frame-template.html, scripts/helper.js, scripts/server.cjs
- **truncated** - composition (11408c) is smaller than 'brainstorming' (13602c) alone

### `explore-this-repo` - 9.4/10 (original 8.4)

- **payload** - original ships 1 file(s) we do not: README.md
- **truncated** - composition (3119c) is smaller than 'cavecrew' (3747c) alone

### `guard-the-dangerous-stuff` - 9.6/10 (original 9.6)

- **payload** - original ships 2 file(s) we do not: bin/check-careful.sh, bin/hook-extract.sh
- **payload** - original ships 1 file(s) we do not: agents/openai.yaml
- **truncated** - composition (5648c) is smaller than 'deprecation-and-migration' (12534c) alone

### `review-my-code` - 9.6/10 (original 9.2)

- **payload** - original ships 1 file(s) we do not: agents/openai.yaml
- **truncated** - composition (15325c) is smaller than 'code-review-and-quality' (20898c) alone

### `simplify-this-code` - 9.6/10 (original 9.3)

- **payload** - original ships 1 file(s) we do not: agents/openai.yaml
- **truncated** - composition (11347c) is smaller than 'code-simplification' (13497c) alone

### `split-across-agents` - 9.6/10 (original 9.3)

- **payload** - original ships 13 file(s) we do not: implementer-prompt.md, re-review-prompt.md, task-reviewer-prompt.md, references/batching.md, references/cannot-verify.md

### `test-every-surface` - 10/10 (original 7.8)

- **payload** - original ships 17 file(s) we do not: SKILL.md.tmpl, references/issue-taxonomy.md, sections/browser-setup.md, sections/browser-setup.md.tmpl, sections/browser-verify.md
- **payload** - original ships 6 file(s) we do not: SKILL.md.tmpl, sections/exploratory.md, sections/exploratory.md.tmpl, sections/manifest.json, sections/reporting.md
- **truncated** - composition (16985c) is smaller than 'qa-only' (43529c) alone

### `trim-my-output` - 9.6/10 (original 9)

- **payload** - original ships 8 file(s) we do not: SECURITY.md, scripts/__init__.py, scripts/__main__.py, scripts/benchmark.py, scripts/cli.py

### `write-a-new-skill` - 10/10 (original 9.6)

- **payload** - original ships 2 file(s) we do not: SKILL-MECHANICS.md, agents/openai.yaml
- **payload** - original ships 7 file(s) we do not: render-graphs.js, references/anthropic-best-practices.md, references/CLAUDE_MD_TESTING.md, references/discovery.md, references/flowcharts.md

### `write-the-docs` - 9.6/10 (original 9.6)

- **truncated** - composition (7121c) is smaller than 'context-engineering' (14936c) alone

## What would make each one a 10

Reachable is the ceiling with the material already in `repos/`: our own text
plus every candidate the manifest proposed. A skill whose reachable equals its
current score is at its ceiling and cannot be improved without new source material.

| skill | now | reachable | the move |
|---|---|---|---|
| `landing-page-design` | 9 | 9.2 | at ceiling - no better source in repos/ |
| `design-to-motion` | 9.2 | 9.4 | at ceiling - no better source in repos/ |
| `explore-this-repo` | 9.4 | 9.6 | gains procedure (9 -> 10) by composing 'cavecrew' |
| `write-the-spec` | 9.6 | 10 | re-vendor from 'loop-factory' (craft 10) instead of 'to-spec' (craft 9.6) (+2 more) |
| `audit-the-whole-repo` | 9.6 | 9.7 | gains references (8 -> 10) by composing 'code-optimizer' |
| `break-into-tasks` | 9.6 | 9.7 | at ceiling - no better source in repos/ |
| `build-in-small-steps` | 9.6 | 9.7 | at ceiling - no better source in repos/ |
| `build-it-test-first` | 9.6 | 9.7 | at ceiling - no better source in repos/ |
| `check-my-ui` | 9.6 | 9.7 | gains references (8 -> 10) by composing 'agent-browser' |
| `design-the-interface` | 9.6 | 9.7 | at ceiling - no better source in repos/ |
| `discuss-on-new-idea` | 9.6 | 9.7 | at ceiling - no better source in repos/ |
| `document-the-decision` | 9.6 | 9.7 | at ceiling - no better source in repos/ |
| `fix-this-bug` | 9.6 | 9.7 | at ceiling - no better source in repos/ |
| `guard-the-dangerous-stuff` | 9.6 | 9.7 | at ceiling - no better source in repos/ |
| `hand-off-to-next-session` | 9.6 | 9.7 | at ceiling - no better source in repos/ |
| `interview-me-properly` | 9.6 | 9.7 | at ceiling - no better source in repos/ |
| `isolate-this-branch` | 9.6 | 9.7 | at ceiling - no better source in repos/ |
| `make-it-accessible` | 9.6 | 9.7 | at ceiling - no better source in repos/ |
| `make-it-observable` | 9.6 | 9.7 | at ceiling - no better source in repos/ |
| `polish-the-ui` | 9.6 | 9.7 | gains size (7 -> 10) by composing 'make-interfaces-feel-better' |
| `prove-it-works` | 9.6 | 9.7 | at ceiling - no better source in repos/ |
| `receive-code-review` | 9.6 | 9.7 | at ceiling - no better source in repos/ |
| `research-this-topic` | 9.6 | 9.7 | at ceiling - no better source in repos/ |
| `review-my-code` | 9.6 | 9.7 | at ceiling - no better source in repos/ |
| `route-to-the-right-skill` | 9.6 | 9.7 | gains references (8 -> 10) by composing 'using-superpowers' |
| `set-the-quality-bar` | 9.6 | 9.7 | gains size (7 -> 10) by composing 'best-practices' |
| `ship-it` | 9.6 | 9.7 | at ceiling - no better source in repos/ |
| `simplify-this-code` | 9.6 | 9.7 | at ceiling - no better source in repos/ |
| `split-across-agents` | 9.6 | 9.7 | gains references (8 -> 10) by composing 'subagent-driven-development' |
| `trim-my-output` | 9.6 | 9.7 | gains references (8 -> 10) by composing 'caveman-compress' |
| `write-less-code` | 9.6 | 9.7 | at ceiling - no better source in repos/ |
| `write-the-docs` | 9.6 | 9.7 | at ceiling - no better source in repos/ |
| `write-the-domain-glossary` | 9.6 | 9.7 | at ceiling - no better source in repos/ |
| `check-my-security` | 10 | 10 | at ceiling - no better source in repos/ |
| `debug-the-stubborn-one` | 10 | 10 | at ceiling - no better source in repos/ |
| `debug-this-code` | 10 | 10 | at ceiling - no better source in repos/ |
| `deslop-the-writing` | 10 | 10 | at ceiling - no better source in repos/ |
| `diagram-the-system` | 10 | 10 | at ceiling - no better source in repos/ |
| `finish-the-experience` | 10 | 10 | at ceiling - no better source in repos/ |
| `make-it-fast` | 10 | 10 | at ceiling - no better source in repos/ |
| `review-the-plan` | 10 | 10 | at ceiling - no better source in repos/ |
| `test-every-surface` | 10 | 10 | at ceiling - no better source in repos/ |
| `watch-my-context` | 10 | 10 | at ceiling - no better source in repos/ |
| `write-a-new-skill` | 10 | 10 | at ceiling - no better source in repos/ |

## Detail

### `landing-page-design` - 9.2/10

fidelity: exact - faithful copy; the score IS the original score

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `landing-page-design` | ai-design-skills | 18750 | 9 | 10 | 10 | 6 | 8 | 10 | 10 |

ours: structure 10, procedure 10, gates 6, references 8, portability 10, size 10

### `design-to-motion` - 9.4/10

fidelity: exact - faithful copy; the score IS the original score

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `design-to-motion` | ai-design-skills | 39011 | 9.2 | 10 | 10 | 10 | 8 | 10 | 7 |

ours: structure 10, procedure 10, gates 10, references 8, portability 10, size 7

### `explore-this-repo` - 9.6/10

fidelity: composed - composition; measured against its own sources

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `cavecrew` | caveman | 3747 | 8.4 | 10 | 10 | 2 | 8 | 10 | 10 |
| `caveman-explore` | caveman | 1966 | 8.2 | 10 | 8 | 10 | 8 | 7 | 6 |

ours: structure 10, procedure 9, gates 10, references 8, portability 10, size 10

alternatives the manifest proposed (best first):

- `cavecrew` (caveman, 3747c) craft 8.4 - in use elsewhere
- `caveman-explore` (caveman, 1966c) craft 8.2 - in use elsewhere
- `caveman-discover` (caveman, 5248c) craft 6.5 - rejected

to improve:

- gains procedure (9 -> 10) by composing 'cavecrew'

### `write-the-spec` - 9.6/10

fidelity: composed - composition; measured against its own sources

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `to-spec` | mattpocock-skills | 3118 | 8.4 | 8 | 10 | 4 | 8 | 10 | 10 |

ours: structure 10, procedure 10, gates 10, references 8, portability 10, size 10

alternatives the manifest proposed (best first):

- `loop-factory` (julius-skills, 8023c) craft 10 - rejected **better than ours**
- `write-milestone-brief` (gsd-2, 8522c) craft 9.6 - rejected
- `to-spec` (mattpocock-skills, 3118c) craft 8.4 - in use elsewhere
- `spec` (gstack, 56410c) craft 6.9 - rejected

to improve:

- re-vendor from 'loop-factory' (craft 10) instead of 'to-spec' (craft 9.6)
- python tools/vendor.py --skill write-the-spec --force   # after flipping chosen in manifest.yml
- gains references (8 -> 10) by composing 'loop-factory'

### `audit-the-whole-repo` - 9.7/10

fidelity: composed - composition; measured against its own sources

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `ponytail-audit` | ponytail | 5520 | 9.3 | 10 | 10 | 8 | 8 | 10 | 10 |
| `review` | gsd-2 | 8632 | 9.6 | 10 | 10 | 10 | 8 | 10 | 10 |

ours: structure 10, procedure 10, gates 10, references 8, portability 10, size 10

alternatives the manifest proposed (best first):

- `code-optimizer` (gsd-2, 7958c) craft 9.4 - rejected
- `ponytail-audit` (ponytail, 5520c) craft 9.3 - in use elsewhere
- `web-quality-audit` (gsd-2, 6713c) craft 8.7 - rejected
- `health` (gstack, 43606c) craft 7.4 - rejected

to improve:

- gains references (8 -> 10) by composing 'code-optimizer'

### `break-into-tasks` - 9.7/10

fidelity: exact - faithful copy; the score IS the original score

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `decompose-into-slices` | gsd-2 | 7640 | 9.6 | 10 | 10 | 10 | 8 | 10 | 10 |

ours: structure 10, procedure 10, gates 10, references 8, portability 10, size 10

alternatives the manifest proposed (best first):

- `decompose-into-slices` (gsd-2, 7640c) craft 9.6 - in use elsewhere
- `planning-and-task-breakdown` (addy-agent-skills, 10480c) craft 9.6 - rejected
- `wayfinder` (mattpocock-skills, 12508c) craft 9 - rejected
- `to-tickets` (mattpocock-skills, 5909c) craft 8.1 - rejected

### `build-in-small-steps` - 9.7/10

fidelity: exact - faithful copy; the score IS the original score

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `incremental-implementation` | addy-agent-skills | 9329 | 9.6 | 10 | 10 | 10 | 8 | 10 | 10 |

ours: structure 10, procedure 10, gates 10, references 8, portability 10, size 10

alternatives the manifest proposed (best first):

- `incremental-implementation` (addy-agent-skills, 9329c) craft 9.6 - in use elsewhere
- `lean-build` (caveman, 1090c) craft 6.5 - rejected

### `build-it-test-first` - 9.7/10

fidelity: exact - faithful copy; the score IS the original score

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `test-driven-development` | addy-agent-skills | 16448 | 9.6 | 10 | 10 | 10 | 8 | 10 | 10 |

ours: structure 10, procedure 10, gates 10, references 8, portability 10, size 10

alternatives the manifest proposed (best first):

- `test-driven-development` (addy-agent-skills, 16448c) craft 9.6 - in use elsewhere
- `tdd` (gsd-2, 6680c) craft 9.6 - rejected
- `verify-and-stop` (caveman, 704c) craft 6.8 - rejected

### `check-my-ui` - 9.7/10

fidelity: composed - composition; measured against its own sources

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `browse` | gstack | 34097 | 7.8 | 10 | 10 | 10 | 8 | 1 | 7 |
| `browser-testing-with-devtools` | addy-agent-skills | 13935 | 9.6 | 10 | 10 | 10 | 8 | 10 | 10 |

ours: structure 10, procedure 10, gates 10, references 8, portability 10, size 10

alternatives the manifest proposed (best first):

- `browser-testing-with-devtools` (addy-agent-skills, 13935c) craft 9.6 - in use elsewhere
- `agent-browser` (gsd-2, 20267c) craft 9.1 - rejected
- `browse` (gstack, 34097c) craft 7.8 - in use elsewhere
- `design-review` (gstack, 136531c) craft 7.4 - rejected

to improve:

- gains references (8 -> 10) by composing 'agent-browser'

### `design-the-interface` - 9.7/10

fidelity: composed - composition; measured against its own sources

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `api-and-interface-design` | addy-agent-skills | 14808 | 8.4 | 10 | 4 | 10 | 8 | 10 | 10 |
| `codebase-design` | mattpocock-skills | 6180 | 8.7 | 10 | 10 | 4 | 8 | 10 | 10 |
| `design-an-interface` | gsd-2 | 5614 | 8.4 | 10 | 10 | 2 | 8 | 10 | 10 |
| `documentation-and-adrs` | addy-agent-skills | 10876 | 9.6 | 10 | 10 | 10 | 8 | 10 | 10 |
| `spec-driven-development` | addy-agent-skills | 12996 | 9.6 | 10 | 10 | 10 | 8 | 10 | 10 |

ours: structure 10, procedure 10, gates 10, references 8, portability 10, size 10

alternatives the manifest proposed (best first):

- `api-design` (gsd-2, 8557c) craft 9 - rejected
- `codebase-design` (mattpocock-skills, 6180c) craft 8.7 - in use elsewhere
- `design-an-interface` (gsd-2, 5614c) craft 8.4 - in use elsewhere
- `api-and-interface-design` (addy-agent-skills, 14808c) craft 8.4 - in use elsewhere

### `discuss-on-new-idea` - 9.7/10

fidelity: composed - composition; measured against its own sources

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `brainstorming` | superpowers | 13602 | 9.6 | 10 | 10 | 10 | 8 | 10 | 10 |
| `idea-refine` | addy-agent-skills | 9223 | 9 | 10 | 10 | 6 | 8 | 10 | 10 |

ours: structure 10, procedure 10, gates 10, references 8, portability 10, size 10

alternatives the manifest proposed (best first):

- `brainstorming` (superpowers, 13602c) craft 9.6 - in use elsewhere
- `idea-refine` (addy-agent-skills, 9223c) craft 9 - in use elsewhere
- `grilling` (mattpocock-skills, 2067c) craft 6.6 - rejected

### `document-the-decision` - 9.7/10

fidelity: exact - faithful copy; the score IS the original score

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `documentation-and-adrs` | addy-agent-skills | 10876 | 9.6 | 10 | 10 | 10 | 8 | 10 | 10 |

ours: structure 10, procedure 10, gates 10, references 8, portability 10, size 10

### `fix-this-bug` - 9.7/10

fidelity: composed - composition; measured against its own sources

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `karpathy-guidelines` | andrej-karpathy-skills | 2573 | 9 | 10 | 10 | 10 | 8 | 10 | 6 |
| `surgical-patch` | caveman | 664 | 6.5 | 10 | 2 | 8 | 8 | 10 | 2 |

ours: structure 10, procedure 10, gates 10, references 8, portability 10, size 10

alternatives the manifest proposed (best first):

- `karpathy-guidelines` (andrej-karpathy-skills, 2573c) craft 9 - in use elsewhere
- `surgical-patch` (caveman, 664c) craft 6.5 - in use elsewhere

### `guard-the-dangerous-stuff` - 9.7/10

fidelity: composed - composition; measured against its own sources

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `careful` | gstack | 4727 | 6.1 | 7 | 3 | 8 | 8 | 1 | 10 |
| `deprecation-and-migration` | addy-agent-skills | 12534 | 9.6 | 10 | 10 | 10 | 8 | 10 | 10 |
| `migration` | caveman | 784 | 6.2 | 10 | 2 | 6 | 8 | 10 | 2 |

ours: structure 10, procedure 10, gates 10, references 8, portability 10, size 10

alternatives the manifest proposed (best first):

- `careful` (gstack, 4727c) craft 6.1 - in use elsewhere
- `guard` (gstack, 3814c) craft 5.4 - rejected
- `freeze` (gstack, 4248c) craft 5 - rejected
- `unfreeze` (gstack, 1559c) craft 5 - rejected

### `hand-off-to-next-session` - 9.7/10

fidelity: exact - faithful copy; the score IS the original score

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `handoff` | gsd-2 | 6186 | 9.6 | 10 | 10 | 10 | 8 | 10 | 10 |

ours: structure 10, procedure 10, gates 10, references 8, portability 10, size 10

alternatives the manifest proposed (best first):

- `handoff` (gsd-2, 6186c) craft 9.6 - in use elsewhere
- `context-save` (gstack, 40324c) craft 7.4 - rejected
- `context-restore` (gstack, 42158c) craft 7.4 - rejected

### `interview-me-properly` - 9.7/10

fidelity: exact - faithful copy; the score IS the original score

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `interview-me` | addy-agent-skills | 15034 | 9.6 | 10 | 10 | 10 | 8 | 10 | 10 |

ours: structure 10, procedure 10, gates 10, references 8, portability 10, size 10

alternatives the manifest proposed (best first):

- `interview-me` (addy-agent-skills, 15034c) craft 9.6 - in use elsewhere
- `grill-me` (gsd-2, 5229c) craft 9 - rejected
- `grilling` (mattpocock-skills, 2067c) craft 6.6 - rejected
- `grill-with-docs` (mattpocock-skills, 254c) craft 4.8 - rejected

### `isolate-this-branch` - 9.7/10

fidelity: exact - faithful copy; the score IS the original score

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `using-git-worktrees` | superpowers | 6803 | 9.6 | 10 | 10 | 10 | 8 | 10 | 10 |

ours: structure 10, procedure 10, gates 10, references 8, portability 10, size 10

alternatives the manifest proposed (best first):

- `using-git-worktrees` (superpowers, 6803c) craft 9.6 - in use elsewhere

### `make-it-accessible` - 9.7/10

fidelity: composed - composition; measured against its own sources

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `accessibility` | gsd-2 | 12832 | 9 | 10 | 10 | 6 | 8 | 10 | 10 |
| `frontend-ui-engineering` | addy-agent-skills | 11689 | 9.6 | 10 | 10 | 10 | 8 | 10 | 10 |

ours: structure 10, procedure 10, gates 10, references 8, portability 10, size 10

alternatives the manifest proposed (best first):

- `accessibility` (gsd-2, 12832c) craft 9 - in use elsewhere
- `web-design-guidelines` (gsd-2, 1270c) craft 7.2 - rejected

### `make-it-observable` - 9.7/10

fidelity: exact - faithful copy; the score IS the original score

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `observability-and-instrumentation` | addy-agent-skills | 13890 | 9.6 | 10 | 10 | 10 | 8 | 10 | 10 |

ours: structure 10, procedure 10, gates 10, references 8, portability 10, size 10

alternatives the manifest proposed (best first):

- `observability-and-instrumentation` (addy-agent-skills, 13890c) craft 9.6 - in use elsewhere
- `observability` (gsd-2, 8286c) craft 9 - rejected

### `polish-the-ui` - 9.7/10

fidelity: composed - composition; measured against its own sources

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `interface-kit` | julius-skills | 21903 | 8 | 10 | 4 | 8 | 10 | 10 | 7 |

ours: structure 10, procedure 10, gates 10, references 10, portability 10, size 7

alternatives the manifest proposed (best first):

- `interface-kit` (julius-skills, 21903c) craft 8 - in use elsewhere
- `make-interfaces-feel-better` (gsd-2, 6232c) craft 7.8 - rejected
- `userinterface-wiki` (gsd-2, 14432c) craft 7.8 - rejected
- `design-review` (gstack, 136531c) craft 7.4 - rejected

to improve:

- gains size (7 -> 10) by composing 'make-interfaces-feel-better'

### `prove-it-works` - 9.7/10

fidelity: exact - faithful copy; the score IS the original score

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `verification-before-completion` | superpowers | 3598 | 9.6 | 10 | 10 | 10 | 8 | 10 | 10 |

ours: structure 10, procedure 10, gates 10, references 8, portability 10, size 10

alternatives the manifest proposed (best first):

- `verification-before-completion` (superpowers, 3598c) craft 9.6 - in use elsewhere
- `verify-before-complete` (gsd-2, 5264c) craft 8.4 - rejected
- `verify-and-stop` (caveman, 704c) craft 6.8 - rejected

### `receive-code-review` - 9.7/10

fidelity: exact - faithful copy; the score IS the original score

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `receiving-code-review` | superpowers | 6165 | 9.6 | 10 | 10 | 10 | 8 | 10 | 10 |

ours: structure 10, procedure 10, gates 10, references 8, portability 10, size 10

alternatives the manifest proposed (best first):

- `receiving-code-review` (superpowers, 6165c) craft 9.6 - in use elsewhere

### `research-this-topic` - 9.7/10

fidelity: composed - composition; measured against its own sources

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `research` | mattpocock-skills | 806 | 6.5 | 10 | 8 | 0 | 8 | 10 | 2 |
| `source-driven-development` | addy-agent-skills | 9964 | 8.4 | 10 | 4 | 10 | 8 | 10 | 10 |

ours: structure 10, procedure 10, gates 10, references 8, portability 10, size 10

alternatives the manifest proposed (best first):

- `source-driven-development` (addy-agent-skills, 9964c) craft 8.4 - in use elsewhere
- `research` (mattpocock-skills, 806c) craft 6.5 - in use elsewhere

### `review-my-code` - 9.7/10

fidelity: composed - composition; measured against its own sources

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `code-review` | mattpocock-skills | 6729 | 8.7 | 10 | 10 | 4 | 8 | 10 | 10 |
| `code-review-and-quality` | addy-agent-skills | 20898 | 9.2 | 10 | 10 | 10 | 8 | 10 | 7 |

ours: structure 10, procedure 10, gates 10, references 8, portability 10, size 10

alternatives the manifest proposed (best first):

- `ponytail-review` (ponytail, 5244c) craft 9.3 - rejected
- `code-review-and-quality` (addy-agent-skills, 20898c) craft 9.2 - in use elsewhere
- `code-review` (mattpocock-skills, 6729c) craft 8.7 - in use elsewhere
- `requesting-code-review` (superpowers, 2970c) craft 7.2 - rejected

### `route-to-the-right-skill` - 9.7/10

fidelity: n/a

alternatives the manifest proposed (best first):

- `using-agent-skills` (addy-agent-skills, 9782c) craft 9.6 - rejected
- `ask-matt` (mattpocock-skills, 12677c) craft 8.7 - rejected
- `using-superpowers` (superpowers, 3180c) craft 8.5 - rejected

to improve:

- gains references (8 -> 10) by composing 'using-superpowers'

### `set-the-quality-bar` - 9.7/10

fidelity: exact - faithful copy; the score IS the original score

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `constraint-driven-development` | addy-agent-skills | 20956 | 9.6 | 10 | 10 | 10 | 10 | 10 | 7 |

ours: structure 10, procedure 10, gates 10, references 10, portability 10, size 7

alternatives the manifest proposed (best first):

- `constraint-driven-development` (addy-agent-skills, 20956c) craft 9.6 - in use elsewhere
- `best-practices` (gsd-2, 12619c) craft 7.5 - rejected

to improve:

- gains size (7 -> 10) by composing 'best-practices'

### `ship-it` - 9.7/10

fidelity: composed - composition; measured against its own sources

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `finishing-a-development-branch` | superpowers | 7729 | 9.3 | 10 | 10 | 8 | 8 | 10 | 10 |
| `git-workflow-and-versioning` | addy-agent-skills | 13863 | 8.1 | 10 | 4 | 8 | 8 | 10 | 10 |

ours: structure 10, procedure 10, gates 10, references 8, portability 10, size 10

alternatives the manifest proposed (best first):

- `finishing-a-development-branch` (superpowers, 7729c) craft 9.3 - in use elsewhere
- `git-workflow-and-versioning` (addy-agent-skills, 13863c) craft 8.1 - in use elsewhere
- `land-and-deploy` (gstack, 72365c) craft 6.9 - rejected
- `pr` (mattpocock-skills, 4277c) craft 6.8 - rejected

### `simplify-this-code` - 9.7/10

fidelity: composed - composition; measured against its own sources

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `code-simplification` | addy-agent-skills | 13497 | 9.3 | 10 | 10 | 8 | 8 | 10 | 10 |
| `safe-refactor` | caveman | 705 | 6.2 | 10 | 2 | 6 | 8 | 10 | 2 |

ours: structure 10, procedure 10, gates 10, references 8, portability 10, size 10

alternatives the manifest proposed (best first):

- `code-simplification` (addy-agent-skills, 13497c) craft 9.3 - in use elsewhere
- `safe-refactor` (caveman, 705c) craft 6.2 - in use elsewhere

### `split-across-agents` - 9.7/10

fidelity: composed - composition; measured against its own sources

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `dispatching-parallel-agents` | superpowers | 6052 | 9.3 | 10 | 10 | 8 | 8 | 10 | 10 |
| `subagent-driven-development` | superpowers | 19391 | 6.8 | 10 | 4 | 10 | 0 | 10 | 10 |

ours: structure 10, procedure 10, gates 10, references 8, portability 10, size 10

alternatives the manifest proposed (best first):

- `dispatching-parallel-agents` (superpowers, 6052c) craft 9.3 - in use elsewhere
- `subagent-driven-development` (superpowers, 19391c) craft 8.8 - in use elsewhere

to improve:

- gains references (8 -> 10) by composing 'subagent-driven-development'

### `trim-my-output` - 9.7/10

fidelity: composed - composition; measured against its own sources

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `caveman` | caveman | 4678 | 9 | 10 | 10 | 6 | 8 | 10 | 10 |
| `caveman-compress` | caveman | 5560 | 7.4 | 10 | 10 | 6 | 0 | 10 | 10 |

ours: structure 10, procedure 10, gates 10, references 8, portability 10, size 10

alternatives the manifest proposed (best first):

- `caveman-compress` (caveman, 5560c) craft 9.4 - in use elsewhere
- `caveman` (caveman, 4678c) craft 9 - in use elsewhere
- `caveman-learn` (caveman, 11463c) craft 8.8 - rejected
- `caveman-optimize` (caveman, 4721c) craft 8.4 - rejected

to improve:

- gains references (8 -> 10) by composing 'caveman-compress'

### `write-less-code` - 9.7/10

fidelity: exact - faithful copy; the score IS the original score

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `ponytail` | ponytail | 3548 | 9.6 | 10 | 10 | 10 | 8 | 10 | 10 |

ours: structure 10, procedure 10, gates 10, references 8, portability 10, size 10

alternatives the manifest proposed (best first):

- `ponytail` (ponytail, 3548c) craft 9.6 - in use elsewhere

### `write-the-docs` - 9.7/10

fidelity: composed - composition; measured against its own sources

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `context-engineering` | addy-agent-skills | 14936 | 9.6 | 10 | 10 | 10 | 8 | 10 | 10 |
| `write-docs` | gsd-2 | 5516 | 9.3 | 10 | 10 | 8 | 8 | 10 | 10 |

ours: structure 10, procedure 10, gates 10, references 8, portability 10, size 10

alternatives the manifest proposed (best first):

- `write-docs` (gsd-2, 5516c) craft 9.3 - in use elsewhere

### `write-the-domain-glossary` - 9.7/10

fidelity: composed - composition; measured against its own sources

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `domain-modeling` | mattpocock-skills | 3296 | 8.7 | 10 | 10 | 4 | 8 | 10 | 10 |

ours: structure 10, procedure 10, gates 10, references 8, portability 10, size 10

alternatives the manifest proposed (best first):

- `domain-modeling` (mattpocock-skills, 3296c) craft 8.7 - in use elsewhere
- `grill-with-docs` (mattpocock-skills, 254c) craft 4.8 - rejected

### `check-my-security` - 10/10

fidelity: composed - composition; measured against its own sources

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `security-and-hardening` | addy-agent-skills | 17530 | 10 | 10 | 10 | 10 | 10 | 10 | 10 |
| `security-review` | gsd-2 | 8101 | 8.1 | 10 | 4 | 8 | 8 | 10 | 10 |

ours: structure 10, procedure 10, gates 10, references 10, portability 10, size 10

alternatives the manifest proposed (best first):

- `security-and-hardening` (addy-agent-skills, 17530c) craft 10 - in use elsewhere
- `cso` (gstack, 17812c) craft 8.2 - rejected
- `security-review` (gsd-2, 8101c) craft 8.1 - in use elsewhere

### `debug-the-stubborn-one` - 10/10

fidelity: exact - faithful copy; the score IS the original score

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `debug-like-expert` | gsd-2 | 8643 | 10 | 10 | 10 | 10 | 10 | 10 | 10 |

ours: structure 10, procedure 10, gates 10, references 10, portability 10, size 10

alternatives the manifest proposed (best first):

- `debug-like-expert` (gsd-2, 8643c) craft 10 - in use elsewhere
- `forensics` (gsd-2, 8298c) craft 9.6 - rejected
- `investigate-first` (caveman, 688c) craft 6.2 - rejected

### `debug-this-code` - 10/10

fidelity: composed - composition; measured against its own sources

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `debugging-and-error-recovery` | addy-agent-skills | 10545 | 9.6 | 10 | 10 | 10 | 8 | 10 | 10 |
| `diagnosing-bugs` | mattpocock-skills | 8799 | 10 | 10 | 10 | 10 | 10 | 10 | 10 |
| `systematic-debugging` | superpowers | 9506 | 9.6 | 10 | 10 | 10 | 8 | 10 | 10 |

ours: structure 10, procedure 10, gates 10, references 10, portability 10, size 10

alternatives the manifest proposed (best first):

- `diagnosing-bugs` (mattpocock-skills, 8799c) craft 10 - in use elsewhere
- `systematic-debugging` (superpowers, 9506c) craft 9.6 - in use elsewhere
- `debugging-and-error-recovery` (addy-agent-skills, 10545c) craft 9.6 - in use elsewhere
- `investigate-first` (caveman, 688c) craft 6.2 - rejected

### `deslop-the-writing` - 10/10

fidelity: exact - faithful copy; the score IS the original score

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `deslopify` | julius-skills | 7747 | 10 | 10 | 10 | 10 | 10 | 10 | 10 |

ours: structure 10, procedure 10, gates 10, references 10, portability 10, size 10

alternatives the manifest proposed (best first):

- `deslopify` (julius-skills, 7747c) craft 10 - in use elsewhere

### `diagram-the-system` - 10/10

fidelity: exact - faithful copy; the score IS the original score

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `archify` | archify | 18723 | 10 | 10 | 10 | 10 | 10 | 10 | 10 |

ours: structure 10, procedure 10, gates 10, references 10, portability 10, size 10

alternatives the manifest proposed (best first):

- `archify` (archify, 18723c) craft 10 - in use elsewhere

### `finish-the-experience` - 10/10

fidelity: exact - faithful copy; the score IS the original score

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `last-20-percent` | julius-skills | 8432 | 10 | 10 | 10 | 10 | 10 | 10 | 10 |

ours: structure 10, procedure 10, gates 10, references 10, portability 10, size 10

alternatives the manifest proposed (best first):

- `last-20-percent` (julius-skills, 8432c) craft 10 - in use elsewhere

### `make-it-fast` - 10/10

fidelity: exact - faithful copy; the score IS the original score

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `performance-optimization` | addy-agent-skills | 16517 | 10 | 10 | 10 | 10 | 10 | 10 | 10 |

ours: structure 10, procedure 10, gates 10, references 10, portability 10, size 10

alternatives the manifest proposed (best first):

- `performance-optimization` (addy-agent-skills, 16517c) craft 10 - in use elsewhere
- `code-optimizer` (gsd-2, 7958c) craft 9.4 - rejected
- `core-web-vitals` (gsd-2, 12035c) craft 7.2 - rejected
- `react-best-practices` (gsd-2, 6294c) craft 7.2 - rejected

### `review-the-plan` - 10/10

fidelity: composed - composition; measured against its own sources

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `junior-to-senior` | julius-skills | 9194 | 10 | 10 | 10 | 10 | 10 | 10 | 10 |
| `plan-eng-review` | gstack | 51484 | 6.9 | 7 | 10 | 10 | 8 | 1 | 4 |

ours: structure 10, procedure 10, gates 10, references 10, portability 10, size 10

alternatives the manifest proposed (best first):

- `junior-to-senior` (julius-skills, 9194c) craft 10 - in use elsewhere
- `plan-eng-review` (gstack, 51484c) craft 6.9 - in use elsewhere
- `office-hours` (gstack, 94105c) craft 6.9 - rejected

### `test-every-surface` - 10/10

fidelity: composed - composition; measured against its own sources

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `qa` | gstack | 50831 | 6.9 | 7 | 10 | 10 | 8 | 1 | 4 |
| `qa-only` | gstack | 43529 | 7.8 | 7 | 10 | 10 | 10 | 1 | 7 |

ours: structure 10, procedure 10, gates 10, references 10, portability 10, size 10

alternatives the manifest proposed (best first):

- `qa` (gstack, 50831c) craft 6.9 - in use elsewhere
- `qa-only` (gstack, 43529c) craft 5.8 - in use elsewhere

### `watch-my-context` - 10/10

fidelity: exact - faithful copy; the score IS the original score

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `context-canary` | julius-skills | 6606 | 10 | 10 | 10 | 10 | 10 | 10 | 10 |

ours: structure 10, procedure 10, gates 10, references 10, portability 10, size 10

alternatives the manifest proposed (best first):

- `context-canary` (julius-skills, 6606c) craft 10 - in use elsewhere
- `context-save` (gstack, 40324c) craft 7.4 - rejected
- `context-restore` (gstack, 42158c) craft 7.4 - rejected

### `write-a-new-skill` - 10/10

fidelity: composed - composition; measured against its own sources

| source | repo | chars | craft | structure | procedure | gates | references | portability | size |
|---|---|---|---|---|---|---|---|---|---|
| `writing-for-agents` | mattpocock-skills | 10963 | 9.6 | 10 | 10 | 10 | 8 | 10 | 10 |
| `writing-skills` | superpowers | 16698 | 8.2 | 10 | 10 | 10 | 3 | 7 | 10 |

ours: structure 10, procedure 10, gates 10, references 10, portability 10, size 10

alternatives the manifest proposed (best first):

- `writing-for-agents` (mattpocock-skills, 10963c) craft 9.6 - in use elsewhere
- `writing-skills` (superpowers, 16698c) craft 9 - in use elsewhere
- `create-skill` (gsd-2, 6434c) craft 8.1 - rejected
- `skillify` (gstack, 43934c) craft 7.8 - rejected

