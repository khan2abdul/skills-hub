# Installing skills-hub into any agent

One page per tool. Each is written to be pasted whole into a chat with an
agent, so the agent can perform the setup itself.

| Tool | File | Skill location it reads |
|---|---|---|
| Claude Code | [claude-code.md](claude-code.md) | `.claude/skills/` or `~/.claude/skills/` |
| Cursor | [cursor.md](cursor.md) | `.cursor/skills/`; rules via User Rules (paste) |
| Kiro | [kiro.md](kiro.md) | `.kiro/steering/` |
| Cline | [cline.md](cline.md) | `~/.cline/skills/`; rules in `.clinerules/` |
| Kilo Code | [kilo-code.md](kilo-code.md) | `skills.paths` in `kilo.json`; legacy `.kilocode/rules-*/` |
| DeepSeek Harness | [deepseek-harness.md](deepseek-harness.md) | `customSkillDirs` in the profile patch |
| Gemini CLI | [gemini-cli.md](gemini-cli.md) | `GEMINI.md` + extension dir |
| OpenAI Codex CLI | [codex-cli.md](codex-cli.md) | `AGENTS.md` |
| Windsurf | [windsurf.md](windsurf.md) | `.windsurf/rules/` |
| Any other | [generic.md](generic.md) | paste `SKILL.md` into the agent's rules |

## The `/` rule

Every skill in this hub ships so it can be invoked as `/<name>`. A skill that
cannot be invoked that way is a defect. `verify.py` fails the build on it.

Read [invoking-with-slash.md](invoking-with-slash.md) for what makes a skill
slashable, the per-tool matrix, and what to do when `/<name>` does not appear.
Only DeepSeek Harness is proven end-to-end; the other tools' slash mechanics are
documented but unverified.

## Before you start

The source repos live inside the hub at `repos/`. If that folder is empty (a
fresh clone), fetch the sources first:

```bash
python3 tools/clone_repos.py
```

Then prove the hub is trustworthy:

```bash
python3 tools/verify.py
```

It must print `OK: every shipped body is proven against upstream`.
If it fails, do not install this into a tool.

You only need `repos/` for vendoring and verification. Installing skills into an
agent reads `skills/`, so you can skip the clone if the hub already has what you
want and you trust the last verify run.

## The one rule

**No skill text is ever edited.** A shipped skill is either a verbatim copy
(only the `name:` line differs from upstream) or a composition of verbatim
excerpts with per-block sha256 proofs. `verify.py` proves both on every run. If
a tool requires a different file format (Cursor `.mdc`, Kiro steering), wrap the
body — never rewrite it.

## What "skills" means per tool

Claude Code, DeepSeek Harness, Gemini CLI and Kilo Code 7.8+ have a true
directory-scanned skill concept. The others load **rules** or **steering**: a
flat set of always-on markdown. For those, install only the handful you want
always-on (see each page's "recommended subset") and keep the rest as
on-demand references, or you will spend your whole context window on trigger
text.
