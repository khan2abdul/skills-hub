#!/usr/bin/env python3
"""Install the writing style, and the hub's skills, into each AI tool's config.

  bootstrap.py                show the plan, ask, then install for detected tools
  bootstrap.py --check        report drift, write nothing, exit 1 on drift
  bootstrap.py --dry-run      print the plan, then stop without asking
  bootstrap.py --only a,b     limit to the named tools
  bootstrap.py --all          every known tool, installed or not
  bootstrap.py --yes          skip the confirm question (needed without a tty)
  bootstrap.py --no-link      copy the skills instead of linking them
  bootstrap.py --dir DIR      use another hub folder as the source
  bootstrap.py --home DIR     target a throwaway home (tests)

The confirm question is the permission gate, so every write path asks. A run
with no terminal refuses rather than writing unseen; --yes is the explicit
opt-out.

Exit codes: 0 clean, 1 drift or refusal, 2 setup problem.

S01: the style source, the marker engine, the atomic write, and the DSH block
target. S02: detection, the plan, the confirm gate, four block targets.
S03: skill links and the Kilo JSON. S04: the four `file` targets and the Cursor
paste text. S05 adds uninstall and update.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hubcommon as C  # noqa: E402

RED, GREEN, YELLOW, CYAN = "\033[31m", "\033[32m", "\033[33m", "\033[36m"
RESET = "\033[0m"

START = "<!-- skills-hub:writing-style:start -->"
END = "<!-- skills-hub:writing-style:end -->"

# Cursor User Rules are an app setting with no documented file, so the hub prints
# the paste text and the way to reach the box instead of guessing a path.
CURSOR_RULES = "Cursor Settings -> Rules -> User Rules"
CURSOR_PASTE = "Copy this text into Cursor User Rules"

# Two strings that only occur in the style body. Used to tell "this file already
# has an unmarked copy" from "this file has none", without comparing the whole
# body: a user may have reflowed it by hand.
_FINGERPRINTS = (
    "Write all responses and messages in simple, easy English",
    "ASD-STE100",
)


def style_path(hub: Path | None = None) -> Path:
    return (hub or C.get_hub_root()) / "style" / "WRITING-STYLE.md"


def style_body(hub: Path | None = None) -> str:
    """The style text, exactly as shipped, with no leading or trailing blank lines."""
    return C.read_text(style_path(hub)).strip("\r\n")


def atomic_write(path: Path, text: str) -> None:
    """Write `text` to `path` in one step: temp file beside it, then replace.

    A crash during the write leaves the old file intact, never a half-written
    config that the tool would load.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".skills-hub-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _find_block(text: str) -> tuple[int, int] | None:
    """Span of the managed region, markers included, or None."""
    start = text.find(START)
    if start < 0:
        return None
    end = text.find(END, start)
    if end < 0:
        return None
    return start, end + len(END)


def render_block(body: str) -> str:
    return f"{START}\n{body}\n{END}"


def _same_block(a: str, b: str) -> bool:
    """True when two blocks hold the same text, whatever their line endings."""
    return a.replace("\r\n", "\n") == b.replace("\r\n", "\n")


def _find_untracked(text: str) -> tuple[int, int] | None:
    """Span of an unmarked copy of the style, or None.

    Anchored on the `## Writing style` heading, because that is the only thing
    that reliably says where the copy starts and ends. A wrap that guessed from
    the prose alone once swallowed a later `<!-- 5-stack -->` region and broke
    its marker pairing.

    The region runs from the heading to the next heading of the same or a higher
    level. An HTML comment ends it too: those wrap tool-managed regions, and
    eating one corrupts a file that another tool owns.
    """
    heading = re.search(r"(?m)^(#{1,6})\s+Writing style\s*$", text)
    if not heading:
        return None
    level = len(heading.group(1))
    pos = heading.end()
    for m in re.finditer(r"(?m)^(#{1,6})\s+\S|^<!--", text[pos:]):
        if m.group(0).startswith("<!--"):
            return heading.start(), pos + m.start()
        if len(m.group(1)) <= level:
            return heading.start(), pos + m.start()
    return heading.start(), len(text)


