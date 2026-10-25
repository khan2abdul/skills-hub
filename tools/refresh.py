#!/usr/bin/env python3
"""Maintainer flow: clone the nine sources, then rebuild the catalogue.

This is not part of the install. An install copies nothing from upstream, so it
needs no `repos/`. This command restores the proof that every shipped body is an
unmodified copy, and rewrites the files that describe the catalogue.

Run: python tools/refresh.py
     python tools/refresh.py --skip-clone
     python tools/refresh.py --dry-run
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hubcommon as C  # noqa: E402

RED, GREEN, YELLOW, CYAN = "\033[31m", "\033[32m", "\033[33m", "\033[36m"
RESET = "\033[0m"

# Order matters: bodies are harvested before anything reads them, and the
# catalogue is rebuilt from verified bodies, so verify runs before catalog.
STEPS = [
    ("clone", ["clone_repos.py"], "fetch the nine sources"),
    ("harvest", ["harvest.py"], "rebuild every skill body"),
    ("verify", ["verify.py"], "prove each body against upstream"),
    ("coverage", ["coverage.py"], "rewrite COVERAGE.md"),
    ("rate", ["rate_skills.py"], "rewrite RATING.md and RATING.json"),
    ("catalog", ["catalog.py"], "rewrite SKILLS.md"),
]


def run_step(name: str, args: list[str], why: str, dry_run: bool) -> int:
    cmd = [sys.executable, str(HERE / args[0])]
    print(f"{CYAN}==> {name}: {why}{RESET}")
    if dry_run:
        print(f"{YELLOW}    would run: {' '.join(cmd)}{RESET}")
        return 0
    proc = subprocess.run(cmd)
    if proc.returncode != 0:
        print(f"{RED}    {name} failed with exit {proc.returncode}{RESET}")
    return proc.returncode


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    dry_run = "--dry-run" in args
    skip_clone = "--skip-clone" in args

    hub = C.get_hub_root()
    print(f"{CYAN}=== skills-hub refresh ==={RESET}")
    print(f"hub: {hub}")

    steps = [s for s in STEPS if not (skip_clone and s[0] == "clone")]
    for name, cmd, why in steps:
        code = run_step(name, cmd, why, dry_run)
        if code != 0:
            # Stop at the first failure: later steps read what this one wrote,
            # so running them would publish a catalogue built from bad input.
            print(f"{RED}Stopped at '{name}'. Nothing after it ran.{RESET}")
            return code
    if dry_run:
        print(f"{YELLOW}Dry run: nothing was written.{RESET}")
        return 0
    print(f"{GREEN}Refresh complete.{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
