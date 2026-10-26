# Skill rating

Every shipped skill scored out of 10 by `tools/rate_skills.py` (rubric v2).
Wire: `tools/apply_rating.py`. Do not edit by hand - re-run the tool.

**Mean 9.76/10** over 43 skills. Grades: A 43.

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
| 2 | `debug-the-stubborn-one` | **10** | A | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 8417 |
| 3 | `debug-this-code` | **10** | A | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 11662 |
| 4 | `deslop-the-writing` | **10** | A | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 7669 |
| 5 | `diagram-the-system` | **10** | A | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 18734 |
| 6 | `finish-the-experience` | **10** | A | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 8346 |
| 7 | `make-it-fast` | **10** | A | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 16505 |
| 8 | `review-the-plan` | **10** | A | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10808 |
| 9 | `test-every-surface` | **10** | A | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 16985 |
| 10 | `watch-my-context` | **10** | A | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 6544 |
| 11 | `write-a-new-skill` | **10** | A | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 16925 |
| 12 | `audit-the-whole-repo` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 7317 |
| 13 | `break-into-tasks` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 7496 |
| 14 | `build-in-small-steps` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 9323 |
| 15 | `build-it-test-first` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 16444 |
| 16 | `check-my-ui` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 11003 |
| 17 | `design-the-interface` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 13041 |
| 18 | `discuss-on-new-idea` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 11408 |
| 19 | `document-the-decision` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 10875 |
| 20 | `fix-this-bug` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 5588 |
| 21 | `guard-the-dangerous-stuff` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 5648 |
| 22 | `hand-off-to-next-session` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 6082 |
| 23 | `interview-me-properly` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 15043 |
| 24 | `isolate-this-branch` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 6803 |
| 25 | `make-it-accessible` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 13788 |
| 26 | `make-it-observable` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 13875 |
| 27 | `polish-the-ui` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 10 | 10 | 7 | 32763 |
| 28 | `prove-it-works` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 3582 |
| 29 | `receive-code-review` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 6163 |
| 30 | `research-this-topic` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 10876 |
| 31 | `review-my-code` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 15325 |
| 32 | `route-to-the-right-skill` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 7937 |
| 33 | `set-the-quality-bar` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 10 | 10 | 7 | 20946 |
| 34 | `ship-it` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 9112 |
| 35 | `simplify-this-code` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 11347 |
| 36 | `split-across-agents` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 8178 |
| 37 | `trim-my-output` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 6927 |
| 38 | `write-less-code` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 3503 |
| 39 | `write-the-docs` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 7121 |
| 40 | `write-the-domain-glossary` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 5676 |
| 41 | `write-the-spec` | **9.7** | A | 9.6 | 10 | 10 | 10 | 10 | 8 | 10 | 10 | 16159 |
| 42 | `explore-this-repo` | **9.6** | A | 9.4 | 10 | 10 | 9 | 10 | 8 | 10 | 10 | 3119 |
| 43 | `landing-page-design` | **9.2** | A | 9 | 10 | 10 | 10 | 6 | 8 | 10 | 10 | 18750 |

## How to improve

Ranked by score gain. `auto` fixes are applied by `python tools/apply_rating.py --apply`;
`no` ones need a decision from you.

| # | skill | finding | gain | auto | what to do |
|---|---|---|---|---|---|