def _adapt_endings(text: str, existing: str | None) -> str:
    """Give `text` the line endings that `existing` already uses.

    The style source is LF and a Windows profile file is usually CRLF. Writing
    one into the other leaves a mixed file that shows as wholly changed in a
    diff, and some editors silently rewrite the rest.
    """
    if existing is None or "\r\n" not in existing:
        return text.replace("\r\n", "\n")
    return text.replace("\r\n", "\n").replace("\n", "\r\n")


def _newline(existing: str | None) -> str:
    """The line ending this file uses, so an append does not mix two."""
    return "\r\n" if existing is not None and "\r\n" in existing else "\n"


def apply_block(path: Path, body: str, replace_untracked: bool = False) -> str:
    """Put `body` into `path` as one managed block.

    Returns one of: "created", "appended", "replaced", "unchanged", "untracked".

    "untracked" means the file already holds the style text but no markers, and
    the copy is not under a `## Writing style` heading. That is the dangerous
    case: appending duplicates the text, and replacing blind could take user
    rules with it. This reports and writes nothing.
    """
    existing = C.read_text(path) if path.is_file() else None
    block = _adapt_endings(render_block(body), existing)
    nl = _newline(existing)

    if existing is None:
        atomic_write(path, block + nl)
        return "created"

    span = _find_block(existing)
    if span is not None:
        start, end = span
        if existing[start:end] == block:
            return "unchanged"
        atomic_write(path, existing[:start] + block + existing[end:])
        return "replaced"

    has_copy = any(fp in existing for fp in _FINGERPRINTS)
    if has_copy:
        region = _find_untracked(existing)
        if region is None or not replace_untracked:
            return "untracked"
        # Wrap the copy in place, and put the canonical body there. The old copy
        # is replaced, never kept beside the new one.
        start, end = region
        head = existing[:start]
        tail = existing[end:].lstrip("\r\n")
        merged = head + block + nl + (nl + tail if tail else "")
        atomic_write(path, merged)
        return "replaced"

    # Always `nl + nl`. A separator that shrinks for a file that already ends in a
    # blank line produces the same bytes as a file that ends in one newline, so
    # remove_block could not tell them apart and the round trip would lose bytes.
    atomic_write(path, existing + nl + nl + block + nl)
    return "appended"


def _same_body(text: str, body: str) -> bool:
    """True when a file holds exactly the style body, whatever its line endings."""
    return text.strip().replace("\r\n", "\n") == body.strip().replace("\r\n", "\n")


def remove_block(path: Path) -> str:
    """Take the managed block out of `path`, keeping every other byte.

    Returns "removed", "deleted", "absent" or "kept".

    "deleted" means the file held nothing but the block, so the file goes too:
    that stops an uninstall leaving an empty file or a wall of blank lines.
    "kept" means the file holds the style text with no markers. This tool cannot
    prove it wrote that copy, so it does not touch it.
    """
    if not path.is_file():
        return "absent"
    existing = C.read_text(path)
    span = _find_block(existing)
    if span is None:
        return "kept" if any(fp in existing for fp in _FINGERPRINTS) else "absent"
    start, end = span
    nl = _newline(existing)
    # apply_block writes `existing + nl + nl + block + nl`, and the span stops at
    # the last character of the END marker. Take back the blank line before the
    # block and the one newline after it, and nothing else.
    head = existing[:start]
    if head.endswith(nl + nl):
        head = head[: -len(nl + nl)]
    tail = existing[end:]
    if tail.startswith(nl):
        tail = tail[len(nl) :]
    rest = head + tail
    if not rest.strip():
        # Only the block was left. Nothing on disk records whether this tool made
        # the file, and an empty file left behind is worse than one removed.
        path.unlink()
        return "deleted"
    atomic_write(path, rest)
    return "removed"


def _is_our_body(text: str, body: str) -> bool:
    """True when `text` is the style body, current or an older revision of it.

    Ownership is the rule uninstall turns on, and a `file` target has no markers,
    so a rewrite deletes every byte the body does not have. The test must
    therefore fail closed.

    A revision of this tool replaces wording, so it has no more lines than the
    body and keeps the body's first and last line. A person who adds their own
    rule adds a line, so the file grows past the body's line count and is theirs.
    That is the distinction: replacement keeps the count, addition raises it.
    """
    if _same_body(text, body):
        return True
    text_lines = [ln.strip() for ln in text.replace("\r\n", "\n").split("\n") if ln.strip()]
    body_lines = [ln.strip() for ln in body.replace("\r\n", "\n").split("\n") if ln.strip()]
    if not text_lines or not any("ASD-STE100" in ln for ln in text_lines):
        return False
    if text_lines[0] != body_lines[0] or text_lines[-1] != body_lines[-1]:
        return False
    if text.count("ASD-STE100") != body.count("ASD-STE100"):
        return False
    # More lines than the body means somebody added text of their own.
    return len(text_lines) <= len(body_lines)


