#!/usr/bin/env python3
"""Mutation check: does the suite catch each rule being removed?

Each mutant edits bootstrap.py in a way that should break a rule, runs the
tests, then restores the file. A mutant that survives is a missing test.

Run: python tools/mutation_check.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import hubcommon as C

HERE = Path(__file__).resolve().parent
TARGET = HERE / "bootstrap.py"

# (name, old, new, why the suite should notice)
MUTANTS = [
    (
        "untracked guard removed",
        "if region is None or not replace_untracked:",
        "if False:",
        "a file with no anchor would be rewritten instead of refused",
    ),
    (
        "idempotence short-circuit removed",
        "if existing[start:end] == block:",
        "if False:",
        "a second run would rewrite instead of reporting unchanged",
    ),
    (
        "comment boundary removed",
        "        if m.group(0).startswith(\"<!--\"):\n"
        "            return heading.start(), pos + m.start()\n",
        "",
        "a managed comment region after the style would be swallowed",
    ),
    (
        "heading anchor widened",
        're.search(r"(?m)^(#{1,6})\\s+Writing style\\s*$", text)',
        're.search(r"(?m)^(#{1,6})\\s+\\S+", text)',
        "any heading would anchor the region, so a wrong section is replaced",
    ),
    (
        "level comparison inverted",
        "if len(m.group(1)) <= level:",
        "if len(m.group(1)) >= level:",
        "the region would end at a deeper heading instead of a shallower one",
    ),
    (
        "detection always false",
        "    return {\n        t[\"tool\"]\n        for t in TOOLS\n        if any((home / s).exists() for s in t[\"signals\"])\n    }",
        "    return set()",
        "no tool would ever be detected, so nothing is written",
    ),
    (
        "detection ignores the signal",
        "if any((home / s).exists() for s in t[\"signals\"])",
        "if True",
        "an absent tool would be written to, creating stray config",
    ),
    (
        "unknown tool name accepted",
        "unknown = [n for n in args.only if n not in tool_names()]",
        "unknown = []",
        "a typo would silently select nothing instead of failing",
    ),
    (
        "non-tty gate fails open",
        "        if not sys.stdin.isatty():\n"
        '            print(f"{YELLOW}No terminal to confirm on. Re-run with --yes to apply.{RESET}")\n'
        "            return 1",
        "        if False:\n"
        "            return 1",
        "a piped run would write with no prompt",
    ),
    (
        "bare run skips the gate",
        "    if not args.yes:",
        "    if args.detect and not args.yes:",
        "a bare run, which install.ps1 makes, would write silently",
    ),
    (
        "existing folder overwritten",
        '            if not _same_content(dst, src):\n'
        "                # The user wrote this folder. Leave it, and say so.\n"
        '                results[src.name] = "kept"\n'
        "                continue",
        "            if False:\n                pass",
        "a skill folder the user wrote would be destroyed",
    ),
    (
        "invalid kilo json overwritten",
        '        except json.JSONDecodeError:\n            return "refused", f"{path} is not valid JSON; left alone"',
        "        except json.JSONDecodeError:\n            data = {}",
        "a config this tool cannot parse would be wiped",
    ),
    (
        "duplicate kilo path appended",
        "    if wanted in paths:\n        return \"unchanged\", wanted",
        "    if False:\n        return \"unchanged\", wanted",
        "every run would add the path again",
    ),
    (
        "filecount: no skills installed",
        "    skills = hub_skills(hub)\n    if not skills:\n        return 0",
        "    skills = []\n    if not skills:\n        return 0",
        "no skill would ever be linked",
    ),
    (
        "junction not recognised as ours",
        "    is_junction = getattr(entry, \"is_junction\", None)\n"
        "    if is_junction is not None:\n"
        "        return bool(is_junction())",
        "    return entry.is_symlink()",
        "a Windows junction looks like a user folder, so links are never repaired",
    ),
    (
        "stale link kept instead of repaired",
        "        if ours:\n",
        "        if ours and False:\n",
        "a link pointing at an old hub would survive",
    ),
    (
        "kilo wrong shape crashes",
        '    if not isinstance(paths, list):\n        return "refused", f"{path} has a non-list skills.paths; left alone"',
        "    if False:\n        pass",
        'a config with {"skills": {"paths": "x"}} would be rewritten',
    ),
    (
        "dsh wiring always not wired",
        "            if _norm_path(Path(raw)) == wanted:\n                return \"wired\"",
        "            if False:\n                return \"wired\"",
        "a wired profile would be reported as not wired",
    ),
    (
        "copy-into-itself allowed",
        "    if _inside(dst_root, src_root):\n"
        '        return {"refused": "destination is inside the skills source"}',
        "    if False:\n        pass",
        "a copy inside its own source would recurse to a path limit",
    ),
    (
        "file target overwrites a user file",
        "    if not _is_our_body(existing, body):\n        return \"kept\"",
        "    if False:\n        return \"kept\"",
        "a file the hub did not write would be destroyed",
    ),
    (
        "file ownership widened to a substring",
        "    return len(text_lines) <= len(body_lines)",
        '    return "ASD-STE100" in text',
        "any file that names the standard would be rewritten",
    ),
    (
        "file target rewrites an unchanged file",
        "    if _same_body(existing, body):\n        return \"unchanged\"",
        "    if False:\n        return \"unchanged\"",
        "a second run would rewrite the file instead of reporting unchanged",
    ),
    (
        "file target ignores line endings",
        '    return text.strip().replace("\\r\\n", "\\n") == body.strip().replace("\\r\\n", "\\n")',
        "    return text.strip() == body.strip()",
        "a correct CRLF copy would be reported as drift",
    ),
    (
        "file kind written as a block",
        '        if t["kind"] == "file":\n            result = apply_file(path, body)',
        '        if False:\n            result = apply_file(path, body)',
        "a file target would gain markers, so the hub no longer owns it whole",
    ),
    (
        "plan hides a write that --all makes",
        '        if name not in chosen:\n'
        '            lines.append(f"  {name:<9} {\'not detected\' if name not in present else \'not selected\':<22}skipped")\n'
        "            continue",
        '        if name not in chosen or name not in present:\n'
        '            lines.append(f"  {name:<9} {\'not detected\':<22}skipped")\n'
        "            continue",
        "the plan would print skipped for a tool the run then writes",
    ),
    (
        "user file reported as drift",
        "                elif _is_our_body(text, body):\n"
        '                    print(f"{RED}DRIFT {t[\'tool\']:<9} {path} differs from style/{RESET}")\n'
        "                    fail += 1",
        '                elif True:\n'
        '                    print(f"{RED}DRIFT {t[\'tool\']:<9} {path} differs from style/{RESET}")\n'
        "                    fail += 1",
        "check would say re-run to fix a file the run refuses to touch",
    ),
    (
        "cursor paste text never printed",
        "    for _ in paste:\n        print_cursor(body)",
        "    for _ in ():\n        print_cursor(body)",
        "the one manual step would never reach the user",
    ),
    (
        "cursor check stays silent",
        '                if t["tool"] in present:\n'
        '                    print(f"{YELLOW}manual    {t[\'tool\']:<9} paste into {CURSOR_RULES}{RESET}")',
        "                if False:\n"
        '                    print(f"{YELLOW}manual    {t[\'tool\']:<9} paste into {CURSOR_RULES}{RESET}")',
        "--check would not report the manual step the spec requires",
    ),
    (
        "uninstall deletes a user style file",
        "            if _is_our_body(C.read_text(path), body):\n"
        "                print(f\"{GREEN}{gone:<12}{t['tool']:<9} {path}{RESET}\")",
        "            if True:\n"
        "                print(f\"{GREEN}{gone:<12}{t['tool']:<9} {path}{RESET}\")",
        "a writing-style.md the user wrote would be deleted",
    ),
    (
        "uninstall keeps a hub style file",
        "            if _is_our_body(C.read_text(path), body):\n"
        "                print(f\"{GREEN}{gone:<12}{t['tool']:<9} {path}{RESET}\")",
        "            if False:\n"
        "                print(f\"{GREEN}{gone:<12}{t['tool']:<9} {path}{RESET}\")",
        "uninstall would leave every style file behind",
    ),
    (
        "uninstall removes a link outside the hub",
        "        if not _inside(target, hub_root):\n"
        '            results[entry.name] = "kept"\n'
        "            continue",
        "        if False:\n"
        '            results[entry.name] = "kept"\n'
        "            continue",
        "a junction into someone else's folder would be destroyed",
    ),
    (
        "uninstall removes a real directory",
        "        if not _is_ours(entry):\n"
        '            results[entry.name] = "kept"\n'
        "            continue",
        "        if False:\n"
        '            results[entry.name] = "kept"\n'
        "            continue",
        "a skill folder the user wrote would be deleted",
    ),
    (
        "uninstall deletes text outside the block",
        "    head = existing[:start]\n"
        '    if head.endswith(nl + nl):\n'
        "        head = head[: -len(nl + nl)]\n"
        "    tail = existing[end:]\n"
        "    if tail.startswith(nl):\n"
        "        tail = tail[len(nl) :]\n"
        "    rest = head + tail",
        "    rest = existing[end:]",
        "the user's text above the block would be lost",
    ),
    (
        "uninstall ignores the dry-run flag",
        "                if not args.dry_run:\n                    path.unlink()",
        "                if True:\n                    path.unlink()",
        "a dry run would delete files",
    ),
    (
        "update does not re-select every tool",
        "        args.all = True\n        selected = set(tool_names())\n        wanted = list(TARGETS)",
        "        args.all = True",
        "update would skip a tool that is not detected",
    ),
]


def clear_cache() -> None:
    """Drop the bytecode cache before each run.

    A rewrite that keeps the same size and the same second can leave a stale
    .pyc in place, and the tests then exercise the mutant's predecessor.
    """
    shutil.rmtree(HERE / "__pycache__", ignore_errors=True)


def run_tests() -> bool:
    clear_cache()
    result = subprocess.run(
        [sys.executable, str(HERE / "test_bootstrap.py")],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def select(names: list[str]) -> list[tuple[str, str, str, str]]:
    """The mutants named by a substring of their name, or all of them."""
    if not names:
        return MUTANTS
    chosen = [m for m in MUTANTS if any(n.lower() in m[0].lower() for n in names)]
    for name in names:
        if not any(name.lower() in m[0].lower() for m in MUTANTS):
            print(f"no mutant matches {name!r}")
    return chosen


def main(argv: list[str]) -> int:
    original = C.read_text(TARGET)
    wanted = select(argv)
    if not wanted:
        print("no mutants selected")
        return 2
    if not run_tests():
        print("baseline is not green; refusing to mutate")
        return 2

    survived = []
    try:
        for name, old, new, why in wanted:
            if old not in original:
                print(f"SKIP  {name}: anchor text not found")
                survived.append((name, "anchor not found"))
                continue
            C.write_text(TARGET, original.replace(old, new, 1))
            if C.read_text(TARGET) == original:
                print(f"SKIP  {name}: mutation did not change the file")
                survived.append((name, "no change"))
                continue
            caught = not run_tests()
            print(f"{'CAUGHT' if caught else 'SURVIVED':<9}{name}", flush=True)
            if not caught:
                survived.append((name, why))
    finally:
        # A killed run must not leave a mutant on disk. SIGINT raises here;
        # SIGTERM on Windows does not, so the caller gets the same restore below.
        C.write_text(TARGET, original)
        # The last mutant's bytecode is still on disk. Clearing it here keeps a
        # later test run from importing the mutant.
        clear_cache()

    print()
    if survived:
        print(f"{len(survived)} mutant(s) survived -> missing tests:")
        for name, why in survived:
            print(f"  - {name}: {why}")
        return 1
    print(f"all {len(wanted)} mutants caught")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
