#!/usr/bin/env python3
"""Shared path resolution and config parsing for the skills hub.

Port of tools/_common.ps1. Resolution order for the sources root:
  1. SKILLS_HUB_SOURCES               (explicit override, wins)
  2. sources_root in repos.toml       (relative to the hub, or absolute)
  3. <hub>/../setupskills             (default sibling layout)

A repo's `path` may be absolute or relative to the resolved sources root.

Note on manifest.yml: it is TOML-shaped ([[skill]] tables) but several
`rationale` values contain unescaped double quotes, so tomllib rejects it and
always will. parse_manifest() mirrors the line-oriented reader that the
PowerShell tools used, which tolerated that. Do not "fix" it to tomllib.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

# tools/ lives one level under the hub root.
HUB_ROOT = Path(__file__).resolve().parent.parent

# Emit UTF-8 on stdout/stderr regardless of platform default. On Windows a pipe
# defaults to cp1252, so printing a page that contains an arrow or a box-drawing
# character dies with UnicodeEncodeError - a Windows-only crash in code meant to
# run on Linux and macOS too. errors="replace" keeps output alive on any console
# that still cannot represent a glyph, rather than aborting mid-report.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            pass


def read_text(path: str | os.PathLike) -> str:
    """Read UTF-8 without newline translation.

    Path.read_text() uses universal newlines and silently rewrites CRLF to LF.
    The PowerShell original ([System.IO.File]::ReadAllText) preserves bytes, and
    the whole provenance system hashes text verbatim - a translated read makes
    every CRLF source look like drift. Always use this, never read_text().
    """
    with open(path, "r", encoding="utf-8", newline="") as fh:
        return fh.read()


def write_text(path: str | os.PathLike, text: str) -> None:
    """Write UTF-8 without newline translation (mirrors WriteAllText)."""
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def read_bytes(path: str | os.PathLike) -> bytes:
    with open(path, "rb") as fh:
        return fh.read()


def ps_len(text: str) -> int:
    """Length the way .NET String.Length counts it: UTF-16 code units.

    Python len() counts code points, so a skill containing an emoji reports one
    char where the PowerShell original reported two. Anywhere the original used
    $text.Length (size banding, the catalog's "Size:" line), use this instead or
    the numbers drift on any non-BMP character.
    """
    return len(text.encode("utf-16-le")) // 2


def ps_num(value: float) -> int | float:
    """Render a number the way PowerShell prints it: 10.0 -> 10, 9.6 -> 9.6.

    [Math]::Round returns a double, but PowerShell's formatter drops a trailing
    ".0". Python keeps it, so every whole-number score, craft value and selection
    note differed textually. Return int for whole values, float otherwise.
    """
    return int(value) if float(value).is_integer() else value


def ps_round(value: float, digits: int = 0) -> float:
    """Round the way .NET Math.Round(double, digits) does, not the way Python does.

    These disagree, and the difference is visible in every published score.
    Math.Round(v, 1) scales first and then rounds the product half-to-even, so it
    rounds the *scaled double*, not the true decimal:

        v = 8.35    (binary 8.3499999999999996447)
        .NET   -> 8.35 * 10 == 83.5 exactly -> half-even -> 84 -> 8.4
        Python -> round(8.34999..., 1)             -> 8.3

    Matching .NET keeps RATING.json, COMPARISON.md and every score identical to
    what the PowerShell tools produced. It is not "more correct" - for 8.35 the
    Python answer follows the real value - but a migration that silently moves
    published numbers is the worse defect. 29 of 187 upstream skills land on a
    midpoint, so this is not theoretical.
    """
    scale = 10 ** digits
    scaled = value * scale
    # Python's round() on a float already rounds half-to-even, which is the .NET
    # default MidpointRounding.ToEven.
    return round(scaled) / scale


def get_hub_root() -> Path:
    return HUB_ROOT


def _match(line: str, pattern: str) -> re.Match | None:
    return re.match(pattern, line)


def _parse_list(value: str) -> list[str]:
    """Parse `["a", "b"]` into ['a', 'b'], dropping empties."""
    inner = value.strip()
    if inner.startswith("[") and inner.endswith("]"):
        inner = inner[1:-1]
    return [p.strip().strip('"') for p in inner.split(",") if p.strip().strip('"')]


def resolve_sources_root(declared: str | None, strict: bool = False) -> Path:
    hub = get_hub_root()
    env = os.environ.get("SKILLS_HUB_SOURCES")
    if env:
        return Path(env).resolve()

    declared_path: Path | None = None
    if declared:
        p = Path(declared)
        declared_path = (p if p.is_absolute() else hub / p).resolve()
        # a declared root that exists always wins
        if declared_path.exists():
            return declared_path

    # strict is for tools that WRITE to the declared location (clone-repos).
    # Falling back to a discovered folder there would clone into the wrong tree.
    if strict and declared_path is not None:
        return declared_path

    # discovery: walk up looking for a sibling directory that actually holds
    # repos. A path that merely exists but is empty must not win, or a stray
    # empty folder up the tree would silently hide every real source.
    d = hub
    while True:
        for cand in ("setupskills", "skills-sources"):
            p = d / cand
            if p.is_dir() and any(c.is_dir() for c in p.iterdir()):
                return p
        if d.parent == d:
            break
        d = d.parent

    # last resort: the declared value even if missing, so the error is useful
    if declared:
        p = Path(declared)
        return (p if p.is_absolute() else hub / p).resolve()
    return (hub.parent / "setupskills").resolve()


def read_repos(file: str | os.PathLike, strict: bool = False) -> dict:
    """Read repos.toml into {'repos': [...], 'sources_root': Path}."""
    repos: list[dict] = []
    cur: dict | None = None
    sources_root: str | None = None

    for line in read_text(file).splitlines():
        t = line.strip()
        m = _match(t, r'^sources_root\s*=\s*"?([^"]*)"?$')
        if m:
            sources_root = m.group(1)
            continue
        if t == "[[repo]]":
            if cur:
                repos.append(cur)
            cur = {}
            continue
        if cur is not None:
            m = _match(t, r'^(\w+)\s*=\s*(.+)$')
            if m:
                k, v = m.group(1), m.group(2).strip()
                if re.match(r'^\[(.*)\]$', v):
                    cur[k] = _parse_list(v)
                else:
                    cur[k] = v.strip('"')

    if cur:
        repos.append(cur)

    root = resolve_sources_root(sources_root, strict=strict)
    for r in repos:
        path = r.get("path")
        if path and not Path(path).is_absolute():
            r["path"] = str((root / path).resolve())
    return {"repos": repos, "sourcesRoot": root}


def read_manifest(file: str | os.PathLike) -> list[dict]:
    """Read manifest.yml's [[skill]] tables. Tolerates unescaped quotes."""
    skills: list[dict] = []
    cur: dict | None = None

    def flush():
        nonlocal cur
        if cur is not None:
            skills.append(cur)
        cur = None

    for line in read_text(file).splitlines():
        t = line.strip()
        if t == "[[skill]]":
            flush()
            cur = {"candidates": [], "composed": []}
            continue
        if cur is None:
            continue

        m = _match(t, r'^name\s*=\s*"(.+)"')
        if m:
            cur["name"] = m.group(1)
            continue
        m = _match(t, r'^status\s*=\s*"(.+)"')
        if m:
            cur["status"] = m.group(1)
            continue
        m = _match(t, r'^chosen\s*=\s*"?(.*?)"?$')
        if m:
            cur["chosen"] = m.group(1)
            continue
        m = _match(t, r'^candidates\s*=\s*\[(.*)\]')
        if m:
            cur["candidates"] = _parse_list(m.group(1))
            continue
        m = _match(t, r'^composed\s*=\s*\[(.*)\]')
        if m:
            cur["composed"] = _parse_list(m.group(1))
            continue

    flush()
    return skills


def get_shipped_sources() -> dict[str, str]:
    """Which upstream skills are ACTUALLY shipped, from skills/*/PROVENANCE.md.

    The manifest's `candidates` are proposals: a losing candidate was never
    shipped, so counting it as "claimed" hides real gaps. Provenance is the only
    claim backed by a file on disk.
    """
    skills_dir = get_hub_root() / "skills"
    mapping: dict[str, str] = {}
    if not skills_dir.is_dir():
        return mapping

    for d in sorted(skills_dir.iterdir()):
        if not d.is_dir():
            continue
        prov = d / "PROVENANCE.md"
        if not prov.is_file():
            continue
        txt = read_text(prov)

        names: list[str] = []
        if re.search(r'(?m)^- mode:\s*composed', txt):
            # the "sources:" line names REPOS; the excerpt table names skills
            names = [
                m.group(1).strip()
                for m in re.finditer(r'(?m)^\|\s*([^|]+?)\s*\|[^|]*\|\s*[0-9a-f]{64}\s*\|', txt)
            ]
            names = [n for n in names if n]
        else:
            m = re.search(r'(?m)^- upstream:\s*(.+?)\s*$', txt)
            if m:
                names = [m.group(1)]

        for n in names:
            mapping.setdefault(n, d.name)
    return mapping


def get_skill_index(repos: list[dict]) -> dict[str, dict]:
    """upstream skill name -> {repo, dir, file}."""
    index: dict[str, dict] = {}
    for r in repos:
        if r.get("status") == "reference":
            continue
        path = r.get("path")
        if not path or not Path(path).exists():
            continue
        for root in r.get("roots") or []:
            p = Path(path) if root == "." else Path(path) / root
            if not p.is_dir():
                continue
            for d in sorted(p.iterdir()):
                f = d / "SKILL.md"
                if d.is_dir() and f.is_file():
                    index.setdefault(d.name, {"repo": r["name"], "dir": str(d), "file": str(f)})
    return index


def read_ignore() -> dict[str, bool]:
    ignored: dict[str, bool] = {}
    f = get_hub_root() / "ignore.txt"
    if f.is_file():
        for line in read_text(f).splitlines():
            t = line.strip()
            if t and not t.startswith("#"):
                ignored[t] = True
    return ignored


def get_skill_coverage() -> dict:
    """One record per upstream skill: shipped, ignored, or dropped."""
    hub = get_hub_root()
    loaded = read_repos(hub / "repos.toml")
    index = get_skill_index(loaded["repos"])
    manifest = read_manifest(hub / "manifest.yml")
    shipped = get_shipped_sources()
    ignored = read_ignore()

    # canonical name each upstream skill was proposed for (report grouping only)
    claim: dict[str, str] = {}
    for s in manifest:
        for c in list(s.get("candidates") or []) + list(s.get("composed") or []):
            if c and c not in claim:
                claim[c] = s.get("name")

    rows = []
    for n, info in index.items():
        if n in shipped:
            state = "shipped"
        elif n in ignored:
            state = "ignored"
        else:
            state = "dropped"
        rows.append({
            "repo": info["repo"],
            "skill": n,
            "chars": Path(info["file"]).stat().st_size,
            "state": state,
            "canonical": shipped.get(n),
            "claimedBy": claim.get(n),
        })

    rows.sort(key=lambda r: (r["repo"], r["skill"]))
    return {
        "rows": rows,
        "shipped": shipped,
        "ignored": ignored,
        "index": index,
        "manifest": manifest,
    }
