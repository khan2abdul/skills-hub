#!/usr/bin/env python3
"""Proves every vendored skill is an unmodified copy of its upstream.

Port of tools/verify.ps1.

verbatim entries : rebuild upstream with only the name: line swapped, compare bytes
composed entries : re-extract each excerpt from its source and compare sha256
authored entries : no upstream, so compare the body against its recorded sha256

Read-only. Exit 1 on any failure.
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hubcommon as C  # noqa: E402

RED, GREEN, YELLOW, CYAN = "\033[31m", "\033[32m", "\033[33m", "\033[36m"
RESET = "\033[0m"


def body_text(file: str | Path) -> str:
    raw = C.read_text(file)
    m = re.match(r'\A---\r?\n.*?\r?\n---\r?\n', raw, re.S)
    return raw[m.end():] if m else raw


def get_section(body: str, heading: str) -> str | None:
    esc = re.escape(heading)
    m = re.search(rf'(?m)^{esc}\s*$', body)
    if not m:
        return None
    level = len(re.match(r'^(#+)', heading).group(1))
    start = m.start()
    after = m.end()
    # Next heading of the same or a higher level, ignoring anything inside a
    # fenced block. Without the fence check, "# Good: Each commit is
    # self-contained" (a bash comment in an example) is read as a heading and
    # truncates the section. Track offsets through the split separators: the old
    # `+ 1` assumed LF and drifted one char per line on CRLF sources.
    # Keep this identical to hubcompose.py.
    parts = re.split(r'(\r?\n)', body[after:])
    pos = after
    in_fence = False
    for i in range(0, len(parts), 2):
        line = parts[i]
        if re.match(r'^\s*(```|~~~)', line):
            in_fence = not in_fence
        elif not in_fence and re.match(rf'^#{{1,{level}}}\s', line):
            return body[start:pos].rstrip()
        pos += len(line)
        if i + 1 < len(parts):
            pos += len(parts[i + 1])
        if pos > len(body):
            break
    return body[start:].rstrip()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main(argv: list[str] | None = None) -> int:
    hub = C.get_hub_root()
    skills_dir = hub / "skills"
    loaded = C.read_repos(hub / "repos.toml")
    index = C.get_skill_index(loaded["repos"])
    manifest = C.read_manifest(hub / "manifest.yml")
    merged = [s for s in manifest if s.get("status") in ("merged", "authored")]
    fail = 0

    print(f"{CYAN}=== skills-hub verify ==={RESET}")
    print(f"sources root: {loaded['sourcesRoot']}")
    print(f"manifest entries: {len(manifest)}   merged: {len(merged)}")

    if merged and not Path(loaded["sourcesRoot"]).exists():
        print()
        print(f"{RED}Sources root not found, so no body can be proven. This is a setup problem,{RESET}")
        print(f"{YELLOW}not a content problem. Fix the path and re-run:{RESET}")
        print(f"{YELLOW}  SKILLS_HUB_SOURCES='<path to the 9 repos>'{RESET}")
        print(f"{YELLOW}  (or sources_root in repos.toml){RESET}")
        return 2

    for s in merged:
        name = s.get("name")
        d = skills_dir / name
        body_file = d / "SKILL.md"
        prov_file = d / "PROVENANCE.md"

        if not body_file.is_file():
            print(f"{RED}MISSING body : {name}{RESET}")
            fail += 1
            continue
        if not prov_file.is_file():
            print(f"{RED}MISSING prov : {name}{RESET}")
            fail += 1
            continue

        text = C.read_text(body_file)
        if not re.search(r'(?m)^name:\s*' + re.escape(name) + r'\s*$', text):
            print(f"{RED}NAME MISMATCH: {name} (frontmatter name must equal the directory name){RESET}")
            fail += 1

        # ---- slash eligibility: every shipped skill must be reachable as /<name>
        fm = re.match(r'\A---\r?\n(.*?)\r?\n---', text, re.S).group(1)
        if not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', name):
            print(f"{RED}NOT SLASHABLE: {name} (name must be kebab-case to be discovered){RESET}")
            fail += 1
        ui = re.search(r'(?m)^user-invocable:\s*(\S+)', fm)
        if ui and re.match(r'^(?i)(false|no|off|0)$', ui.group(1)):
            print(f"{RED}NOT SLASHABLE: {name} (user-invocable is off, so /{name} cannot be invoked){RESET}")
            fail += 1

        # ---- composed mode: re-extract and re-hash each excerpt
        if s.get("composed"):
            spec_file = hub / "compose" / f"{name}.yml"
            if not spec_file.is_file():
                print(f"{RED}NO spec      : {name}{RESET}")
                fail += 1
                continue
            spec = C.read_text(spec_file)

            blocks = []
            for blk in re.finditer(r'(?ms)^\[\[include\]\](.*?)(?=^\[\[include\]\]|\Z)', spec):
                b = blk.group(1)
                blocks.append({
                    "skill": (re.search(r'(?m)^skill\s*=\s*"(.+?)"', b) or [None, ""])[1],
                    "from": (re.search(r'(?m)^from\s*=\s*"(.+?)"', b) or [None, ""])[1],
                    "file": (re.search(r'(?m)^file\s*=\s*"(.+?)"', b) or [None, ""])[1],
                    "whole": bool(re.search(r'(?m)^whole\s*=\s*true', b)),
                })

            # hashes recorded in the shipped body's source comments
            recorded = {}
            for m in re.finditer(r'<!-- source: (.+?) \| (.*?) \| sha256: ([0-9a-f]{64}) -->', text):
                recorded[m.group(1) + "|" + m.group(2)] = m.group(3)

            bad = 0
            for b in blocks:
                if b["skill"] not in index:
                    print(f"  {RED}EXCERPT SOURCE GONE: {name} <- {b['skill']}{RESET}")
                    bad += 1
                    continue
                label = (
                    f"file:{b['file']}" + ("#" + re.sub(r'^#+\s*', '', b["from"]) if b["from"] else "")
                    if b["file"]
                    else b["from"]
                )
                src_body = body_text(index[b["skill"]]["file"])
                if b["file"]:
                    payload = Path(index[b["skill"]]["dir"]) / b["file"].replace("/", "\\")
                    if not payload.is_file():
                        print(f"  {RED}PAYLOAD GONE: {name} <- {b['skill']} '{b['file']}'{RESET}")
                        bad += 1
                        continue
                    payload_text = C.read_text(payload)
                    excerpt = get_section(payload_text, b["from"]) if b["from"] else payload_text.rstrip()
                elif b["whole"]:
                    excerpt = re.sub(r'(?m)^#\s+.*\r?\n', '', src_body).strip()
                else:
                    excerpt = get_section(src_body, b["from"])
                if not excerpt:
                    print(f"  {RED}SECTION GONE: {name} <- {b['skill']} '{label}'{RESET}")
                    bad += 1
                    continue

                now_hash = sha256_text(excerpt)
                key = b["skill"] + "|" + label
                if key not in recorded:
                    print(f"  {RED}NO HASH IN BODY: {name} <- {key}{RESET}")
                    bad += 1
                    continue
                if recorded[key] != now_hash:
                    print(f"  {YELLOW}EXCERPT DRIFT: {name} <- {b['skill']} '{label}' upstream changed, re-compose{RESET}")
                if not re.search(re.escape(excerpt), text):
                    # Upstream checkouts mix endings: the shipped bodies are LF
                    # (the * -text policy), but some harvested repos are CRLF on
                    # disk (gsd-2, karpathy). hubcompose normalized on the way in,
                    # so a CRLF excerpt can never match an LF body. Compare the
                    # other form before calling it drift.
                    alt = excerpt.replace("\r\n", "\n") if "\r\n" in excerpt else excerpt.replace("\n", "\r\n")
                    if not re.search(re.escape(alt), text):
                        print(f"  {RED}EXCERPT ALTERED: {name} <- {b['skill']} '{label}' not found verbatim in the shipped body{RESET}")
                        bad += 1
            if bad == 0:
                print(f"{GREEN}OK    {name} (composed, {len(blocks)} excerpts all verbatim){RESET}")
            else:
                fail += 1
            continue

        # ---- authored mode: no upstream, so the body is held to its own recorded hash
        # One skill needs this: the parent router, whose every line is a routing
        # decision about THIS hub. Vendoring it was what broke it - the copy named
        # 30 skills that had been renamed or dropped. See its PROVENANCE.md.
        prov_text = C.read_text(prov_file)
        if re.search(r'(?m)^- mode:\s*authored', prov_text):
            h = re.search(r'(?m)^- body sha256:\s*([0-9a-fA-F]{64})', prov_text)
            if not h:
                print(f"{RED}NO body hash : {name} (authored entry must record one){RESET}")
                fail += 1
                continue
            now = sha256_text(body_text(body_file))
            if now != h.group(1).lower():
                print(f"{RED}BODY DRIFT   : {name} (authored body changed; update '- body sha256:' once reviewed){RESET}")
                fail += 1
            else:
                print(f"{GREEN}OK    {name} (authored, body hash matches){RESET}")
            continue

        # ---- verbatim mode
        upstream = re.search(r'(?m)^- upstream:\s*(.+?)\s*$', prov_text)
        upstream_name = upstream.group(1) if upstream else ""
        rh = re.search(r'(?m)^- upstream SKILL\.md sha256:\s*([0-9a-fA-F]{64})', prov_text)
        recorded_hash = rh.group(1) if rh else ""
        bc = re.search(r'(?m)^- body changed:\s*(.+?)\s*$', prov_text)
        body_changed = bc.group(1) if bc else ""
        if not upstream_name:
            print(f"{RED}NO upstream in PROVENANCE: {name}{RESET}")
            fail += 1
            continue

        verbatim_ok = False
        if upstream_name in index:
            src_raw = C.read_text(index[upstream_name]["file"])
            m = re.match(r'\A(---\r?\n)(.*?)(\r?\n---\r?\n)', src_raw, re.S)
            if m:
                expected = (
                    m.group(1)
                    + re.sub(r'(?m)^name:\s*.*$', f"name: {name}", m.group(2), count=1)
                    + m.group(3)
                    + src_raw[m.end():]
                )
                if expected != text:
                    at = min(len(expected), len(text))
                    for i in range(at):
                        if expected[i] != text[i]:
                            at = i
                            break
                    line = expected[:at].count("\n") + 1
                    print(f"{RED}BODY MODIFIED: {name} differs from upstream '{upstream_name}' at line ~{line}{RESET}")
                    fail += 1
                else:
                    verbatim_ok = True
            else:
                print(f"{RED}NO frontmatter upstream: {upstream_name}{RESET}")
                fail += 1
        else:
            print(f"{RED}UPSTREAM GONE: {name} <- '{upstream_name}' not on disk (cannot prove body){RESET}")
            fail += 1

        if upstream_name in index and recorded_hash:
            now_hash = hashlib.sha256(Path(index[upstream_name]["file"]).read_bytes()).hexdigest()
            if now_hash != recorded_hash.lower():
                print(f"{YELLOW}UPSTREAM DRIFT: {name} <- '{upstream_name}' changed since vendoring{RESET}")
        if body_changed and body_changed != "no":
            print(f"{YELLOW}BODY DECLARED CHANGED: {name} says '{body_changed}' but policy is name-only{RESET}")
        if verbatim_ok:
            print(f"{GREEN}OK    {name} (verbatim, name: line only){RESET}")

    if skills_dir.is_dir():
        valid = {s.get("name") for s in merged}
        for d in sorted(skills_dir.iterdir()):
            if d.is_dir() and d.name not in valid:
                print(f"{YELLOW}ORPHAN dir   : {d.name} vendored but not merged in manifest{RESET}")

    if fail > 0:
        print(f"{RED}FAILED: {fail} problem(s){RESET}")
        return 1
    print(f"{GREEN}OK: every shipped body is proven against upstream{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
