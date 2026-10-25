---
name: route-to-the-right-skill
description: "The parent skill. Route any request to the right skill before acting, keep re-routing at every phase boundary, and block the rationalisations that skip a skill. Use at the start of every session and after every phase change, failed attempt, or scope change."
---

# Route to the Right Skill

This is the parent skill. Every other skill in this hub is a phase it routes to.
It does not do the work; it decides which skill does, and it keeps deciding as the
work moves.

## The rule

**Check for an applicable skill before you act.** Not before you finish thinking -
before the first tool call, the first file read, the first edit.

The check is compulsory. The invocation is conditional. Those are different
obligations, and conflating them is why strict routing gets switched off:

- A 20-second check that concludes "no skill applies" is a pass, and it is cheap.
- Acting first and checking later is a fail even when the right skill turns out
  to be irrelevant, because you cannot tell that in advance.

When a skill applies, you do not have discretion. Read it, then follow it.

## How to check

1. **Name the phase.** Understand, Research, Spec, Plan, Build, Debug, Review,
   Verify, Finish, Visualise, Docs, Ship. If you cannot name it, you are in Understand.
2. **Read the matching line in the phase table below.** It names one to four
   skills.
3. **Read the skill file** at `D:/repo/skills-hub/skills/<name>/SKILL.md` before
   running its procedure. Do not work from memory of what it probably says.
4. **Say which skill you are using**, in one clause: "Using `fix-this-bug`, the
   root-cause-first path." If the skill has a checklist, make a todo per item.

## Phase table

Every skill in the hub appears exactly once. Two are always on.

| Phase | Enter when | Skills |
|---|---|---|
| **Always on** | every coding task | `write-less-code` — smallest complete change |
| **Always on** | every reply | `trim-my-output` — only when the user asks for it |
| **Understand** | the ask is vague, or you are filling in requirements yourself | `interview-me-properly` first; `discuss-on-new-idea` when there are no options yet |
| **Research** | you need facts you do not have, or a repo you do not know | `research-this-topic` for outside facts; `explore-this-repo` for this codebase |
| **Spec** | work is non-trivial and nothing is written down | `write-the-spec`; `write-the-domain-glossary` for vocabulary; `document-the-decision` for an ADR |
| **Plan** | a spec exists but the work is not sliced | `break-into-tasks`; `review-the-plan` to attack it; `design-the-interface` to compare designs |
| **Build** | about to write code | `build-it-test-first`; `build-in-small-steps` for multi-file work; `isolate-this-branch` first if the tree must stay clean; `fix-this-bug` for a known defect |
| **Debug** | something is broken and the cause is unknown | `debug-this-code`; escalate to `debug-the-stubborn-one` after two failed hypotheses |
| **Review** | code exists and is not yet trusted | `review-my-code` is the gate; add `check-my-security` for auth, input, secrets, storage; `receive-code-review` when the feedback is someone else's; `audit-the-whole-repo` for a one-shot sweep |
| **Verify** | about to claim it works | `prove-it-works` always; `test-every-surface` for API/CLI/job; `check-my-ui` for a browser surface; `make-it-accessible` before shipping UI |
| **Finish** | it works but feels like a demo | `finish-the-experience`; `polish-the-ui`; `make-it-fast` only when measured; `make-it-observable` before production |
| **Visualise** | a system, flow or schema needs a checked picture | `diagram-the-system` for architecture, sequence, dataflow, ERD, lifecycle, class, tree, timeline, waterfall and explainer views |
| **Docs** | writing prose a stranger must act on | `write-the-docs`; `deslop-the-writing` as a final pass on any prose |
| **Ship** | tests pass and it needs to reach the remote | `ship-it`; `guard-the-dangerous-stuff` before any destructive command |
| **Meta** | changing the skill set, the bar, or the process | `simplify-this-code`, `write-a-new-skill`, `set-the-quality-bar`, `split-across-agents`, `hand-off-to-next-session`, `watch-my-context` |

`route-to-the-right-skill` is the table itself, so it is listed here and nowhere
else.

## Re-route at these moments

Routing once at the start is not enough. Re-check when any of these happens:

- **A phase boundary is crossed.** Spec approved means you are in Build, not Spec.
- **Two attempts on the same problem failed.** That is `debug-this-code`, not a
  third guess.
- **The user changes what they want.** Back to Understand; the spec is stale.
- **You are about to say "done", "fixed", or "works".** That is `prove-it-works`,
  every time, before the words leave you.
- **You are about to run a command that deletes, overwrites, force-pushes, or
  resets.** That is `guard-the-dangerous-stuff`, before the command.
- **You are about to touch a file outside the stated scope.** That is a scope
  change; name it or stop.

## Gates

A phase is not finished because it feels finished. It is finished when its gate
passes.

| Gate | Passes when |
|---|---|
| Spec locked | `.gsd/SPEC.md` exists, or the change is under ~10 lines |
| Plan sliced | One slice named, with its own verification |
| Test written | A test fails for the right reason before the fix |
| Review passed | `review-my-code` ran on the actual diff, not from memory |
| Verified | The verification command and its output are in the message |
| Ship safe | `guard-the-dangerous-stuff` cleared the destructive step |

Name the gate that blocks you. Do not silently carry an unmet gate forward.

## Red flags

These thoughts mean stop. Each one is a rationalisation, and the reality column is
why it is wrong.

| Thought | Reality |
|---|---|
| "This is just a simple question" | Then the check takes ten seconds and passes. Do it. |
| "I need more context first" | The skill tells you how to gather it. Check first. |
| "Let me just look at the code" | Skills define what to look for. Check first. |
| "It's a one-line fix, no ceremony" | Possibly true. That is the check's conclusion, not its replacement. |
| "I know this skill already" | Skills change. Read the current file. |
| "The skill is overkill here" | Overkill is a conclusion you reach after reading it. |
| "I'll invoke it once I'm sure it applies" | Certainty comes from reading it. |
| "Reading it would slow me down" | Rework from the wrong approach is slower. |
| "I already did the work, invoking now is theatre" | Then say so and run the gate; do not skip it. |
| "The user wants speed, not process" | A wrong answer delivered fast is not fast. |

## Working with dsh's bundled skills

Twelve skills ship with the harness and are not part of this hub's 42. Route to
them the same way; they are not competitors:

- `office`, `office-docx`, `office-xlsx`, `office-pptx`, `office-export-pdf`,
  `office-recalculate`, `office-render` - document work. Any `.docx`, `.xlsx`,
  `.pptx` or PDF request goes here first.
- `cordis-plugin-development`, `cordis-composition-reference`,
  `editing-cordis-compositions` - plugin and preset authoring in this harness.
- `agent-experience` - writing the tool definitions, skills and context loaders
  themselves.
- `diagnose-windows-sandbox-acl` - a Windows sandbox denial that is not expected
  confinement.

## Failure modes

1. Checking after acting, then declaring the skill irrelevant.
2. Routing to a skill and then not following it.
3. Running a phase that was never entered - reviewing code no spec ever governed.
4. Carrying an unmet gate into the next phase.
5. Routing to a skill name that no longer exists. If a name here is missing from
   the catalog, this file is stale: say so and route by phase instead.
6. Treating this skill as the work. It is the map, not the territory.
