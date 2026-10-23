#!/usr/bin/env python3
"""Scores a debugging skill against a fixed rubric of practices that matter.

Port of tools/evaluate.ps1. Read-only.
"""
from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hubcommon as C  # noqa: E402

CYAN, RESET = "\033[36m", "\033[0m"

# name, weight, pattern, why it matters
RUBRIC = [
    ("Reproduce before fixing", 3, r'(?i)reproducable|reproduce|repro\b', "without a red signal you are guessing"),
    ("Refuse symptom fixes", 3, r'(?i)root cause|symptom fix|not the symptom', "the single most common failure"),
    ("Minimise the repro", 2, r'(?i)minimi[sz]e|minimal (repro|case|example)', "shrinks the hypothesis space"),
    ("Build a tight loop", 3, r'(?i)feedback loop|tight(er)? loop|red-capable', "turns debugging from staring into testing"),
    ("Ranked hypotheses (3+)", 3, r'(?i)3-5|three to five|ranked hypotheses|multiple hypotheses|several hypotheses', "single-hypothesis anchors on the first idea"),
    ("One variable at a time", 2, r'(?i)one variable|single (change|variable)', "confounded tests prove nothing"),
    ("Targeted instrumentation", 2, r'(?i)instrument|targeted log|tag every|prefix', '"log everything and grep" is not a method'),
    ("Non-deterministic handling", 3, r'(?i)non-?deterministic|flaky|intermittent|race', "most real bugs are flaky"),
    ("Regression test for bug", 3, r'(?i)regression test|failing test|test that (fails|catches)', "stops it coming back"),
    ("Verify end-to-end", 2, r'(?i)end-to-end|full (test )?suite|re-run', "a green unit test is not a fixed bug"),
    ("Cleanup instrumentation", 1, r'(?i)remov(e|ing) .*(instrument|log)|cleanup|delete.*prototype', "debug code leaks to prod"),
    ("Question architecture", 2, r'(?i)architectur(e|al)', "3 failed fixes means the design is wrong"),
    ("Error output untrusted", 2, r'(?i)untrusted|do not (execute|follow)|embedded instruction', "prompt injection via stack traces"),
    ("Redact secrets", 2, r'(?i)redact|<REDACTED>|secret', "debugging leaks credentials"),
    ("Anti-rationalisation", 2, r'(?i)rationali[sz]ation|red flag|excuse', "names the shortcuts agents take"),
    ("Triage by layer", 2, r'(?i)which layer|locali[sz]e|bisect', "narrows where to look"),
]


def strip_frontmatter(raw: str) -> str:
    return re.sub(r'\A---\r?\n.*?\r?\n---\r?\n', '', raw, count=1, flags=re.S)


def get_score(path: str) -> dict | None:
    p = Path(path)
    if not p.exists():
        return None
    body = strip_frontmatter(C.read_text(p))
    got = 0
    maximum = 0
    covered = 0
    for name, w, pat, _why in RUBRIC:
        maximum += w
        if re.search(pat, body):
            got += w
            covered += 1
    return {
        "file": path,
        "name": Path(path).parent.name,
        "chars": len(body),
        "tokens": round(len(body) / 4),
        "score": got,
        "max": maximum,
        "pct": C.ps_round(100 * got / maximum),
        "covered": covered,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default="", help="score one file instead of the default set")
    args = ap.parse_args(argv)

    hub = C.get_hub_root()
    loaded = C.read_repos(hub / "repos.toml")
    index = C.get_skill_index(loaded["repos"])

    files: list[str] = []
    composed = hub / "skills" / "debug-this-code" / "SKILL.md"
    if composed.is_file():
        files.append(str(composed))

    if args.file:
        files = [args.file]
    else:
        for n in ("debugging-and-error-recovery", "systematic-debugging", "diagnosing-bugs",
                  "debug-like-expert", "investigate-first"):
            if n in index:
                files.append(index[n]["file"])

    rows = [r for r in (get_score(f) for f in files) if r]
    if not rows:
        print("no files scored", file=sys.stderr)
        return 1

    print(f"{CYAN}=== rubric: {len(RUBRIC)} practices, max {rows[0]['max']} points ==={RESET}")
    # Ties keep a stable, name-based order. PowerShell's Sort-Object is not
    # stable, so its tie order varied between runs; the scores are identical.
    rows.sort(key=lambda r: (-r["pct"], r["name"]))

    # Format-Table -AutoSize equivalent: text columns left, numeric columns
    # right (PowerShell right-aligns anything it infers as a number), two-space
    # gap between columns.
    heads = ["skill", "pts", "cover%", "items", "chars", "~tok"]
    numeric = [False, True, True, False, True, True]
    table = []
    for r in rows:
        table.append([
            r["name"], f"{r['score']}/{r['max']}", str(r["pct"]),
            f"{r['covered']}/{len(RUBRIC)}", str(r["chars"]), str(r["tokens"]),
        ])
    widths = [max(len(h), *(len(row[i]) for row in table)) for i, h in enumerate(heads)]
    gap = "  "

    def fmt(cells):
        return gap.join(
            str(c).rjust(w) if num else str(c).ljust(w)
            for c, w, num in zip(cells, widths, numeric)
        )

    print(fmt(heads))
    print(fmt(["-" * w for w in widths]))
    for row in table:
        print(fmt(row))

    # per-item matrix so a win is auditable, not asserted
    print(f"{CYAN}=== per-practice coverage ==={RESET}")
    hdr = "practice".ljust(30)
    for r in rows:
        hdr += r["name"][: min(9, len(r["name"]))].rjust(10)
    print(hdr)

    bodies = {r["name"]: strip_frontmatter(C.read_text(r["file"])) for r in rows}
    for name, _w, pat, _why in RUBRIC:
        line = name.ljust(30)
        for r in rows:
            line += ("yes" if re.search(pat, bodies[r["name"]]) else ".").rjust(10)
        print(line)

    return 0


if __name__ == "__main__":
    sys.exit(main())
