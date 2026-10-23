# Invoking a hub skill with `/`

The rule for this repo: **every skill ships as `/<name>`.** A skill that cannot be
invoked as `/<name>` is a defect, not a preference.

## What makes a skill slashable

Two things, both enforced by `tools/verify.ps1`:

1. **`name:` must be kebab-case and equal the directory name.** Discovery only
   finds `<root>/<name>/SKILL.md`, and a name that is not kebab-case is dropped
   with a warning.
2. **The invocation policy must permit the user surface.** In dsh, omitted
   `user-invocable` **defaults to true**, so doing nothing is already correct.
   Only `user-invocable: false` removes the skill from `/`.

```powershell
# fails the build if any shipped skill cannot be invoked as /<name>
& "$hub/tools/verify.ps1"
```

`disable-model-invocation: true` is fine and does **not** break `/` — it hides the
skill from the model while leaving it user-invocable, which is exactly how you
build a slash-only skill.

## Per-tool matrix

| Tool | Has `/<name>`? | How it reaches the skill | Verified |
|---|---|---|---|
| DeepSeek Harness | **yes** | native skill provider; `/name` token or `/` menu | yes — config schema + live catalog |
| Claude Code | **yes** | `~/.claude/skills/<name>/SKILL.md` is exposed as `/<name>` | partly — dir layout seen, not run |
| Kiro | no | steering documents only, read as context | no |
| Cursor | no | rules (`.cursor/rules/*.mdc`), read by glob/alwaysApply | no |
| Cline | no | rules + workflows | no |
| Kilo Code | no | rules + workflows | no |
| Windsurf | no | rules + workflows | no |
| Codex CLI | no | `AGENTS.md` context | no |
| Gemini CLI | no | `GEMINI.md` context (+ extensions) | no |
| generic | no | whatever the tool reads | no |

**Read the verified column honestly.** Only the DeepSeek Harness row is proven by
running it here. The rest reflect what each page already documents; their slash
mechanics were not executed, and no upstream docs were reachable while writing
this. Do not treat an unverified row as a promise.

## If your tool has no `/`

Do not fake one. A "slash command" you invent is a prompt with extra steps. Pick
the honest option:

- **Rules-based tools** — use the index rule from that tool's page. The model
  reads the matching `SKILL.md` when the topic appears. You lose the explicit
  trigger, not the skill.
- **Tools with a real command mechanism** — if and only if the tool documents
  one, wrap the body in that format. The wrapper changes, the body does not.
  Confirm the exact directory and file format in the tool's own docs first; the
  formats differ and an unrecognised one silently does nothing.

## A skill added mid-session will not appear in `/`

The DeepSeek Harness Web client caches the skill catalog per session, and a new
`SKILL.md` on disk forwards no event to it:

> Catalog changes without a forwarded event keep cached catalogs — adding or
> removing a `SKILL.md` on disk forwards no event at all, so an open session
> lists its previous skills until a preset switch, plugin manager operation, or
> connection reset.

So when `/` looks stale:

1. Reload the page (`Ctrl+R`), or switch agent preset.
2. If still missing, run `verify.ps1` — the frontmatter is the next suspect.
3. Restart the app only if both of those fail.

Restarting is the answer people reach for first and it is almost never the fix.