def apply_file(path: Path, body: str) -> str:
    """Make `path` hold the body and nothing else, because the hub owns the file.

    Returns one of: "created", "unchanged", "replaced", "kept".

    "kept" is the ownership rule. Nothing on disk records which run wrote a file,
    so the only proof is the text: a file is replaced only when it is the body, or
    an older revision of it, and nothing else. A file that merely mentions the
    standard is the user's own, and it is left untouched. That is what lets
    uninstall delete a file this tool wrote and nothing else.
    """
    if not path.is_file():
        atomic_write(path, body + "\n")
        return "created"
    existing = C.read_text(path)
    if _same_body(existing, body):
        return "unchanged"
    if not _is_our_body(existing, body):
        return "kept"
    # A `file` target has no markers, so a stale body cannot be edited in place.
    atomic_write(path, _adapt_endings(body, existing) + _newline(existing))
    return "replaced"


# --- targets -----------------------------------------------------------------
# One row per known tool: what says it is installed, and where its style goes.
# `signals` are paths whose presence means the tool is installed. Config folders
# are the signal because no binary for these tools resolves on PATH; a
# Get-Command check would detect nothing.
#
# `kind` says who owns the bytes at `rel`:
#   "block" the user also edits the file, so the body sits between markers
#   "file"  the hub owns the whole file, so there are no markers
#   "print" no file at all: the hub prints the text for a manual paste
#
# `rel` is None for a tool this hub can detect but has no style file for.
# Detection still reports it, so the plan never hides a tool that is really
# installed.
TOOLS: list[dict] = [
    {"tool": "claude", "rel": ".claude/CLAUDE.md", "kind": "block", "signals": (".claude",), "skills": (".claude/skills",)},
    {"tool": "codex", "rel": ".codex/AGENTS.md", "kind": "block", "signals": (".codex",), "skills": (".agents/skills",)},
    {"tool": "gemini", "rel": ".gemini/GEMINI.md", "kind": "block", "signals": (".gemini",), "skills": ()},
    {"tool": "dsh", "rel": ".dsh/AGENTS.md", "kind": "block", "signals": (".dsh",), "skills": ()},
    # Kilo takes skills.paths in JSON and its style in a file it does not read back.
    {"tool": "kilo", "rel": ".kilocode/rules/writing-style.md", "kind": "file", "signals": (".config/kilo/kilo.json",), "skills": ()},
    {"tool": "cline", "rel": "Documents/Cline/Rules/writing-style.md", "kind": "file", "signals": (".cline",), "skills": (".cline/skills",)},
    # Cursor reads its own folder and the shared one, so it fills both. Its
    # User Rules have no documented file, so the style is a print target.
    {"tool": "cursor", "rel": None, "kind": "print", "signals": (".cursor",), "skills": (".cursor/skills", ".agents/skills")},
    {"tool": "kiro", "rel": ".kiro/steering/writing-style.md", "kind": "file", "signals": (".kiro",), "skills": (".kiro/skills",)},
    {"tool": "windsurf", "rel": ".codeium/windsurf/memories/writing-style.md", "kind": "file", "signals": (".codeium",), "skills": ()},
]

# A `print` row has no file, so it never appears in a write loop: `rel` is the
# test for "has a path", and `kind` says who owns the bytes at that path.
TARGETS: list[dict] = [t for t in TOOLS if t["rel"]]

KILO_JSON = ".config/kilo/kilo.json"


def tool_names() -> list[str]:
    return sorted(t["tool"] for t in TOOLS)


def detect(home: Path) -> set[str]:
    """Names of the installed tools, judged by their config paths."""
    return {
        t["tool"]
        for t in TOOLS
        if any((home / s).exists() for s in t["signals"])
    }


