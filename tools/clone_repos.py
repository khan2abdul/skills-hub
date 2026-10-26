#!/usr/bin/env python3
"""Clones every status="cloned" repo from repos.toml into the hub's own repos/.

Port of tools/clone-repos.ps1. Makes the hub self-contained: no dependency on an
external sources folder.

  clone_repos.py                 -> clone anything missing, report what exists
  clone_repos.py --update        -> fetch and report drift (changes nothing)
  clone_repos.py --update --force -> fetch and hard-reset to upstream HEAD
  clone_repos.py --full          -> full history instead of --depth 1

Shallow by default: the hub only needs current file contents to vendor from, and
gstack alone is ~1.5 GB with history and node_modules.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hubcommon as C  # noqa: E402

RED, GREEN, YELLOW, CYAN, RESET = "\033[31m", "\033[32m", "\033[33m", "\033[36m", "\033[0m"


def git(*args: str, check: bool = False) -> str:
    """Run git, returning stdout. Progress goes to stderr and must not be captured."""
    r = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    if check and r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    return r.stdout.strip()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--update", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--what-if", action="store_true")
    args = ap.parse_args(argv)

    hub = C.get_hub_root()
    loaded = C.read_repos(hub / "repos.toml")
    repos_dir = hub / "repos"

    print(f"hub         : {hub}")
    print(f"repos dir   : {repos_dir}")
    print()

    if not args.what_if:
        repos_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for r in loaded["repos"]:
        if r.get("status") != "cloned":
            continue
        if not r.get("url"):
            print(f"{YELLOW}WARNING: no url for {r.get('name')}, skipping{RESET}", file=sys.stderr)
            continue

        dest = Path(r.get("path") or "")
        is_git = (dest / ".git").exists()

        if not is_git:
            if args.what_if:
                print(f"{CYAN}WOULD clone {r['name']:<24} {r['url']}{RESET}")
                continue
            print(f"{CYAN}cloning {r['name']:<24} ...{RESET}")
            cmd = ["clone", "--single-branch", "--quiet"]
            if not args.full:
                cmd += ["--depth", "1"]
            cmd += [r["url"], str(dest)]
            # git writes progress to stderr; verify on disk instead of trusting
            # the exit code, because a clone can fail after partially succeeding.
            git(*cmd)
            if not (dest / ".git").exists():
                print(f"{RED}FAILED  {r['name']}{RESET}")
                rows.append({"repo": r["name"], "state": "FAILED", "commit": "", "skills": 0, "mb": 0})
                continue
            # A fresh clone checks out before this config applies, so rewrite the
            # tree from the index. Sources are proved byte for byte; a CRLF
            # working tree would make a vendored body differ by machine.
            git("-C", str(dest), "config", "core.autocrlf", "false")
            git("-C", str(dest), "checkout-index", "-a", "-f")
        else:
            if not args.what_if:
                git("-C", str(dest), "config", "core.autocrlf", "false")
            if args.update:
                git("-C", str(dest), "fetch", "--quiet", "origin")
                head = git("-C", str(dest), "rev-parse", "HEAD")
                remote = git("-C", str(dest), "rev-parse", "origin/HEAD")
                if not remote:
                    remote = git("-C", str(dest), "rev-parse", "origin/HEAD^{commit}")
                drift = head != remote
                if drift and args.force:
                    git("-C", str(dest), "reset", "--hard", "--quiet", remote)
                    print(f"{GREEN}updated {r['name']:<24} {head[:7]} -> {remote[:7]}{RESET}")
                elif drift:
                    print(f"{YELLOW}DRIFT   {r['name']:<24} local {head[:7]}, upstream {remote[:7]} (use --force to reset){RESET}")

        commit = ""
        if (dest / ".git").exists():
            commit = git("-C", str(dest), "rev-parse", "--short", "HEAD")

        # count skill bundles this repo contributes through its declared roots
        count = 0
        for root in r.get("roots") or []:
            p = dest if root == "." else dest / root
            if not p.is_dir():
                continue
            try:
                count += sum(1 for d in p.iterdir() if d.is_dir() and (d / "SKILL.md").is_file())
            except OSError:
                pass
        size = 0
        if dest.is_dir():
            for f in dest.rglob("*"):
                try:
                    if f.is_file():
                        size += f.stat().st_size
                except OSError:
                    pass
        rows.append({
            "repo": r["name"],
            "state": "would-clone" if args.what_if else "ok",
            "commit": commit,
            "skills": count,
            "mb": round(size / (1024 * 1024), 1),
        })

    print()
    for r in sorted(rows, key=lambda r: r["repo"]):
        print(f"{r['repo']:<24} {r['state']:<10} {r['commit']:<9} {r['skills']:>3} skills {r['mb']:>7} MB")
    total = sum(r["skills"] for r in rows)
    mb = round(sum(r["mb"] for r in rows), 1)
    print(f"repos: {len(rows)}   skill bundles: {total}   size: {mb} MB")
    print(f"{CYAN}Next: python tools/harvest.py{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
