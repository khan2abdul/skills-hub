# Provenance

- canonical: route-to-the-right-skill
- mode: authored
- authored: 2026-10-23
- body sha256: a955a019dbab3e75d328c088022c24bb860c85567d66be4c0818a347d39786ba
- published policy: skill text is immutable *except* for an entry that declares
  `mode: authored` here. Nothing upstream owns this text, so there is no excerpt
  to re-hash; `verify.ps1` proves instead that the shipped body has not drifted
  from the hash above.

## Why this one is authored, not vendored

It replaced a `mode: verbatim` copy of `using-agent-skills` from
`addy-agent-skills` (commit `aeac41d`). That copy could not be repaired within the
immutability rule: it routed to 30 skills under names this hub does not have
(`interview-me`, `spec-driven-development`, `test-driven-development`,
`code-review-and-quality`, `shipping-and-launch`, `idea-refine`,
`context-engineering`, `planning-and-task-breakdown`, and the rest), and it cited
`../../references/definition-of-done.md`, a file that does not exist in this
layout. Fixing the names was a rewrite, not a name-only swap.

Three candidates were considered and all three had the same defect:

| candidate | repo | why it was not enough |
|---|---|---|
| `using-agent-skills` | addy-agent-skills | the shipped copy; routes to retired names |
| `using-superpowers` | superpowers | strongest enforcement, but routes to `superpowers:*` skills that are not vendored |
| `ask-matt` | mattpocock-skills | persona router, not a phase router |

So the discipline was kept from `using-superpowers` (the compulsory check, the
red-flag table) and the routing shape from `using-agent-skills` (phase tree), with
every name rewritten to the 41 that actually ship. The body is prose written for
this hub; no upstream bytes are quoted, so there is no excerpt to prove.

## What changed from the vendored copy

- Every skill name resolves to a shipped skill or to a dsh bundled skill. There
  are no dead names.
- Added re-routing triggers (phase boundary, two failed attempts, scope change,
  about to claim done, about to run a destructive command).
- Added a gate table, so a phase cannot be silently declared finished.
- Added the dsh bundled-skill section, because the retired copy could not know
  about skills that ship with the harness.
- Dropped the `../../references/definition-of-done.md` pointer (no such file) and
  the 16-step lifecycle, which named skills this hub does not have.