def plan_lines(home: Path, hub: Path, chosen: set[str]) -> list[str]:
    """One line per known tool, so a detection miss is always visible.

    Every write this run will make is listed here, skills included. The gate
    asks consent for the plan, so a write that is not on the plan is a write
    the user never approved.
    """
    present = detect(home)
    skills = hub_skills(hub)
    folders: dict[str, list[str]] = {}
    seen: set[str] = set()
    for t in TOOLS:
        if t["tool"] not in chosen:
            continue
        for rel in t["skills"]:
            if rel in seen:
                continue
            seen.add(rel)
            folders.setdefault(t["tool"], []).append(rel)
    lines = []
    for t in TOOLS:
        name = t["tool"]
        # `--all` writes a tool that is not detected, so the plan follows what the
        # run will write, not what detection found. A write off the plan is a
        # write the user never approved.
        if name not in chosen:
            lines.append(f"  {name:<9} {'not detected' if name not in present else 'not selected':<22}skipped")
            continue
        wrote = False
        if t["rel"] is not None:
            lines.append(f"  {name:<9} {home / t['rel']}")
            wrote = True
        if t["kind"] == "print":
            lines.append(f"  {name:<9} paste into {CURSOR_RULES}")
            wrote = True
        for rel in folders.get(name, []):
            plural = "" if len(skills) == 1 else "s"
            lines.append(f"  {name:<9} {home / rel} ({len(skills)} skill{plural})")
            wrote = True
        if name == "kilo":
            lines.append(f"  {name:<9} {home / KILO_JSON} (skills.paths)")
            wrote = True
        if not wrote:
            lines.append(f"  {name:<9} {'no writable target':<22}skipped")
    if "dsh" in chosen:
        lines.append(f"  {'dsh':<9} customSkillDirs: {dsh_wiring(home, hub / 'skills')}")
    return lines


def print_cursor(body: str) -> None:
    """Show the one manual step: the text to paste, and where the box is."""
    print(f"{CYAN}{CURSOR_PASTE}.{RESET}")
    print(f"{CYAN}  {CURSOR_RULES}{RESET}")
    print()
    print(body)
    print()


def confirm(prompt: str) -> bool:
    try:
        return input(prompt).strip().lower() in ("y", "yes")
    except EOFError:
        return False


# --- skills ------------------------------------------------------------------


def skill_folders(selected: set[str]) -> list[tuple[str, str]]:
    """(tool, folder) pairs to write skills into, one entry per folder.

    `selected` is the set of tools this run may write, already resolved against
    detection by the caller. Cursor and Codex both read `~/.agents/skills`, so
    it is written once and skipped for the second tool: writing it twice would
    fight itself.
    """
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for t in TOOLS:
        if t["tool"] not in selected:
            continue
        for rel in t["skills"]:
            if rel in seen:
                continue
            seen.add(rel)
            out.append((t["tool"], rel))
    return out


def hub_skills(hub: Path) -> list[Path]:
    """The skill folders to link: one level down, each holding a SKILL.md."""
    return _skill_dirs(hub / "skills")


def _skill_dirs(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(p for p in root.iterdir() if (p / "SKILL.md").is_file())


def _make_link(src: Path, dst: Path) -> bool:
    """Link dst to src. True when a link exists, False when it cannot be made.

    A Windows junction needs no admin rights. A POSIX symlink needs no rights
    either. The caller falls back to copy, and reports which one it used.
    """
    try:
        if os.name == "nt":
            proc = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(dst), str(src)],
                capture_output=True,
                text=True,
            )
            return proc.returncode == 0
        dst.symlink_to(src, target_is_directory=True)
        return True
    except (OSError, NotImplementedError):
        return False


def _same_content(a: Path, b: Path) -> bool:
    """True when two skill folders hold the same files with the same bytes.

    This is how a copy the hub made is told apart from a folder the user wrote,
    with no state file to go stale.
    """
    try:
        left = {p.relative_to(a): p for p in a.rglob("*") if p.is_file()}
        right = {p.relative_to(b): p for p in b.rglob("*") if p.is_file()}
        if left.keys() != right.keys():
            return False
        return all(C.read_text(left[k]) == C.read_text(right[k]) for k in left)
    except (OSError, UnicodeDecodeError):
        return False


def _is_ours(entry: Path) -> bool:
    """True for a link this hub could have made, junction or symlink.

    `Path.is_symlink()` is False for a Windows junction, so it cannot be used
    alone here: on Windows every link this hub makes is a junction. `is_junction`
    exists only from 3.12, and the spec promises 3.11, so read the reparse tag
    directly when that attribute is absent.
    """
    if entry.is_symlink():
        return True
    is_junction = getattr(entry, "is_junction", None)
    if is_junction is not None:
        return bool(is_junction())
    try:
        # FILE_ATTRIBUTE_REPARSE_POINT, without following the link.
        return bool(entry.stat(follow_symlinks=False).st_file_attributes & 0x400)
    except (OSError, AttributeError):
        return False


