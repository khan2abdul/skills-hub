---
name: design-the-interface
description: Produce several radically different designs for a module, API or interface, compare them against explicit criteria, and synthesize a recommendation - then check the winner against a design checklist and decide whether it warrants a recorded decision. Use when asked to design an interface, shape an API, design it twice, explore module boundaries, or when planning a new deep module and the first idea is unlikely to be the best.
---

# Design The Interface

Composed from verbatim excerpts of 8 upstream skills. Each section is
byte-identical to its source; provenance and hashes are in PROVENANCE.md.
Do not paraphrase a section when editing - change the compose spec instead.

## Design it twice

<!-- source: codebase-design |  | sha256: 2b64e02647e4718b4ba7c47093d28ad02702cf1e9ed48960dae4ed2d1cb0cf69 -->

Design **deep modules**: a lot of behaviour behind a small interface, placed at a clean seam, testable through that interface. Use this language and these principles wherever code is being designed or restructured. The aim is leverage for callers, locality for maintainers, and testability for everyone.

## Glossary

Use these terms exactly: don't substitute "component," "service," "API," or "boundary." Consistent language is the whole point.

**Module**: anything with an interface and an implementation. Deliberately scale-agnostic: a function, class, package, or tier-spanning slice. _Avoid_: unit, component, service.

**Interface**: everything a caller must know to use the module correctly: the type signature, but also invariants, ordering constraints, error modes, required configuration, and performance characteristics. _Avoid_: API, signature (too narrow, they refer only to the type-level surface).

**Implementation**: what's inside a module, its body of code. Distinct from **Adapter**: a thing can be a small adapter with a large implementation (a Postgres repo) or a large adapter with a small implementation (an in-memory fake). Reach for "adapter" when the seam is the topic; "implementation" otherwise.

**Depth**: leverage at the interface. The amount of behaviour a caller (or test) can exercise per unit of interface they have to learn. A module is **deep** when a large amount of behaviour sits behind a small interface, **shallow** when the interface is nearly as complex as the implementation.

**Seam** _(Michael Feathers)_: a place where you can alter behaviour without editing in that place; the *location* at which a module's interface lives. Where to put the seam is its own design decision, distinct from what goes behind it. _Avoid_: boundary (overloaded with DDD's bounded context).

