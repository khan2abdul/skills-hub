# DeepSeek Harness (dsh)

> Paste this whole file into a dsh session and say: **"set this up for me."**

## What dsh reads

dsh has a real skill provider — `@deepseek-ai/dsh-skill-filesystem` — that scans
ranked roots and indexes any `<root>/<name>/SKILL.md`:

| Rank | Source | Path |
|---|---|---|
| 100 | project-dsh | `<projectRoot>/.dsh/skills` |
| 200 | project-agents | `<projectRoot>/.agents/skills` |
| 300 | **custom** | `Config.customSkillDirs` |
| 400 | user-dsh | `~/.dsh/skills` |
| 500 | user-agents | `~/.agents/skills` |

Discovery is **one level deep**. `<root>/<name>/SKILL.md` is found;
`<root>/a/b/SKILL.md` is not. Project root is the nearest ancestor containing `.git`.

**A root that does not exist is silently skipped — not an error.** This is the
most common reason skills "don't appear".

## 0. Find the hub

Everything below uses `$hub`. Resolve it once (idempotent - safe to re-run):

```powershell
$hub = $env:SKILLS_HUB
if (-not $hub) {
  $d = Get-Item .
  while ($d -and -not (Test-Path (Join-Path $d.FullName 'skills-hub/tools/verify.ps1'))) { $d = $d.Parent }
  if ($d) { $hub = Join-Path $d.FullName 'skills-hub' }
}
if (-not $hub -or -not (Test-Path "$hub/skills")) { $hub = Read-Host 'Path to your skills-hub checkout' }
"hub: $hub"
if (-not (Test-Path "$hub/skills")) { throw "no skills/ under $hub" }
```

## Install (recommended: user-dsh root)

`~/.dsh/skills` is rank 400 and is scanned in every project, with no config edit.
It does not exist by default, so create it:

```powershell
$dst = "$HOME/.dsh/skills"
New-Item -ItemType Directory -Force -Path $dst | Out-Null
Get-ChildItem "$hub/skills" -Directory | ForEach-Object {
  Copy-Item $_.FullName -Destination (Join-Path $dst $_.Name) -Recurse -Force
}
```

Watching is on by default, so the catalog refreshes without a restart.

## Invoke a skill with `/`

Every hub skill is reachable as `/<name>` — type it as a standalone word in the
composer (space or start of message before it, space or Enter after):

```
/debug-this-code
/write-less-code
```

Pressing `/` opens the skill menu. Picking from the menu and typing the token
send the same literal text; the host loads the skill either way.

If `/<name>` never appears, the frontmatter is at fault, not the install. Run
this and fix anything it names:

```powershell
& "$hub/tools/verify.ps1"
```

Both invocation keys default to permitting their surface, so an omitted
`user-invocable` is already correct. Only `user-invocable: false` removes a skill
from `/`, and `verify.ps1` now fails on it.

**A skill added mid-session will not show in `/` until the page reloads.** The
Web client caches the catalog per session, and a new `SKILL.md` on disk forwards
no event. Press `Ctrl+R`, or switch agent preset. Restarting dsh is not needed.

Verify with the harness's own inspector:

```
cordis_inspect_query platform=host provider=Config method=listConfigs
```

or simply confirm each `SKILL.md` parses:

```powershell
Get-ChildItem "$HOME/.dsh/skills" -Directory | ForEach-Object {
  $f = Join-Path $_.FullName 'SKILL.md'
  $state = if (Test-Path $f) { 'ok' } else { 'MISSING' }
  "{0,-32} {1}" -f $_.Name, $state
}
```

## Install (alternative: customSkillDirs)

Use this when you want the hub path recorded in the profile instead of copied.

Edit the active profile patch — find the profile name first:

```powershell
Get-ChildItem "$HOME/.dsh/profiles" -Directory | Select-Object Name
```

Then in `~/.dsh/profiles/<profile>/cordis.patch.yml`:

```yaml
- id: skill-filesystem
  name: "@deepseek-ai/dsh-skill-filesystem"
  disabled: false
  config:
    includeDefaultRoots: false
    customSkillDirs:
      - D:/repo/skills-hub/skills
```

Back it up first — this one file affects every session in that profile:

```powershell
$f = "$HOME/.dsh/profiles/<profile>/cordis.patch.yml"
Copy-Item $f "$f.bak-$(Get-Date -Format yyyyMMdd-HHmmss)"
```

### Two things that bite

**`customSkillDirs` only adds a root — it never removes one.** Without
`includeDefaultRoots: false`, `~/.dsh/skills`, `~/.agents/skills*` and the
project-level `.dsh/skills` + `.agents/skills` roots are still scanned, so any
skill already sitting there stays in the catalog alongside the hub's. Set the
flag when the hub is meant to be the whole catalog.

**Turning off that flag does not remove the bundled skills.** dsh's own skills
(`office*`, the cordis authoring set, `agent-experience`,
`diagnose-windows-sandbox-acl`) come from the `@deepseek-ai/dsh-agent-preset`
plugin, whose *own* provider declaration swaps in the preset's `skills`
directory as a custom root. They are not a default root and no
`skill-filesystem` setting affects them. To retire one, disable that provider
entry in the preset rather than editing this patch.

`bundledSkillDir` is worth knowing for the same reason: the filesystem provider
only reads it when `includeDefaultRoots` is true, so setting the flag to false
also drops whatever that variable pointed at.

## Verify it actually indexed

The dsh skill catalog appears in the session as a list of `<name>: description`
entries. If the count does not match the hub, check in this order:

1. Does the root directory exist? (a missing root is skipped silently)
2. Is it exactly `<root>/<name>/SKILL.md` — one level, no nesting?
3. Does the frontmatter have both `name:` and `description:`? Missing either
   drops the skill with only a warning.
4. Is `name:` kebab-case and equal to the directory name?
5. Does the skill set `disable-model-invocation: true`? That hides it from the
   model catalog by design (still user-invocable).
6. Does `description:` contain a colon followed by a space, unquoted? That is
   invalid YAML and dsh drops the skill with only a logged warning. Quote the
   value — `tools/compose.ps1` does this for composed skills.

## Optional: always-on routing

dsh also loads `~/.dsh/AGENTS.md` globally and `AGENTS.md`/`CLAUDE.md` per
project. Copy the router there if you want phase routing always present:

```powershell
Copy-Item "$hub/MASTER_ROUTING.md" -Destination "./CLAUDE.md" -Force
```

## Recommended subset

dsh indexes the whole hub comfortably. If you want a smaller catalog, vendor
only the phases you use and point `customSkillDirs` at a filtered directory.

## Uninstall

```powershell
Get-ChildItem "$HOME/.dsh/skills" -Directory |
  Where-Object { Test-Path "$hub/skills/$($_.Name)" } |
  Remove-Item -Recurse -Force
```

## Notes

- Do not point `customSkillDirs` at `$hub` itself — the hub root
  contains `tools/` and `setup/`, which are not skill bundles. Point it at
  `$hub/skills`.
- The provider watches at depth 1. Editing a `SKILL.md` body refreshes the next
  catalog; editing files under `references/` does not.
