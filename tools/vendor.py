#!/usr/bin/env python3
"""Vendors a skill under a canonical name WITHOUT touching its body.

Port of tools/vendor.ps1.

  vendor.py --skill debug-this-code
  vendor.py --skill debug-this-code --from diagnosing-bugs
  vendor.py --all --what-if
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hubcommon as C  # noqa: E402

RED, GREEN, YELLOW, CYAN, RESET = "\033[31m", "\033[32m", "\033[33m", "\033[36m", "\033[0m"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill", default="")
    ap.add_argument("--from", dest="from_", default="")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--what-if", action="store_true")
    args = ap.parse_args(argv)

    hub = C.get_hub_root()
    loaded = C.read_repos(hub / "repos.toml")
    index = C.get_skill_index(loaded["repos"])
    manifest = C.read_manifest(hub / "manifest.yml")

    targets = manifest if args.all else [s for s in manifest if s.get("name") == args.skill]
    if not targets:
        print(f"no manifest entry named '{args.skill}'. Run tools/harvest.py to see valid names.", file=sys.stderr)
        return 1

    done = 0
    skipped = 0
    errors: list[str] = []

    # compose.py is imported lazily: it imports this module's siblings and is not
    # needed for verbatim entries.
    import compose

    for s in targets:
        canonical = s.get("name")
        out_dir = hub / "skills" / canonical

        # ---- composed mode ----
        if s.get("composed"):
            spec_file = hub / "compose" / f"{canonical}.yml"
            if not spec_file.is_file():
                errors.append(f"{canonical} : composed entry has no compose/{canonical}.yml")
                continue
            if out_dir.exists() and not args.force:
                print(f"{YELLOW}SKIP  {canonical} (exists, use --force){RESET}")
                skipped += 1
                continue
            rc = compose.run(canonical, what_if=args.what_if, force=args.force)
            if rc != 0:
                errors.append(f"{canonical} : compose failed")
                continue
            done += 1
            continue

        # ---- verbatim mode ----
        source_name = args.from_ or s.get("chosen") or (s.get("candidates") or [""])[0]
        if not source_name:
            errors.append(f"{canonical} : no chosen source and no candidates")
            continue
        if source_name not in index:
            errors.append(f"{canonical} : upstream '{source_name}' not found on disk")
            continue

        src = index[source_name]
        if out_dir.exists() and not args.force:
            print(f"{YELLOW}SKIP  {canonical} (exists, use --force){RESET}")
            skipped += 1
            continue

        raw = C.read_text(src["file"])
        m = re_frontmatter(raw)
        if not m:
            errors.append(f"{canonical} : '{source_name}' has no YAML frontmatter")
            continue

        # Mirror vendor.ps1 exactly: rewrite name: only inside the frontmatter
        # block, and only once. Replacing every name: in the file would hit
        # code-fence examples too. The match stops before \r, so a CRLF source
        # keeps its line ending.
        head, yaml, sep, rest = m
        import re
        yaml2 = re.sub(r'(?m)^name:[^\r\n]*', f"name: {canonical}", yaml, count=1)
        if yaml2 == yaml and not re.search(r'(?m)^name:\s*', yaml):
            errors.append(f"{canonical} : '{source_name}' frontmatter has no name: line")
            continue
        new_raw = head + yaml2 + sep + rest

        if args.what_if:
            print(f"{CYAN}WOULD {canonical:<24} <- {source_name:<32} mode=verbatim name-line-only{RESET}")
            done += 1
            continue

        out_dir.mkdir(parents=True, exist_ok=True)
        C.write_text(out_dir / "SKILL.md", new_raw)
        for item in sorted(Path(src["dir"]).iterdir()):
            if item.name == "SKILL.md":
                continue
            dest = out_dir / item.name
            try:
                if item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest)
            except OSError:
                pass

        src_hash = hashlib.sha256(C.read_bytes(src["file"])).hexdigest().upper()
        repo_root = next((r.get("path") for r in loaded["repos"] if r.get("name") == src["repo"]), None)
        commit = ""
        if repo_root and (Path(repo_root) / ".git").exists():
            try:
                commit = subprocess.run(
                    ["git", "-C", repo_root, "rev-parse", "HEAD"],
                    capture_output=True, text=True, check=False,
                ).stdout.strip()
            except OSError:
                commit = ""
        rel = str(src["file"])[len(repo_root or ""):].lstrip("\\/").replace("\\", "/")

        others = ", ".join(c for c in (s.get("candidates") or []) if c != source_name)
        prov = (
            "# Provenance\n"
            "\n"
            f"- canonical: {canonical}\n"
            "- mode: verbatim\n"
            f"- upstream: {source_name}\n"
            f"- repo: {src['repo']}\n"
            f"- path: {rel}\n"
            f"- commit: {commit}\n"
            f"- upstream SKILL.md sha256: {src_hash}\n"
            "- body changed: no\n"
            f"- change: frontmatter `name:` rewritten from `{source_name}` to `{canonical}`; every other byte preserved\n"
            f"- other candidates considered: {others}\n"
            f"- vendored: {date.today().isoformat()}\n"
        )
        # Set-Content -Encoding UTF8 wrote a BOM in Windows PowerShell 5.1;
        # match the existing files, which have none.
        C.write_text(out_dir / "PROVENANCE.md", prov)
        print(f"{GREEN}OK    {canonical} <- {source_name} ({src['repo']}){RESET}")
        done += 1

    print()
    print(f"vendored: {done}  skipped: {skipped}  errors: {len(errors)}")
    if errors:
        for e in errors:
            print(f"  {RED}{e}{RESET}")
        return 1
    print(f"{CYAN}Now run tools/verify.py to re-prove every body.{RESET}")
    return 0


def re_frontmatter(raw: str):
    """Return (head, yaml, sep, rest) or None. Mirrors \\A(---)(.*?)(---)."""
    import re
    m = re.match(r'\A(---\r?\n)(.*?)(\r?\n---\r?\n)', raw, re.S)
    if not m:
        return None
    return m.group(1), m.group(2), m.group(3), raw[m.end():]


if __name__ == "__main__":
    sys.exit(main())
