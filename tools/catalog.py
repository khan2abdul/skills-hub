#!/usr/bin/env python3
"""Writes SKILLS.md: what every shipped skill does, where it came from, and -
for composed skills - which sections were combined.

Port of tools/catalog.ps1.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hubcommon as C  # noqa: E402
import hubrubric as R  # noqa: E402

GREEN, RESET = "\033[32m", "\033[0m"

# The order a reader meets the skills, not alphabetical.
PHASES = {
    "Understand": ["interview-me-properly", "discuss-on-new-idea", "explore-this-repo", "research-this-topic"],
    "Define": ["write-the-spec", "write-the-domain-glossary", "design-the-interface",
               "document-the-decision", "write-the-docs"],
    "Visualise": ["diagram-the-system"],
    "Plan": ["break-into-tasks", "review-the-plan", "set-the-quality-bar"],
    "Build": ["build-it-test-first", "build-in-small-steps", "write-less-code", "simplify-this-code",
              "split-across-agents", "isolate-this-branch"],
    "Finish": ["finish-the-experience"],
    "Debug": ["debug-this-code", "debug-the-stubborn-one", "fix-this-bug"],
    "Review": ["review-my-code", "receive-code-review", "check-my-security", "audit-the-whole-repo",
               "prove-it-works", "test-every-surface"],
    "UI": ["check-my-ui", "polish-the-ui", "landing-page-design", "design-to-motion",
           "make-it-accessible", "make-it-fast"],
    "Operate": ["make-it-observable", "ship-it", "guard-the-dangerous-stuff", "hand-off-to-next-session"],
    "Meta": ["watch-my-context", "trim-my-output", "route-to-the-right-skill", "write-a-new-skill",
             "deslop-the-writing"],
}


def clean_section(s: str) -> str:
    s = s.strip()
    if s.startswith("file:"):
        s = s[5:].replace("#", ": ")
    out = re.sub(r'^#+\s*', '', s).strip()
    return out if out else "whole body"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--what-if", action="store_true")
    args = ap.parse_args(argv)

    hub = C.get_hub_root()
    skills_dir = hub / "skills"
    loaded = C.read_repos(hub / "repos.toml")
    index = C.get_skill_index(loaded["repos"])

    scores: dict[str, float] = {}
    rating_file = hub / "RATING.json"
    if rating_file.is_file():
        rating = json.loads(C.read_text(rating_file))
        for r in rating.get("skills", []):
            scores[r["name"]] = r["score"]

    rows = []
    for d in sorted((p for p in skills_dir.iterdir() if p.is_dir()), key=lambda p: p.name):
        file = d / "SKILL.md"
        if not file.is_file():
            continue
        text = C.read_text(file)
        fm = R.get_frontmatter(text)
        desc = fm["keys"].get("description") or "(no description)"

        prov_file = d / "PROVENANCE.md"
        prov = C.read_text(prov_file) if prov_file.is_file() else ""
        mode = (re.search(r'(?m)^- mode:\s*(.+?)\s*$', prov) or [None, ""])[1]
        upstream = (re.search(r'(?m)^- upstream:\s*(.+?)\s*$', prov) or [None, ""])[1]
        repo = (re.search(r'(?m)^- repo:\s*(.+?)\s*$', prov) or [None, ""])[1]

        build = []
        if mode == "composed":
            grouped: dict[str, list[str]] = {}
            for m in re.finditer(
                r'(?m)^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*[0-9a-f]{64}\s*\|\s*([0-9]+)\s*\|', prov
            ):
                src = m.group(1).strip()
                sec = clean_section(m.group(2))
                grouped.setdefault(src, []).append(sec)
            for src, secs in grouped.items():
                src_repo = index[src]["repo"] if src in index else "unknown"
                build.append({"skill": src, "repo": src_repo, "sections": secs})

        rows.append({
            "name": d.name,
            "description": desc,
            "mode": mode,
            "upstream": upstream,
            "repo": repo,
            "build": build,
            "chars": C.ps_len(text),
            "score": scores.get(d.name),
        })

    by_name = {r["name"]: r for r in rows}
    verbatim = sum(1 for r in rows if r["mode"] == "verbatim")
    composed = sum(1 for r in rows if r["mode"] == "composed")
    authored = sum(1 for r in rows if r["mode"] == "authored")
    # The count must add up to the skill total. Reporting only verbatim and
    # composed read as "40 skills" for the hub once an authored entry
    # existed - exactly the kind of silent gap this file exists to expose.
    assert verbatim + composed + authored == len(rows), (
        f"provenance modes do not add up: {verbatim}+{composed}+{authored} of {len(rows)}"
    )
    tail = f"{composed} compositions"
    if authored:
        tail += f", {authored} authored"
    short = f"{verbatim} verbatim, {composed} composed"
    if authored:
        short += f", {authored} authored"

    out: list[str] = []

    def W(s: str = "") -> None:
        out.append(s)

    W("# Skill catalog")
    W("")
    W("What each shipped skill does, which upstream repo and skill it came from,")
    W("and - for composed skills - exactly which sections were combined.")
    W("")
    W("Generated by `tools/catalog.py` from `manifest.yml`,")
    W("`skills/*/PROVENANCE.md`, each `SKILL.md`, and `RATING.json`. Do not edit by")
    W("hand. Exact commits and per-block sha256 are in `skills/<name>/PROVENANCE.md`.")
    W("")
    W(f"**{len(rows)} skills: {verbatim} verbatim copies, {tail}.**")
    W("")

    mapped: list[str] = []
    for phase, names_in_phase in PHASES.items():
        names = [n for n in names_in_phase if n in by_name]
        if not names:
            continue
        mapped.extend(names)
        W(f"## {phase}")
        W("")
        for name in names:
            r = by_name[name]
            W(f"### `{name}`")
            W("")
            W(f"**What it does:** {r['description']}")
            W("")
            if r["mode"] == "composed":
                W(f"**Built from {len(r['build'])} upstream skills:**")
                W("")
                for b in r["build"]:
                    W(f"- `{b['skill']}` (`{b['repo']}`): {'; '.join(b['sections'])}")
                W("")
                W(f"**Compose spec:** `compose/{name}.yml`")
            elif r["mode"] == "verbatim":
                W(f"**Source:** `{r['repo']}` / `{r['upstream']}` - verbatim, name line only")
            else:
                W("**Source:** no PROVENANCE.md")
            W("")
            score = f"{r['score']}/10" if r["score"] is not None else "unrated"
            W(f"**Size:** {r['chars']} chars | **Score:** {score} | **Provenance:** `skills/{name}/PROVENANCE.md`")
            W("")

    other = sorted(r["name"] for r in rows if r["name"] not in mapped)
    if other:
        W("## Other")
        W("")
        for name in other:
            r = by_name[name]
            W(f"### `{name}`")
            W("")
            W(f"**What it does:** {r['description']}")
            W("")
            src_label = "composed" if r["mode"] == "composed" else f"`{r['repo']}` / `{r['upstream']}`"
            W(f"**Source:** {src_label}")
            W("")

    W("## Source repos")
    W("")
    W("| repo | URL |")
    W("|---|---|")
    for r in sorted((r for r in loaded["repos"] if r.get("status") == "cloned"), key=lambda r: str(r.get("name"))):
        W(f"| `{r.get('name')}` | {r.get('url')} |")
    W("")
    W("A verbatim skill is an unmodified copy: only the frontmatter `name:` line")
    W("changes. A composition quotes named sections byte-for-byte and records their")
    W("sha256. `tools/verify.py` re-extracts and re-hashes every block.")
    W("")

    text = "\n".join(out) + "\n"

    if args.what_if:
        print(f"WOULD write SKILLS.md ({len(rows)} skills: {short})")
        return 0

    C.write_text(hub / "SKILLS.md", text)
    print(f"{GREEN}wrote SKILLS.md{RESET}")
    print(f"  {len(rows)} skills: {short}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