def _inside(child: Path, parent: Path) -> bool:
    """True when `child` is `parent` or sits below it, by resolved path."""
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except (ValueError, OSError):
        return False


def link_skills(src_root: Path, dst_root: Path, allow_link: bool = True) -> dict[str, str]:
    """Put one entry per skill from `src_root` into `dst_root`.

    Returns {skill: "linked" | "copied" | "repaired" | "kept"}. A real directory
    this hub did not create is "kept": the user may have written it, and
    deleting it would destroy their work.

    A destination inside the source is refused outright. Copying there makes the
    copy contain itself, and the filesystem recurses until a path limit stops it.
    """
    if _inside(dst_root, src_root):
        return {"refused": "destination is inside the skills source"}
    results: dict[str, str] = {}
    dst_root.mkdir(parents=True, exist_ok=True)
    for src in _skill_dirs(src_root):
        dst = dst_root / src.name
        ours = _is_ours(dst)
        if ours and dst.resolve() == src.resolve():
            results[src.name] = "linked"
            continue
        if ours:
            # A link at the wrong target is stale, so replace it. On Windows a
            # junction needs rmdir, and unlink() also removes a symlink.
            if os.name == "nt" and not dst.is_symlink():
                os.rmdir(dst)
            else:
                dst.unlink()
            state = "repaired"
        elif dst.exists():
            if not _same_content(dst, src):
                # The user wrote this folder. Leave it, and say so.
                results[src.name] = "kept"
                continue
            # A copy of this very skill: the hub made it when linking failed.
            shutil.rmtree(dst)
            state = "repaired"
        else:
            state = "linked"
        if allow_link and _make_link(src, dst):
            results[src.name] = state
        else:
            shutil.copytree(src, dst)
            results[src.name] = "copied"
    return results


def _norm_path(p: Path) -> str:
    """Compare paths by value, so the YAML spelling of slashes or case is free."""
    return str(p).replace("\\", "/").rstrip("/").lower()


def _yaml_list_items(text: str, key: str) -> list[str]:
    """The `- item` lines under `key:`, with trailing comments removed.

    Deliberately small. The hub only reads this one key and never writes YAML,
    so a parser dependency is not worth it.
    """
    out: list[str] = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.rstrip(":") != key or not stripped.endswith(":"):
            continue
        base = len(line) - len(line.lstrip())
        for nxt in lines[i + 1 :]:
            nxt_stripped = nxt.strip()
            if not nxt_stripped or nxt_stripped.startswith("#"):
                continue
            indent = len(nxt) - len(nxt.lstrip())
            if not nxt_stripped.startswith("- ") or indent < base:
                break
            item = nxt_stripped[2:].split(" #")[0].strip().strip("'\"")
            if item:
                out.append(item)
    return out


def dsh_wiring(home: Path, skills_root: Path) -> str:
    """Say whether a DSH profile patch lists this hub in customSkillDirs.

    Read only. The hub ships no YAML writer, and a wrong rewrite of a profile
    patch changes every session on that machine, so this reports and stops.
    """
    patches = sorted((home / ".dsh" / "profiles").glob("*/cordis.patch.yml"))
    if not patches:
        return "no profile"
    wanted = _norm_path(skills_root)
    for patch in patches:
        text = C.read_text(patch)
        if "customSkillDirs" not in text:
            continue
        for raw in _yaml_list_items(text, "customSkillDirs"):
            if _norm_path(Path(raw)) == wanted:
                return "wired"
    return "not wired"


