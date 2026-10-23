#!/usr/bin/env python3
"""Reports what the source repos contain versus what the manifest claims.

Port of tools/harvest.ps1. Read-only. Never writes skills/ and never edits
manifest.yml.
  harvest.py              -> drift report + unclaimed candidates
  harvest.py --new-repo X -> also list skills from repo X not in the manifest
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hubcommon as C  # noqa: E402

RED, GREEN, YELLOW, CYAN, DARK = "\033[31m", "\033[32m", "\033[33m", "\033[36m", "\033[90m"
RESET = "\033[0m"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--new-repo", default="", help="also list skills from repo X")
    args = ap.parse_args(argv)

    hub = C.get_hub_root()
    loaded = C.read_repos(hub / "repos.toml")
    repos = loaded["repos"]
    manifest = C.read_manifest(hub / "manifest.yml")
    sources_root = loaded["sourcesRoot"]

    print(f"sources root   : {sources_root}")

    if not Path(sources_root).exists():
        print()
        print(f"{RED}No sources root at that path. The 9 cloned repos are not on this machine.{RESET}")
        print(f"{YELLOW}Point at them with either:{RESET}")
        print(f"{YELLOW}  -e SKILLS_HUB_SOURCES   (environment variable, wins){RESET}")
        print(f"{YELLOW}  sources_root in repos.toml (relative to the hub, or absolute){RESET}")
        print(f"{YELLOW}Then re-run. Manifest entries are not validated until sources resolve.{RESET}")
        return 2

    # --- index every upstream skill actually on disk ---
    on_disk: dict[str, list[str]] = {}
    ref_count = 0
    for r in repos:
        if r.get("status") == "reference":
            ref_count += 1
            continue
        path = r.get("path")
        if not path or not Path(path).exists():
            print(f"{YELLOW}WARNING: repo missing: {r.get('name')} -> {path}{RESET}", file=sys.stderr)
            continue
        for root in r.get("roots") or []:
            p = Path(path) if root == "." else Path(path) / root
            if not p.is_dir():
                continue
            for d in sorted(p.iterdir()):
                if d.is_dir() and (d / "SKILL.md").is_file():
                    on_disk.setdefault(d.name, [])
                    if r["name"] not in on_disk[d.name]:
                        on_disk[d.name].append(r["name"])

    # --- claimed candidate that does not exist upstream = broken manifest ---
    broken: list[str] = []
    for s in manifest:
        for c in list(s.get("candidates") or []) + list(s.get("composed") or []):
            if not c:
                continue
            if c not in on_disk:
                broken.append(f"{s.get('name')} -> {c} (not found)")

    # --- on disk but claimed by nobody = candidate for a new manifest entry ---
    # "Claimed" means SHIPPED (proven by skills/<name>/PROVENANCE.md). A skill
    # that only appears in a `candidates` list was proposed and then lost;
    # counting it as claimed is how 72 upstream skills went missing with harvest
    # reporting zero.
    cov = C.get_skill_coverage()
    shipped, ignored = cov["shipped"], cov["ignored"]
    unclaimed = sorted(k for k in on_disk if k not in shipped and k not in ignored)
    suppressed = sum(1 for k in on_disk if k in ignored)

    cloned = sum(1 for r in repos if r.get("status") != "reference")
    merged_count = sum(1 for s in manifest if s.get("status") == "merged")

    print(f"{CYAN}=== skills-hub harvest ==={RESET}")
    print(f"repos          : {cloned} cloned, {ref_count} reference")
    print(f"upstream skills: {len(on_disk)}")
    print(f"manifest needs : {len(manifest)}")
    print(f"shipped        : {len(shipped)} upstream skills -> {merged_count} canonical names")
    print(f"ignored        : {suppressed} (rejected, reason in ignore.txt)")
    print(f"dropped        : {len(unclaimed)} (neither shipped nor rejected)")
    print()

    col = RED if broken else GREEN
    print(f"{col}=== BROKEN: manifest cites a skill that is not on disk ({len(broken)}) ==={RESET}")
    for b in broken:
        print(f"  {RED}{b}{RESET}")

    print()
    col = YELLOW if unclaimed else GREEN
    print(f"{col}=== DROPPED: on disk, not shipped, not rejected ({len(unclaimed)}, {suppressed} ignored) ==={RESET}")
    print(f"{DARK}  give each one a decision: ship it, fold it into a shipped skill, or add it to ignore.txt{RESET}")
    for u in unclaimed:
        print(f"  {YELLOW}{u:<34} {', '.join(on_disk[u])}{RESET}")

    print()
    print(f"{CYAN}=== MERGED entries whose source is gone ==={RESET}")
    gone = [s for s in manifest if s.get("status") == "merged" and s.get("chosen") and s["chosen"] not in on_disk]
    if gone:
        for s in gone:
            print(f"  {RED}{s.get('name')} <- {s['chosen']} MISSING{RESET}")
    else:
        print(f"  {GREEN}none{RESET}")

    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
