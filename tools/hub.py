#!/usr/bin/env python3
"""One entry point. Runs the hub's checks in the order that makes failures actionable.

Port of tools/hub.ps1.

  hub.py                 -> health check (harvest + verify + coverage + rating + catalog)
  hub.py --setup <tool>  -> print the install page for a tool and stop
  hub.py --tools         -> list available install pages
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hubcommon as C  # noqa: E402

RED, GREEN, YELLOW, CYAN, RESET = "\033[31m", "\033[32m", "\033[33m", "\033[36m", "\033[0m"


def _pages(setup_dir: Path) -> list[Path]:
    if not setup_dir.is_dir():
        return []
    return sorted(p for p in setup_dir.glob("*.md") if p.name != "README.md")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--setup", default="")
    ap.add_argument("--tools", action="store_true")
    args = ap.parse_args(argv)

    hub = C.get_hub_root()
    setup_dir = hub / "setup"

    if args.tools:
        print(f"{CYAN}Install pages in {setup_dir} :{RESET}")
        for p in _pages(setup_dir):
            first = C.read_text(p).split("\n", 1)[0]
            print(f"  {p.stem:<22} {first}")
        return 0

    if args.setup:
        page = setup_dir / f"{args.setup}.md"
        if not page.is_file():
            print(f"{RED}no page for '{args.setup}'. Available:{RESET}")
            for p in _pages(setup_dir):
                print(f"  {p.stem}")
            return 1
        print(C.read_text(page))
        return 0

    import harvest
    import verify
    import coverage
    import rate_skills
    import catalog

    fail = 0

    def step(title: str, fn) -> int:
        print(f"{CYAN}--- {title} ---{RESET}")
        return fn()

    code = step("harvest", lambda: harvest.main([]))
    if code == 2:
        print()
        print(f"{YELLOW}The source repos are not cloned yet. Run this once:{RESET}")
        print(f"{YELLOW}  python tools/clone_repos.py{RESET}")
        return 2
    if code != 0:
        fail += 1

    print()
    code = step("verify", lambda: verify.main([]))
    if code == 2:
        print()
        print(f"{YELLOW}The source repos are not cloned yet. Run this once:{RESET}")
        print(f"{YELLOW}  python tools/clone_repos.py{RESET}")
        return 2
    if code != 0:
        fail += 1

    print()
    code = step("coverage", lambda: coverage.main([]))
    if code == 2:
        print()
        print(f"{YELLOW}The source repos are not cloned yet. Run this once:{RESET}")
        print(f"{YELLOW}  python tools/clone_repos.py{RESET}")
        return 2
    if code != 0:
        fail += 1

    print()
    code = step("rating", lambda: rate_skills.main([]))
    if code == 2:
        print()
        print(f"{YELLOW}No skills to rate. Run tools/vendor.py --all first.{RESET}")
        return 2
    if code != 0:
        fail += 1

    print()
    code = step("catalog", lambda: catalog.main([]))
    if code != 0:
        fail += 1

    print()
    if fail > 0:
        print(f"{RED}HUB NOT HEALTHY{RESET}")
        return 1
    print(f"{GREEN}HUB HEALTHY{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