def merge_kilo_json(path: Path, skills_root: Path, dry_run: bool = False) -> tuple[str, str]:
    """Add `skills_root` to skills.paths in the Kilo config.

    Returns (result, detail) where result is "created", "added", "unchanged" or
    "refused". A file this tool cannot parse is never rewritten: it may hold the
    user's whole configuration.
    """
    wanted = str(skills_root.resolve())
    data: dict = {}
    if path.is_file():
        raw = C.read_text(path)
        try:
            data = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            return "refused", f"{path} is not valid JSON; left alone"
        if not isinstance(data, dict):
            return "refused", f"{path} is not a JSON object; left alone"
    skills = data.get("skills")
    if skills is None:
        skills = data["skills"] = {}
    if not isinstance(skills, dict):
        return "refused", f"{path} has a non-object skills key; left alone"
    paths = skills.get("paths")
    if paths is None:
        paths = skills["paths"] = []
    if not isinstance(paths, list):
        return "refused", f"{path} has a non-list skills.paths; left alone"
    if wanted in paths:
        return "unchanged", wanted
    existed = path.is_file()
    if dry_run:
        return "added", wanted
    paths.append(wanted)
    atomic_write(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return ("added" if existed else "created"), wanted


def unlink_skills(dst_root: Path, src_root: Path) -> dict[str, str]:
    """Remove this hub's entries from `dst_root`, and nothing else.

    Returns {name: "removed" | "kept"}. An entry goes only when it is a link whose
    target is inside the hub. A link elsewhere, a real directory, and a folder the
    user wrote all stay: uninstall may not destroy work it cannot prove it made.
    """
    results: dict[str, str] = {}
    if not dst_root.is_dir():
        return results
    hub_root = src_root.resolve()
    for entry in sorted(dst_root.iterdir()):
        if not _is_ours(entry):
            results[entry.name] = "kept"
            continue
        try:
            target = entry.resolve()
        except OSError:
            results[entry.name] = "kept"
            continue
        if not _inside(target, hub_root):
            results[entry.name] = "kept"
            continue
        # A Windows junction needs rmdir; unlink() also removes a symlink.
        if os.name == "nt" and not entry.is_symlink():
            os.rmdir(entry)
        else:
            entry.unlink()
        results[entry.name] = "removed"
    return results


def uninstall(hub: Path, home: Path, selected: set[str], args: argparse.Namespace) -> int:
    """Remove every write this tool can prove it made.

    A `file` target goes only when `_is_our_body` proves the hub wrote it. A block
    is cut out and the bytes around it are kept. A skill entry goes only when it
    is a link into this hub. The Kilo JSON and the hub folder stay.
    """
    body = style_body(hub)
    # A dry run must not say "removed": the plan is not the act.
    gone = "would remove" if args.dry_run else "removed"
    for t in TOOLS:
        if t["tool"] not in selected or t["kind"] == "print":
            continue
        path = home / t["rel"]
        if not path.is_file():
            continue
        if t["kind"] == "file":
            if _is_our_body(C.read_text(path), body):
                print(f"{GREEN}{gone:<12}{t['tool']:<9} {path}{RESET}")
                if not args.dry_run:
                    path.unlink()
            else:
                print(f"{YELLOW}{'kept':<12}{t['tool']:<9} {path} is not a file this tool wrote{RESET}")
            continue
        if _find_block(C.read_text(path)) is None:
            print(f"{YELLOW}{'kept':<12}{t['tool']:<9} {path} has no managed block{RESET}")
            continue
        print(f"{GREEN}{gone:<12}{t['tool']:<9} {path}{RESET}")
        if not args.dry_run:
            remove_block(path)

    src_root = hub / "skills"
    for tool, rel in skill_folders(selected):
        root = home / rel
        if args.dry_run:
            continue
        results = unlink_skills(root, src_root)
        removed = sum(1 for v in results.values() if v == "removed")
        kept = sum(1 for v in results.values() if v == "kept")
        if removed or kept:
            detail = f"{removed} removed" + (f", {kept} kept" if kept else "")
            colour = YELLOW if kept else GREEN
            print(f"{colour}skills     {tool:<9} {root} ({detail}){RESET}")
    if args.dry_run:
        print(f"{YELLOW}Uninstall dry run: nothing was removed.{RESET}")
    return 0


def run(args: argparse.Namespace) -> int:
    hub = Path(args.dir).resolve() if args.dir else C.get_hub_root()
    home = Path(args.home).resolve() if args.home else Path.home()
    if not style_path(hub).is_file():
        print(f"{RED}no style/WRITING-STYLE.md under {hub}{RESET}")
        print(f"{YELLOW}That file is the only copy of the style text. Nothing was written.{RESET}")
        return 2

    unknown = [n for n in args.only if n not in tool_names()]
    if unknown:
        print(f"{RED}unknown tool name: {', '.join(unknown)}{RESET}")
        print(f"{YELLOW}Known names: {', '.join(tool_names())}{RESET}")
        return 2

    body = style_body(hub)
    present = detect(home)
    if args.only:
        selected = set(args.only)
    elif args.all:
        # Every known tool, installed or not: "--all" is the repair switch.
        selected = set(tool_names())
    else:
        selected = present
    wanted = [t for t in TARGETS if t["tool"] in selected]
    fail = 0

    if args.uninstall:
        return uninstall(hub, home, selected, args)
    # --update is --all: repair every target and re-link. It still asks, because
    # a repair is a write and the confirm is the gate that makes a write visible.
    if args.update:
        args.all = True
        selected = set(tool_names())
        wanted = list(TARGETS)

    if args.check:
        for t in TOOLS:
            if t["tool"] not in selected:
                continue
            if t["kind"] == "print":
                # Nothing to read, so the one manual step is reported, not failed.
                if t["tool"] in present:
                    print(f"{YELLOW}manual    {t['tool']:<9} paste into {CURSOR_RULES}{RESET}")
                else:
                    print(f"{YELLOW}SKIP  {t['tool']:<9} not installed{RESET}")
                continue
            path = home / t["rel"]
            if not path.is_file():
                if t["tool"] in present:
                    print(f"{RED}DRIFT {t['tool']:<9} {path} is missing{RESET}")
                    fail += 1
                else:
                    print(f"{YELLOW}SKIP  {t['tool']:<9} {path} (not installed){RESET}")
                continue
            if t["kind"] == "file":
                text = C.read_text(path)
                if _same_body(text, body):
                    print(f"{GREEN}OK    {t['tool']:<9} {path}{RESET}")
                elif _is_our_body(text, body):
                    print(f"{RED}DRIFT {t['tool']:<9} {path} differs from style/{RESET}")
                    fail += 1
                else:
                    # The run refuses to touch this file, so "re-run to fix" would
                    # be advice it will not follow.
                    print(f"{YELLOW}kept  {t['tool']:<9} {path} is not a hub file, left alone{RESET}")
                continue
            span = _find_block(C.read_text(path))
            if span is None:
                print(f"{RED}DRIFT {t['tool']:<9} {path} has no managed block{RESET}")
                fail += 1
            elif _same_block(C.read_text(path)[span[0] : span[1]], render_block(body)):
                print(f"{GREEN}OK    {t['tool']:<9} {path}{RESET}")
            else:
                print(f"{RED}DRIFT {t['tool']:<9} {path} block differs from style/{RESET}")
                fail += 1
        fail += check_skills(hub, home, selected)
        if fail:
            print(f"{RED}FAILED: {fail} target(s) drifted. Re-run bootstrap.py to fix.{RESET}")
            return 1
        print(f"{GREEN}OK: every installed style block, style file and skill link is in place{RESET}")
        return 0

    print(f"{CYAN}This will write:{RESET}")
    for line in plan_lines(home, hub, selected):
        print(line)
    # A tool can be picked for its skills alone, or for one paste alone, with no
    # file to write, so an empty `wanted` is not "nothing to do".
    skill_targets = skill_folders(selected)
    kilo_wanted = "kilo" in selected and "kilo" in present
    paste = [t for t in TOOLS if t["kind"] == "print" and t["tool"] in selected and t["tool"] in present]
    if not wanted and not skill_targets and not kilo_wanted and not paste:
        print(f"{YELLOW}No tool to write. Nothing was written.{RESET}")
        return 0
    if args.dry_run:
        return 0
    # Every write path asks, including a bare run, because that is what
    # install.ps1 calls. Fail closed without a terminal: piped stdin cannot
    # answer, and skipping the question there is a silent write past the gate.
    if not args.yes:
        if not sys.stdin.isatty():
            print(f"{YELLOW}No terminal to confirm on. Re-run with --yes to apply.{RESET}")
            return 1
        if not confirm("\nApply this? [y/N] "):
            print(f"{YELLOW}Nothing was written.{RESET}")
            return 1

    for t in wanted:
        path = home / t["rel"]
        if t["kind"] == "file":
            result = apply_file(path, body)
            colour = GREEN if result in ("created", "replaced", "unchanged") else YELLOW
            print(f"{colour}{result:<10}{t['tool']:<9} {path}{RESET}")
            if result == "kept":
                print(f"{YELLOW}  This file holds none of the style text, so it may be yours.{RESET}")
                print(f"{YELLOW}  Left alone. Delete it to let the hub write its own.{RESET}")
                fail += 1
            continue
        result = apply_block(path, body, replace_untracked=args.replace_untracked)
        colour = GREEN if result in ("created", "appended", "replaced", "unchanged") else YELLOW
        print(f"{colour}{result:<10}{t['tool']:<9} {path}{RESET}")
        if result == "untracked":
            print(f"{YELLOW}  This file already holds the style text with no markers.{RESET}")
            print(f"{YELLOW}  Re-run with --replace-untracked to wrap it in one managed block.{RESET}")
            fail += 1

    for _ in paste:
        print_cursor(body)

    fail += install_skills(hub, home, selected, args)
    return 1 if fail else 0


def check_skills(hub: Path, home: Path, selected: set[str]) -> int:
    """Report skills entries that are missing, stale, or a copy of the hub.

    "Exists" is not enough: a copy, or a link into an old hub, would pass a bare
    existence test while giving the tool stale prose.
    """
    skills = hub_skills(hub)
    if not skills:
        return 0
    fail = 0
    for tool, rel in skill_folders(selected):
        root = home / rel
        missing: list[str] = []
        wrong: list[str] = []
        for s in skills:
            entry = root / s.name
            if not entry.exists():
                missing.append(s.name)
            elif not _is_ours(entry):
                wrong.append(s.name)
            elif entry.resolve() != s.resolve():
                wrong.append(s.name)
        if missing:
            print(f"{RED}DRIFT skills    {tool:<9} {root} missing {len(missing)}{RESET}")
            fail += 1
        elif wrong:
            print(f"{RED}DRIFT skills    {tool:<9} {root} has {len(wrong)} copy or stale link(s){RESET}")
            fail += 1
        else:
            print(f"{GREEN}OK    {tool:<9} {root} ({len(skills)} skills){RESET}")
    if "kilo" in selected:
        result, detail = merge_kilo_json(home / KILO_JSON, hub / "skills", dry_run=True)
        if result == "unchanged":
            print(f"{GREEN}OK    {'kilo':<9} {detail} is in skills.paths{RESET}")
        else:
            print(f"{RED}DRIFT kilo      {detail}{RESET}")
            fail += 1
    return fail


def install_skills(
    hub: Path,
    home: Path,
    selected: set[str],
    args: argparse.Namespace,
) -> int:
    """Link the skills into each selected tool that has a skills folder."""
    src_root = hub / "skills"
    if not hub_skills(hub):
        return 0
    fail = 0
    for tool, rel in skill_folders(selected):
        results = link_skills(src_root, home / rel, allow_link=not args.no_link)
        counts: dict[str, int] = {}
        for state in results.values():
            counts[state] = counts.get(state, 0) + 1
        summary = ", ".join(f"{n} {state}" for state, n in sorted(counts.items()))
        colour = YELLOW if "kept" in counts else GREEN
        print(f"{colour}skills     {tool:<9} {home / rel} ({summary}){RESET}")
    if "kilo" in selected:
        result, detail = merge_kilo_json(home / KILO_JSON, src_root)
        colour = YELLOW if result == "refused" else GREEN
        print(f"{colour}{result:<10}{'kilo':<9} {detail}{RESET}")
        if result == "refused":
            fail += 1
    if "dsh" in selected:
        # DSH has no skills folder the hub may write, so report and stop.
        state = dsh_wiring(home, src_root)
        colour = GREEN if state == "wired" else YELLOW
        print(f"{colour}{state:<10}{'dsh':<9} customSkillDirs{RESET}")
    return fail


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Install the writing style into each AI tool.")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--only", default="")
    ap.add_argument("--uninstall", action="store_true", help="remove only what this tool wrote")
    ap.add_argument("--update", action="store_true", help="re-apply every target and re-link")
    ap.add_argument("--replace-untracked", action="store_true")
    ap.add_argument("--no-link", action="store_true", help="copy skills instead of linking")
    ap.add_argument("--yes", action="store_true", help="skip the confirm prompt")
    ap.add_argument("--home", default="")
    ap.add_argument("--dir", default="")
    args = ap.parse_args(argv)
    if args.only:
        args.only = [n.strip() for n in args.only.split(",") if n.strip()]
    else:
        args.only = []
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
