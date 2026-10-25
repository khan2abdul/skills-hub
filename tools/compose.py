#!/usr/bin/env python3
"""Builds a composed skill from compose/<name>.yml.

Port of tools/compose.ps1.

Every excerpt is copied verbatim from its upstream SKILL.md; sha256 of each is
recorded in the shipped body as a comment and in PROVENANCE.md, so verify.py can
re-extract and re-prove them later.

Note on read/write: PowerShell 5.1 on Windows writes a UTF-8 BOM for
Set-Content -Encoding UTF8, which the original did. This port writes no BOM -
a BOM is invisible in most editors but breaks strict parsers on Linux and macOS,
which is exactly the audience the hub now targets. verify.py compares bodies with
and without a leading BOM so both vintages still pass.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hubcommon as C  # noqa: E402

GREEN, YELLOW, CYAN, RED, RESET = "\033[32m", "\033[33m", "\033[36m", "\033[31m", "\033[0m"


def get_body_text(path: str | Path) -> str:
    raw = C.read_text(path)
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
    # Keep this identical to verify.py.
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


def parse_spec(spec: str) -> dict:
    desc = (re.search(r'(?m)^description\s*=\s*"(.+)"\s*$', spec) or [None, ""])[1]
    srcs = (re.search(r'(?m)^sources\s*=\s*\[(.*)\]', spec) or [None, ""])[1]
    source_repos = [p.strip().strip('"') for p in srcs.split(",") if p.strip().strip('"')]

    includes = []
    for blk in re.finditer(r'(?ms)^\[\[include\]\](.*?)(?=^\[\[include\]\]|\Z)', spec):
        b = blk.group(1)
        inc = {
            "skill": (re.search(r'(?m)^skill\s*=\s*"(.+?)"', b) or [None, ""])[1],
            "title": (re.search(r'(?m)^title\s*=\s*"(.+?)"', b) or [None, ""])[1],
            "from": (re.search(r'(?m)^from\s*=\s*"(.+?)"', b) or [None, ""])[1],
            # Some upstream skills keep their procedure in a payload file next to
            # SKILL.md (gstack's sections/*.md). `file` quotes that file whole.
            "file": (re.search(r'(?m)^file\s*=\s*"(.+?)"', b) or [None, ""])[1],
            "whole": bool(re.search(r'(?m)^whole\s*=\s*true', b)),
        }
        if inc["skill"]:
            includes.append(inc)
    return {"desc": desc, "sourceRepos": source_repos, "includes": includes}


def run(name: str, what_if: bool = False, force: bool = False) -> int:
    """Compose one skill. Returns 0 on success, 1 on refusal, raises on bad spec."""
    hub = C.get_hub_root()
    spec_file = hub / "compose" / f"{name}.yml"
    if not spec_file.is_file():
        raise FileNotFoundError(f"no compose spec at {spec_file}")

    spec = C.read_text(spec_file)
    parsed = parse_spec(spec)
    desc, source_repos, includes = parsed["desc"], parsed["sourceRepos"], parsed["includes"]
    if not includes:
        raise ValueError(f"no [[include]] blocks in {spec_file}")

    loaded = C.read_repos(hub / "repos.toml")
    index = C.get_skill_index(loaded["repos"])

    out_lines: list[str] = []
    manifest_rows = []

    for inc in includes:
        if inc["skill"] not in index:
            raise ValueError(f"include '{inc['skill']}' not found on disk")
        file = index[inc["skill"]]["file"]
        body = get_body_text(file)
        if inc["file"]:
            label = "file:" + inc["file"] + ("#" + re.sub(r'^#+\s*', '', inc["from"]) if inc["from"] else "")
        else:
            label = inc["from"]

        if inc["file"]:
            payload = Path(index[inc["skill"]]["dir"]) / inc["file"].replace("/", "\\")
            if not payload.is_file():
                raise ValueError(f"file '{inc['file']}' not found in {inc['skill']}")
            payload_text = C.read_text(payload)
            excerpt = get_section(payload_text, inc["from"]) if inc["from"] else payload_text.rstrip()
        elif inc["whole"]:
            excerpt = re.sub(r'(?m)^#\s+.*\r?\n', '', body).strip()
        else:
            excerpt = get_section(body, inc["from"])
        if not excerpt:
            raise ValueError(f"section '{label}' not found in {inc['skill']}")

        h = hashlib.sha256(excerpt.encode("utf-8")).hexdigest()

        # A title is only needed when the excerpt does not already open with its
        # own heading. Emitting both produced "## Red flags" immediately followed
        # by "## Red flags" in ten shipped skills: the composition read as if each
        # section had been pasted twice.
        starts_with_heading = bool(re.match(r'^#{1,6}\s', excerpt))
        if inc["title"] and not starts_with_heading:
            out_lines.append(f"## {inc['title']}")
            out_lines.append("")
        out_lines.append(f"<!-- source: {inc['skill']} | {label} | sha256: {h} -->")
        out_lines.append("")
        out_lines.append(excerpt)
        out_lines.append("")
        manifest_rows.append({"skill": inc["skill"], "from": label, "sha256": h, "chars": C.ps_len(excerpt)})

    # Title and source count come from the spec, not from a hardcoded string: this
    # used to emit "# Debug This Code" and "three upstream skills" into every
    # composition, so a second composed skill shipped with the wrong heading.
    title = (re.search(r'(?m)^title\s*=\s*"(.+)"\s*$', spec) or [None, ""])[1]
    if not title:
        title = " ".join(w[:1].upper() + w[1:] for w in name.split("-"))
    n = len(includes)
    # YAML-escape the description. An unquoted scalar breaks on the first
    # colon-space ("review of a change: a STRIDE pass"), and dsh then drops the
    # skill from its catalog with only a warning - 15 shipped skills were
    # invisible that way.
    #
    # Quote only when the value needs it. Quoting every description rewrote 8
    # shipped SKILL.md files whose text is otherwise unchanged, and those bodies
    # are meant to be byte-identical to what was reviewed. A plain scalar is safe
    # when it has no colon-space, no leading indicator, no trailing space and no
    # quote/backslash. Everything else gets the quoted form.
    needs_quotes = (
        ": " in desc or " #" in desc
        or desc[:1] in ("-", "?", ":", ",", "[", "]", "{", "}", "#", "&", "*", "!", "|", ">", "'", '"', "%", "@", "`")
        or desc != desc.strip()
        or '"' in desc or "\\" in desc
    )
    if needs_quotes:
        desc_yaml = desc.replace("\\", "\\\\").replace('"', '\\"')
        desc_line = f'description: "{desc_yaml}"\n'
    else:
        desc_line = f"description: {desc}\n"
    plural = "s" if n != 1 else ""
    header = (
        "---\n"
        f"name: {name}\n"
        + desc_line
        + "---\n"
        "\n"
        f"# {title}\n"
        "\n"
        f"Composed from verbatim excerpts of {n} upstream skill{plural}. Each section is\n"
        "byte-identical to its source; provenance and hashes are in PROVENANCE.md.\n"
        "Do not paraphrase a section when editing - change the compose spec instead."
    )

    # TrimEnd + explicit blank line: a here-string's last newline is not
    # preserved, so relying on it silently glues the first "## heading" onto the
    # preamble line. The file ends with two newlines, which is what the shipped
    # bodies have and what git stores.
    #
    # Normalise to LF. 72 of the original 187 upstream skills are checked out with CRLF, and a
    # raw excerpt would carry those CRLFs into the shipped body. The original did
    # not: StringBuilder.AppendLine and the here-strings normalised every line on
    # the way out, so all committed bodies are LF. Writing CRLF here rewrites 16
    # SKILL.md files on the first re-compose, and those bodies are meant to be
    # byte-identical.
    text = (header.rstrip() + "\n\n" + "\n".join(out_lines) + "\n").replace("\r\n", "\n")

    # Guard: every block must start on its own line after a blank line. Cheap, and
    # it catches the class of bug where concatenation eats the separator. Two
    # legitimate exceptions, both present in real upstream skills:
    #   - a "## Heading" inside a fence is example text, not a heading;
    #   - a heading straight after a closing fence needs no blank line.
    prev = ""
    in_fence = False
    prev_was_fence = False
    for line in text.split("\n"):
        if re.match(r'^\s*(```|~~~)', line):
            in_fence = not in_fence
            prev = line
            prev_was_fence = not in_fence
            continue
        if (not in_fence and not prev_was_fence and re.match(r'^#{1,2} ', line)
                and prev != "" and not re.match(r'^\s*$', prev)):
            raise ValueError(f"compose produced a heading with no preceding blank line: '{line}'")
        prev = line
        prev_was_fence = False

    if what_if:
        print(f"{CYAN}WOULD compose {name} ({len(manifest_rows)} sections, {C.ps_len(text)} chars){RESET}")
        for r in manifest_rows:
            print(f"  {r['skill']:<32} {r['chars']:>6} chars")
        return 0

    d = hub / "skills" / name
    if d.exists() and not force:
        print(f"{YELLOW}exists: {d} (use --force){RESET}")
        return 1
    d.mkdir(parents=True, exist_ok=True)
    C.write_text(d / "SKILL.md", text)

    rows = "\n".join(f"| {r['skill']} | {r['from']} | {r['sha256']} | {r['chars']} |" for r in manifest_rows)
    prov = (
        "# Provenance\n"
        "\n"
        f"- canonical: {name}\n"
        "- mode: composed\n"
        "- body changed: no (every excerpt verbatim; only headings and ordering are new)\n"
        f"- sources: {', '.join(source_repos)}\n"
        f"- spec: compose/{name}.yml\n"
        f"- composed: {date.today().isoformat()}\n"
        "\n"
        "## Excerpts\n"
        "\n"
        "| upstream skill | section | sha256 | chars |\n"
        "|---|---|---|---|\n"
        f"{rows}\n"
        "\n"
        "\n"
        "Each sha256 above is over the exact excerpt text. verify.py re-extracts and\n"
        "re-hashes to prove the shipped body still matches upstream.\n"
        "\n"
    )
    C.write_text(d / "PROVENANCE.md", prov)
    print(f"{GREEN}composed {name} ({len(manifest_rows)} sections, {C.ps_len(text)} chars){RESET}")
    for r in manifest_rows:
        print(f"  {r['skill']:<32} {r['chars']:>6} chars")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--what-if", action="store_true")
    args = ap.parse_args(argv)
    try:
        return run(args.name, what_if=args.what_if, force=args.force)
    except (ValueError, FileNotFoundError) as e:
        print(f"{RED}{e}{RESET}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