**Adapter**: a concrete thing that satisfies an interface at a seam. Describes *role* (what slot it fills), not substance (what's inside).

**Leverage**: what callers get from depth. More capability per unit of interface they learn. One implementation pays back across N call sites and M tests.

**Locality**: what maintainers get from depth. Change, bugs, knowledge, and verification concentrate in one place rather than spreading across callers. Fix once, fixed everywhere.

## Deep vs shallow

**Deep module** = small interface + lots of implementation:

```
┌─────────────────────┐
│   Small Interface   │  ← Few methods, simple params
├─────────────────────┤
│                     │
│  Deep Implementation│  ← Complex logic hidden
│                     │
└─────────────────────┘
```

**Shallow module** = large interface + little implementation (avoid):

```
┌─────────────────────────────────┐
│       Large Interface           │  ← Many methods, complex params
├─────────────────────────────────┤
│  Thin Implementation            │  ← Just passes through
└─────────────────────────────────┘
```

When designing an interface, ask:

- Can I reduce the number of methods?
- Can I simplify the parameters?
- Can I hide more complexity inside?

## Principles

- **Depth is a property of the interface, not the implementation.** A deep module can be internally composed of small, mockable, swappable parts; they just aren't part of the interface. A module can have **internal seams** (private to its implementation, used by its own tests) as well as the **external seam** at its interface.
- **The deletion test.** Imagine deleting the module. If complexity vanishes, it was a pass-through. If complexity reappears across N callers, it was earning its keep.
- **The interface is the test surface.** Callers and tests cross the same seam. If you want to test *past* the interface, the module is probably the wrong shape.
- **One adapter means a hypothetical seam. Two adapters means a real one.** Don't introduce a seam unless something actually varies across it.

## Designing for testability

Good interfaces make testing natural:

1. **Accept dependencies, don't create them.**

   ```typescript
   // Testable
   function processOrder(order, paymentGateway) {}

   // Hard to test
   function processOrder(order) {
     const gateway = new StripeGateway();
   }
   ```

2. **Return results, don't produce side effects.**

   ```typescript
   // Testable
   function calculateDiscount(cart): Discount {}

   // Hard to test
   function applyDiscount(cart): void {
     cart.total -= discount;
   }
   ```

3. **Small surface area.** Fewer methods = fewer tests needed. Fewer params = simpler test setup.

## Relationships

- A **Module** has exactly one **Interface** (the surface it presents to callers and tests).
- **Depth** is a property of a **Module**, measured against its **Interface**.
- A **Seam** is where a **Module**'s **Interface** lives.
- An **Adapter** sits at a **Seam** and satisfies the **Interface**.
- **Depth** produces **Leverage** for callers and **Locality** for maintainers.

## Rejected framings

- **Depth as ratio of implementation-lines to interface-lines** (Ousterhout): rewards padding the implementation. We use depth-as-leverage instead.
- **"Interface" as the TypeScript `interface` keyword or a class's public methods**: too narrow: interface here includes every fact a caller must know.
- **"Boundary"**: overloaded with DDD's bounded context. Say **seam** or **interface**.

## Going deeper

- **Deepening a cluster given its dependencies**, see [DEEPENING.md](DEEPENING.md): dependency categories, seam discipline, and replace-don't-layer testing.
- **Exploring alternative interfaces**, see [DESIGN-IT-TWICE.md](DESIGN-IT-TWICE.md): spin up parallel sub-agents to design the interface several radically different ways, then compare on depth, locality, and seam placement.

<!-- source: design-an-interface | ## Step 4: Compare in prose | sha256: c261ae3fe496170eadddb37b74d3cc0ce4bb9553470a34e71e9a59657cee21a2 -->

## Step 4: Compare in prose

After all three are on the page, compare them on:

- **Simplicity** — fewer methods and simpler params are easier to learn and harder to misuse
- **Depth** — small interface hiding significant complexity (good) vs large interface with thin implementation (bad)
- **Generality vs specialization** — does it cover the real use case without overfitting?
- **Efficiency of the shape** — does the interface let the implementation be efficient, or force awkward internals?
- **Misuse surface** — what can a caller do wrong?

Prose, not a table. Highlight where the designs diverge most sharply — that is where the interesting trade-off lives.

<!-- source: design-an-interface | ## Step 6: Capture the decision | sha256: 441f38a61f28baae84e8e8cfa0b4059b6b6975744d73834aed0ee88ca7c1b3a3 -->

## Step 6: Capture the decision

Once the user picks:

- Append to `.gsd/DECISIONS.md` with the chosen shape and the reason.
- If a slice is active, update `S##-CONTEXT.md` with the interface sketch.
- Do not write the implementation — that happens during execute.

</process>

<anti_patterns>

- **Three-variants-of-the-same-idea:** all three use a builder, all three return the same object, etc. Kill and re-spawn.
- **Implementation creep:** proposing file paths, call graphs, or internal data structures. Keep it at interface shape.
- **Skipping comparison:** presenting three designs and asking "which do you like?" The comparison is the whole skill.
- **Effort-based ranking:** "#2 is easiest to build" is not an interface argument. Rank by what the caller experiences.

</anti_patterns>

<success_criteria>

- [ ] 3+ genuinely different interface shapes were produced.
- [ ] Each design shows a real usage example, not a type signature in isolation.
- [ ] Trade-offs are named per design.
- [ ] A specific recommendation (or hybrid) is on the page with a reason.
- [ ] The decision is captured in `.gsd/DECISIONS.md` or the active `S##-CONTEXT.md`.

</success_criteria>

<!-- source: api-and-interface-design | ## Verification | sha256: b60b48f8175eb563668c492fafd5bc04bfd3038962a89a5a1599552817c48ca6 -->

## Verification

After designing an API:

- [ ] Every endpoint has typed input and output schemas
- [ ] Error responses follow a single consistent format
- [ ] Validation happens at system boundaries only
- [ ] List endpoints support pagination
- [ ] New fields are additive and optional (backward compatible)
- [ ] Naming follows consistent conventions across all endpoints
- [ ] API documentation or types are committed alongside the implementation
- [ ] State-changing endpoints either honour an idempotency key or are documented as unsafe to retry
- [ ] The key is claimed in one atomic operation, guarded by a unique constraint
- [ ] A reused key with a different payload fails loudly rather than replaying the wrong response
- [ ] The in-flight-duplicate response is a deliberate choice (409, wait, or 202) rather than whatever falls out
- [ ] Key retention outlives the longest retry path, including dead-letter replay

<!-- source: api-and-interface-design | ## Red Flags | sha256: 080a7763932fc6ff15aedf031db1dd09e20ddef7ebca6e42a2611dc5490a0a8c -->

## Red Flags

- Endpoints that return different shapes depending on conditions
- Inconsistent error formats across endpoints
- Validation scattered throughout internal code instead of at boundaries
- Breaking changes to existing fields (type changes, removals)
- List endpoints without pagination
- Verbs in REST URLs (`/api/createTask`, `/api/getUsers`)
- Third-party API responses used without validation or sanitization
- A `SELECT` for an idempotency key followed by an `INSERT` — that's a race, not a guard
- An idempotency key derived from a UUID, timestamp, or anything else regenerated per attempt
- The same key accepted with a different request body, silently returning the first response
- A key retention window shorter than the longest path that can re-deliver the request

<!-- source: documentation-and-adrs | ### When to Write an ADR | sha256: 7eaa00b9a8aee0d814a6db4279321cff4485efa11072e06814ca3226c5c08b23 -->

### When to Write an ADR

- Choosing a framework, library, or major dependency
- Designing a data model or database schema
- Selecting an authentication strategy
- Deciding on an API architecture (REST vs. GraphQL vs. tRPC)
- Choosing between build tools, hosting platforms, or infrastructure
- Any decision that would be expensive to reverse

<!-- source: documentation-and-adrs | ## Prose Review | sha256: ff4569db674ef294437a38e1670153d3f0130e840921fdf1b69f6caedf867289 -->

## Prose Review

After checking the technical content, review the prose for the people who will use it. Clearer wording must not change the decision or its limits.

1. Mark the details that must survive the edit: names, numbers and units, commands, paths, links, conditions, trade-offs, and uncertainty. Check them against the available code and decision context; flag anything you cannot substantiate.
2. Replace stock introductions, promotional adjectives, and repeated summaries with the concrete information the reader needs. Do not replace an unsupported claim with an invented example or a stronger guarantee. Keep necessary technical repetition and the project's established terminology.
3. Compare the edited document with the original and its sources. Restore any lost qualifier or caveat, verify command and code examples still work as documented, and explain any unresolved factual question rather than polishing it away.

<!-- source: spec-driven-development | ## Verification | sha256: 8811928f0dcf8908ec80cb5dfaef6df88a75f5b3fbc92efc6e8b52688a6f6e50 -->

## Verification

Before proceeding to implementation, confirm:

- [ ] The spec covers all six core areas
- [ ] The human has reviewed and approved the spec
- [ ] The turn ended after saving the spec; approval came in a later turn
- [ ] Success criteria are specific and testable
- [ ] Boundaries (Always/Ask First/Never) are defined
- [ ] The spec is saved to a file in the repository
- [ ] If the request bundles several independently testable capabilities, a capability map (module ids, dependency direction, build order) was approved before any module spec was written
- [ ] Every module spec traces to a module id in the approved map

