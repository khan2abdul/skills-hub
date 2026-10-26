# Supercomputer Routing

Skills are invoked by name. Each name maps to one capability with one canonical
body. Nothing here requires editing a skill body.

## Always on

- `trim-my-output` — terse `file:line` contracts, no filler.
- `write-less-code` — the Code Necessity Ladder on every line written.

## Pipeline

| Phase | Skill | Output |
|---|---|---|
| Understand | `interview-me-properly`, or `discuss-on-new-idea` | shared understanding |
| Research | `research-this-topic` | findings on disk |
| Spec | `write-the-spec` | `.gsd/SPEC.md` |
| Glossary | `write-the-domain-glossary` | `GLOSSARY.md` |
| Slice | `break-into-tasks` | `.gsd/TICKETS.md` |
| Plan review | `review-the-plan` | approved plan |
| Build | `build-it-test-first`, `build-in-small-steps` | code and tests |
| Finish | `finish-the-experience` | product walk-through, not just plumbing |
| Debug | `debug-this-code` → `debug-the-stubborn-one` | failing test, then fix |
| Review | `review-my-code`, `check-my-security` | findings, including spec conformance |
| Verify | `prove-it-works`, `test-every-surface` | evidence in this message |
| UI | `check-my-ui`, `polish-the-ui`, `landing-page-design`, `design-to-motion`, `make-it-accessible`, `make-it-fast` | live DOM / console / network; page and motion craft |
| Visualise | `diagram-the-system` | checked architecture, sequence, dataflow, ERD and explainer visuals |
| Docs | `write-the-docs`, `deslop-the-writing` | publishable prose |
| Ship | `ship-it` | PR, changelog |

## Gates

- No code before `.gsd/SPEC.md` exists on non-trivial work.
- No "done" claim without `prove-it-works` evidence produced in the same message.
- No user-facing "done" without the `finish-the-experience` walk.
- No fix without a failing test that reproduces it first.
- `debug-this-code` gets two hypotheses. Then stop and report the trace.

## Non-trivial means

A new feature, a schema or API change, an auth/money/data path, or roughly more
than ten changed lines. Skip the ceremony for a typo or a one-line fix — but still
run the test covering the line you touched.

## Installing

See `setup/<tool>.md`. Only the frontmatter `name:` line and the per-tool wrapper
ever differ from upstream; `tools/verify.py` proves it.
