# Skill rating

Every shipped skill scored out of 10 by `tools/rate_skills.py` (rubric v2).
Wire: `tools/apply_rating.py`. Do not edit by hand - re-run the tool.

**Mean 9.77/10** over 41 skills. Grades: A 41.

The score has two halves, because "is this a good skill" and "was this the
best skill available" are different questions:

- **craft (75%)** - is the shipped text well made?
- **selection (25%)** - did we take the strongest source for the job?

A well-made copy of the wrong skill is still the wrong skill. Selection is
where a wrong-but-well-made choice shows up.

## Craft dimensions

| dimension | weight | measures |
|---|---|---|
| structure | 15 | frontmatter parses, name matches dir, description usable |
| procedure | 20 | numbered steps and headings - does it say what to do |
| gates | 15 | STOP/MUST/NEVER and verification language |
| references | 20 | files the body names exist in the skill dir |
| portability | 15 | no absolute paths or uninstalled vendor helpers |
| size | 15 | big enough to be a procedure, small enough to load |

## Scoreboard

| # | skill | score | grade | craft | sel | struc | proc | gates | refs | port | size | chars |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `check-my-security` | **10** | A | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 19413 |
| 2 | `debug-the-stubborn-one` | **10** | A | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 8647 |
| 3 | `debug-this-code` | **10** | A | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 11662 |
| 4 | `deslop-the-writing` | **10** | A | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 7755 |
| 5 | `finish-the-experience` | **10** | A | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 8437 |
| 6 | `make-it-fast` | **10** | A | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 16505 |
| 7 | `review-the-plan` | **10** | A | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10808 |
| 8 | `test-every-surface` | **10** | A | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 16985 |
| 9 | `watch-my-context` | **10** | A | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 6607 |
| 10 | `write-a-new-skill` | **10** | A | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 16925 |
| 11 | `audit-the-whole-repo` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 7317 |
| 12 | `break-into-tasks` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 7634 |
| 13 | `build-in-small-steps` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 9323 |
| 14 | `build-it-test-first` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 16444 |
| 15 | `check-my-ui` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 11003 |
| 16 | `design-the-interface` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 13041 |
| 17 | `discuss-on-new-idea` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 11408 |
| 18 | `document-the-decision` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 10875 |
| 19 | `fix-this-bug` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 5588 |
| 20 | `guard-the-dangerous-stuff` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 5648 |
| 21 | `hand-off-to-next-session` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 6202 |
| 22 | `interview-me-properly` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 15043 |
| 23 | `isolate-this-branch` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 6803 |
| 24 | `make-it-accessible` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 13788 |
| 25 | `make-it-observable` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 13875 |
| 26 | `polish-the-ui` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 10 | 10 | 7 | 32763 |
| 27 | `prove-it-works` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 3582 |
| 28 | `receive-code-review` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 6163 |
| 29 | `research-this-topic` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 10876 |
| 30 | `review-my-code` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 15325 |
| 31 | `route-to-the-right-skill` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 7704 |
| 32 | `set-the-quality-bar` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 10 | 10 | 7 | 20946 |
| 33 | `ship-it` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 9112 |
| 34 | `simplify-this-code` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 11347 |
| 35 | `split-across-agents` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 8178 |
| 36 | `trim-my-output` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 6927 |
| 37 | `write-less-code` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 3554 |
| 38 | `write-the-docs` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 7121 |
| 39 | `write-the-domain-glossary` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 5676 |
| 40 | `write-the-spec` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 16159 |
| 41 | `explore-this-repo` | **9.6** | A | 9.4 | 10 | 10 | 9 | 10 | 8 | 10 | 10 | 3119 |

## How to improve

Ranked by score gain. `auto` fixes are applied by `python tools/apply_rating.py --apply`;
`no` ones need a decision from you.

| # | skill | finding | gain | auto | what to do |
|---|---|---|---|---|---|

