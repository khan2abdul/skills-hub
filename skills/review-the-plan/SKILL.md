---
name: review-the-plan
description: Adversarial review of a plan, design or architecture before work starts. Treats the plan as junior work, constructs a senior reviewer for the domains it touches, checks the claims against what is actually true in the codebase, and promotes or blocks it. Use when a plan is ready for sign-off, when you want the assumptions attacked before they become code, or when a design needs a harder look than its author can give it.
---

# Review The Plan

Composed from verbatim excerpts of 2 upstream skills. Each section is
byte-identical to its source; provenance and hashes are in PROVENANCE.md.
Do not paraphrase a section when editing - change the compose spec instead.

## The adversarial review

<!-- source: junior-to-senior |  | sha256: 271e5b710dc867e2c51932f248b6414dd9d565b2ad0f47beb156b2650cf69082 -->

Assume the plan in front of you was written by a capable junior: fluent, confident, and trained on the past. Build a senior reviewer that is grounded in two things the junior was not — **this codebase as it actually exists** and **the state of the art as it exists today** — and let the senior tear the plan down and rebuild it.

This skill exists because agent-generated plans fail at two altitudes:

- **Fog** — the plan describes the high level fine ("add caching", "handle auth", "make it scalable") but never commits on the hard parts. No interfaces, no data shapes, no failure handling, no named libraries. An engineer reading it still has to make every real decision themselves.
- **Tunnel** — the plan dives into function signatures and file diffs but has no product vision. No statement of who this is for, what success means, what is out of scope, or why this approach beats the boring alternative. It optimizes a local detail while the shape of the feature is still wrong.

Both are altitude failures. The senior's job is to drag the plan to the right altitude *and* upgrade its substance past the model's training cutoff.

## The cardinal rule

**Every senior finding needs evidence.** A claim about the codebase cites a file and line. A claim about best practice cites a fetched source — official docs, release notes, an RFC, a postmortem — with a date. If web research is unavailable, the finding is labeled `[training-data, unverified]` so stale knowledge is never laundered as current truth. A senior who argues from vibes is just a louder junior.

## Phase 0: Capture the junior artifact

Identify exactly what is under review:

- A plan the agent just produced in this conversation (the default — including your own output from a moment ago).
- A pasted plan, design doc, RFC, or issue description.
- A planning document in the repo the user points at.

Freeze it. Quote or restate the artifact in full before reviewing so the review targets a fixed text, not a moving memory of it. If there is no artifact yet, say so and offer to either generate the junior draft first or review the user's existing idea — do not review thin air.

## Phase 1: Construct the senior

The senior is not a tone of voice. It is a reviewer profile built from research done *now*. Skipping this phase and going straight to critique produces generic review slop.

### 1a. Extract the domains

List the 2-5 load-bearing technical domains the plan touches (e.g., "Postgres schema migration", "React server components", "OAuth token refresh", "vector search at 10M rows"). For each, write one sentence on what a staff-level engineer in that domain would refuse to let slide. This list drives all research that follows.

### 1b. Code research — what is true here

Investigate the repository before judging the plan against it:

- Existing conventions and architecture the plan must fit (or explicitly break, with justification).
- Actual versions in lockfiles/manifests — a plan recommending an API that the pinned version doesn't have is a blocker.
- Prior art: similar features already in the codebase, ADRs, migrations, test patterns.
- Real constraints the junior plan ignored: build system, deploy targets, performance budgets, existing data.

Use a subagent (e.g. `Explore`) for broad sweeps so the review context stays clean.

### 1c. Web research — what is true now

For each load-bearing decision in the plan, search for the current state of the art. The junior's knowledge ends at a training cutoff; the senior's must not. Prioritize primary sources (official docs, changelogs, release notes, maintainer posts) and check dates. You are looking for three kinds of delta:

- **Deprecations** — the plan's approach is now discouraged or removed.
- **Supersessions** — a newer pattern/library/API has clearly won since the cutoff.
- **Hard-won lessons** — published postmortems, benchmarks, or security advisories that change the tradeoff.

Query patterns, source-quality ranking, and when to stop are in **[references/research-playbook.md](references/research-playbook.md)**. If web access is unavailable, proceed on code research alone and mark every best-practice claim `[training-data, unverified]`.

### 1d. Isolation

When the harness supports subagents, run the senior review in a context-isolated subagent that receives the frozen artifact and the research findings but *not* the reasoning that produced the junior plan. Self-review in the same context anchors on its own justifications; isolation is what makes the review adversarial rather than confirmatory.

## Phase 2: Diagnose the altitude

Before line-by-line critique, classify the artifact: **fog**, **tunnel**, or **mixed** (most real plans fog the hard parts and tunnel on the easy ones — flag each section separately).

