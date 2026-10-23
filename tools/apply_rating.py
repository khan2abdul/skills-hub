#!/usr/bin/env python3
"""Reads RATING.json and applies the fixes it can apply without editing a skill body.

Port of tools/apply-rating.ps1.

The hub's core guarantee is that skill text is immutable, so this tool
deliberately cannot touch SKILL.md: every fix here copies or deletes files
AROUND the body, and re-runs verify.py to prove nothing drifted.

  apply_rating.py                 -> show what would change
  apply_rating.py --apply         -> do it, then verify
  apply_rating.py --apply --only debug-this-code

Unapplied findings (VENDOR-HELPER, BIGGER-CANDIDATE, SLASH-ONLY, EMPTY-BODY)
need a decision, not a script: they are printed as TODO.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hubcommon as C  # noqa: E402

RED, GREEN, YELLOW, CYAN, DARKGRAY, RESET = (
    "\033[31m", "\033[32m", "\033[33m", "\033[36m", "\033[90m", "\033[0m"
)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--only", default="")
    args = ap.parse_args(argv)

    hub = C.get_hub_root()
    rating_file = hub / "RATING.json"
    if not rating_file.is_file():
        print(f"{RED}no RATING.json - run tools/rate_skills.py first{RESET}")
        return 2
    rating = json.loads(C.read_text(rating_file))

    # Guard: a stale report must not be applied to a skill set that has changed.
    skills_now = sum(1 for p in (hub / "skills").iterdir() if p.is_dir() and (p / "SKILL.md").is_file())
    if rating["summary"]["count"] != skills_now:
        print(f"{RED}RATING.json is stale: it rated {rating['summary']['count']} skills, {skills_now} exist.{RESET}")
        print(f"{YELLOW}Re-run tools/rate_skills.py.{RESET}")
        return 1

    fixes = [f for s in rating["skills"] for f in s.get("fixes") or [] if f]
    if args.only:
        fixes = [f for f in fixes if f["skill"] == args.only]

    todos = [p for p in rating["plan"] if not p["auto"]]
    if args.only:
        todos = [p for p in todos if p["skill"] == args.only]

    print(f"{CYAN}=== apply-rating ==={RESET}")
    print(f"rated   : {rating['generated']}  rubric v{rating['rubric_version']}  mean {rating['summary']['mean']}")
    print(f"apply   : {len(fixes)} automatic, {len(todos)} need a decision")
    print()

    if not fixes:
        print(f"{GREEN}nothing to apply automatically.{RESET}")
    else:
        done = 0
        skipped = 0
        errors: list[str] = []
        for f in fixes:
            src = hub / f["source"]
            dst = hub / "skills" / f["target"]
            if not src.exists():
                errors.append(f"{f['skill']}: source missing {f['source']}")
                continue
            if dst.exists() and not args.apply:
                print(f"{YELLOW}SKIP  {f['skill']:<24} {f['ref']} (exists){RESET}")
                skipped += 1
                continue
            if not args.apply:
                print(f"{CYAN}WOULD {f['skill']:<24} copy {f['source']} -> {f['target']}{RESET}")
                done += 1
                continue
            # payload only: refuse to overwrite a SKILL.md even if the JSON asks
            if dst.name == "SKILL.md":
                errors.append(f"{f['skill']}: refusing to overwrite SKILL.md (bodies are immutable)")
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"{GREEN}OK    {f['skill']:<24} {f['ref']}{RESET}")
            done += 1

        print()
        print(f"applied: {done}  skipped: {skipped}  errors: {len(errors)}")
        for e in errors:
            print(f"  {RED}{e}{RESET}")
        if errors:
            return 1

    if todos:
        print()
        print(f"{YELLOW}=== needs a decision (not auto-applied) ==={RESET}")
        grouped: dict[str, list[dict]] = {}
        for t in todos:
            grouped.setdefault(t["finding"], []).append(t)
        for finding in sorted(grouped):
            group = grouped[finding]
            print()
            print(f"{YELLOW}{finding} ({len(group)}){RESET}")
            for t in group:
                print(f"  {t['skill']}: {t['message']}")
                if t["command"]:
                    print(f"    {DARKGRAY}-> {t['command']}{RESET}")

    if args.apply:
        print()
        print(f"{CYAN}--- verify ---{RESET}")
        import verify
        if verify.main() != 0:
            print(f"{RED}verify failed after applying - the fix changed something it should not have{RESET}")
            return 1
        print()
        print(f"{CYAN}re-run tools/rate_skills.py to see the new scores.{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