Fog test — for every component the plan names, can a competent engineer start tomorrow without making a product or architecture decision themselves? Tunnel test — does the plan state who this is for, what success looks like, what is explicitly out of scope, and why this approach beat the obvious alternative?

The full diagnostic checklists, the vague-word blacklist ("simple", "scalable", "handle gracefully", "robust", ...), and severity definitions are in **[references/review-rubric.md](references/review-rubric.md)**.

## Phase 3: Adversarial review

The senior reviews the frozen artifact against three lenses: codebase reality (1b), current state of the art (1c), and altitude (Phase 2). Rules of engagement:

- Every vague phrase gets challenged with the concrete question it is hiding from.
- Every named technology gets a version and a reason; every unnamed one ("a queue", "some cache") gets named or the choice gets flagged as an open decision.
- Every data shape that crosses a boundary gets written down.
- Every plan gets asked: what is the rollback, what is the migration, what breaks at 10x.
- Steelman before attacking: state the strongest version of the junior's choice, then show why it still loses (or concede that it wins — agreeing with the junior when the evidence supports it is a valid senior outcome, not a failure of the skill).

Findings use three severities — **blocker** (plan fails as written), **major** (works but meaningfully worse than SOTA or misfit to the repo), **minor** (polish) — each with evidence and a concrete fix. Definitions and examples: **[references/review-rubric.md](references/review-rubric.md)**.

## Phase 4: Promote the plan

Critique without a rewrite is just complaining. Produce the senior version of the plan with this shape:

1. **Goal and non-goals** — one paragraph of product intent; explicit out-of-scope list.
2. **Decisions** — each load-bearing choice with the chosen option, version, rationale, the strongest rejected alternative, and the evidence (file ref or source link).
3. **Design at the right altitude** — interfaces, data shapes, and failure handling for the hard parts; deliberately coarse strokes for the routine parts.
4. **Sequencing** — milestones with an observable verification step each ("done" must be checkable, not vibes).
5. **Risks and rollback** — what is hardest to undo and the escape hatch.
6. **Open questions for a human** — product decisions the senior is *not* allowed to invent. Scoping is the senior's job; product direction is not.

## Output format

Deliver two artifacts, review first:

```markdown
## Senior Review

**Altitude diagnosis:** fog | tunnel | mixed — one-sentence justification.

### Blockers
- [B1] Finding — evidence (file:line or source+date) — fix.

### Major
- [M1] ...

### Minor
- [m1] ...

### What the junior got right
- Credit where due; preserved in the rewrite.

## Promoted Plan (v2)
[Phase 4 structure]

## Delta summary
- 3-6 bullets: what changed from junior to senior and why.

## Open questions for you
- Product decisions that need a human.
```

## Boundaries

- The senior scopes and upgrades; it does **not** invent product direction. Genuine product choices go to "Open questions", not into the rewrite.
- Never silently replace the junior plan — the user sees the review, the rewrite, and the delta, and decides.
- If research contradicts the user's stated preference, present the evidence and defer; the user may have context the senior lacks.
- A review with zero blockers and zero majors is a legitimate result. Say "this plan holds" and stop — do not manufacture findings to look rigorous.

<!-- source: plan-eng-review | ## Cognitive Patterns — How Great Eng Managers Think | sha256: b220a844244d3a657e9fe278b9cd1c9926ac78b9d374b3015484ac4e508245c8 -->

## Cognitive Patterns — How Great Eng Managers Think

Apply throughout, not as extra checks:

1. **State diagnosis:** Match falling behind, treading water, repaying debt or innovating (Larson).
2. **Blast radius:** Trace worst-case harm to systems and people.
3. **Boring by default:** Three innovation tokens; otherwise proven technology (McKinley).
4. **Incremental change:** Strangler migrations and canaries over big bangs (Fowler).
5. **Systems over heroes:** Design for tired humans at 3am.
6. **Reversibility:** Flags and incremental rollouts make mistakes cheap to undo.
7. **Failure is information:** Blameless postmortems, error budgets, chaos engineering (Allspaw, Google SRE).
8. **Conway's Law:** Design team/system boundaries together (Skelton/Pais).
9. **DX signals quality:** Slow CI, local dev and deploys predict quality and retention trouble.
10. **Essential vs accidental complexity:** Real problem or self-created? (Brooks).
11. **Two-week smell:** A small feature taking two weeks suggests onboarding trouble.
12. **Glue work:** Value coordination without trapping people in it (Reilly).
13. **Make change easy first:** Refactor before behavior changes; keep them separate (Beck).
14. **Own production:** Dev and ops share responsibility (Majors).
15. **Error budgets:** Spend a 99.9% SLO's 0.1% downtime budget; avoid uptime at any cost (Google SRE).

