#!/usr/bin/env python3
"""The scoring core, shared by rate_skills.py and compare_skills.py.

Port of tools/_rubric.ps1. Both tools must score the same way, or "our skill is
7.3 and the original is 9.1" would be a comparison between two different
rulers. Every function here takes plain text and returns numbers plus the
evidence behind them.

No side effects, no file writes, no dependency on the skill directory layout
beyond what is passed in.
"""
from __future__ import annotations

import re
from pathlib import Path

from hubcommon import ps_len, ps_round

# A "gate" is any explicit stop/accept/verify criterion - not just the four
# shouty words. "Definition of done", "acceptance criteria" and plain "criteria"
# are exactly what a gate is, and were being missed: break-into-tasks writes
# "definition of done" and "acceptance" and scored gates 6/10 for not saying
# STOP. Counting the requirement, not the capitalisation.
GATE_PATTERNS = [
    r'\bSTOP\b', r'\bMUST\b', r'\bNEVER\b', r'(?i)\bdo not\b', r'(?i)\bbefore you\b',
    r'(?i)\bverif(y|ication|ied)\b', r'(?i)\bevidence\b', r'(?i)\bcheck\b', r'(?i)\bgate\b',
    r'(?i)\bcriteria\b', r'(?i)\bdefinition of done\b', r'(?i)\bacceptance\b',
    r'(?i)\bstop when\b', r'(?i)\bdone when\b', r'(?i)\bexit criteri',
]

HOST_KEYS = ['preamble-tier', 'allowed-tools', 'triggers', 'hooks', 'model', 'tools']

# Path reference ending in a filename character, not a sentence's full stop:
# "see references/foo.md." must capture "references/foo.md", not "...md."
REL_REF = re.compile(
    r'(?<![\w/])((?:references|scripts|assets|templates|examples)/[A-Za-z0-9_.\-/]*[A-Za-z0-9_\-/])'
)

PORTABILITY_PATTERNS = [
    {"p": r'~/\.claude/skills/', "why": "hard-coded ~/.claude/skills path"},
    {"p": r'gstack/bin/', "why": "calls a gstack helper the hub does not ship"},
    {"p": r'[A-Za-z]:\\\\[Uu]sers\\\\', "why": "hard-coded Windows user path"},
]


def get_frontmatter(text: str) -> dict:
    """Split frontmatter keys from body. Mirrors _rubric.ps1 Get-Frontmatter."""
    m = re.match(r'\A---\r?\n(.*?)\r?\n---\r?\n?', text, re.S)
    if not m:
        return {"keys": {}, "body": text}

    keys: dict[str, str] = {}
    lines = re.split(r'\r?\n', m.group(1))
    i = 0
    while i < len(lines):
        km = re.match(r'^([A-Za-z][A-Za-z0-9_-]*):\s*(.*)$', lines[i])
        if not km:
            i += 1
            continue
        key, val = km.group(1), km.group(2).strip()

        # A YAML block scalar (| or >) puts the real text on the following
        # indented lines. Reading only the "|" line reports a 1-char
        # description and makes a well-described skill look unnamed.
        if re.match(r'^[|>][+-]?$', val):
            block = []
            j = i + 1
            while j < len(lines):
                if re.match(r'^\s+\S', lines[j]) or re.match(r'^\s*$', lines[j]):
                    block.append(lines[j].strip())
                    j += 1
                else:
                    break
            val = " ".join(block).strip()
            i = j - 1
        else:
            # plain or quoted scalar that continues on the next indented line
            j = i + 1
            while j < len(lines):
                if re.match(r'^\s+\S', lines[j]):
                    val += " " + lines[j].strip()
                    j += 1
                else:
                    break
            i = j - 1

        keys[key] = val.strip('"').strip("'")
        i += 1

    return {"keys": keys, "body": text[m.end():]}


def get_grade(score: float) -> str:
    if score >= 9:
        return "A"
    if score >= 8:
        return "B"
    if score >= 7:
        return "C"
    if score >= 6:
        return "D"
    return "F"


def get_size_band(chars: int) -> dict:
    if chars < 1500:
        return {"s": 2, "why": f"{chars} chars - stub, not a procedure"}
    if chars < 3000:
        return {"s": 6, "why": f"{chars} chars - thin"}
    if chars <= 20000:
        return {"s": 10, "why": f"{chars} chars - in range"}
    if chars <= 45000:
        return {"s": 7, "why": f"{chars} chars - heavy"}
    return {"s": 4, "why": f"{chars} chars - context bomb"}


def get_craft_score(text: str, name: str, skill_dir: str = "") -> dict:
    """Scores the craft half only. Selection needs manifest context."""
    fm = get_frontmatter(text)
    body = fm["body"]
    keys = fm["keys"]
    dims: dict[str, int] = {}
    ev: dict[str, list[str]] = {}

    # ---- structure
    s = 0
    e: list[str] = []
    if keys.get("name") == name:
        s += 4
        e.append("name matches directory")
    else:
        e.append(f"name mismatch: '{keys.get('name')}'")
    desc = keys.get("description")
    if desc:
        s += 3
        if 80 <= ps_len(desc) <= 1024:
            s += 3
            e.append(f"description {ps_len(desc)} chars (usable)")
        else:
            e.append(f"description {ps_len(desc)} chars (want 80-1024)")
    else:
        e.append("no description")
    if re.search(r'(?m)^disable-model-invocation:\s*true', text):
        e.append("slash-only: model cannot choose it")
        s -= 2
    dims["structure"] = max(0, min(10, s))
    ev["structure"] = e

    # ---- procedure
    steps = len(re.findall(r'(?m)^\s*\d+\.\s+\S', body))
    heads = len(re.findall(r'(?m)^#{2,3}\s+\S', body))
    bullets = len(re.findall(r'(?m)^\s*[-*]\s+\S', body))
    if steps >= 6:
        p = 10
    elif steps >= 3:
        p = 8
    elif steps >= 1:
        p = 5
    else:
        p = 1
    if heads >= 4:
        p += 2
    elif heads >= 2:
        p += 1
    if bullets >= 5:
        p += 1
    dims["procedure"] = min(10, p)
    ev["procedure"] = [f"{steps} numbered steps, {heads} headings, {bullets} bullets"]

    # ---- gates
    # PowerShell's -match is case-INSENSITIVE by default, so the port must pass
    # IGNORECASE or a skill writing "stop" instead of "STOP" scores lower here
    # than under the original. That is a porting artefact, not a scoring change.
    hits = sum(1 for pat in GATE_PATTERNS if re.search(pat, body, re.IGNORECASE))
    dims["gates"] = 10 if hits >= 5 else 8 if hits == 4 else 6 if hits == 3 else 4 if hits == 2 else 2 if hits == 1 else 0
    ev["gates"] = [f"{hits} gate/verification markers"]

    # ---- references (needs a dir to check against; without one, assume present)
    refs = sorted({m.group(1) for m in REL_REF.finditer(body)})
    missing: list[str] = []
    if skill_dir:
        for r in refs:
            alt = Path(skill_dir) / r.replace("/", "\\")
            leaf = Path(skill_dir) / Path(r).name
            if not alt.exists() and not leaf.exists():
                missing.append(r)
    if not refs:
        dims["references"] = 8
        ev["references"] = ["names no resource files"]
    else:
        present = len(refs) - len(missing)
        # [int][Math]::Round uses banker's rounding; Python's round() matches.
        dims["references"] = int(round(10 * present / len(refs)))
        ee = [f"{present}/{len(refs)} referenced files present"]
        if missing:
            ee.append("missing: " + ", ".join(missing))
        ev["references"] = ee

    # ---- portability
    issues: list[str] = []
    for pp in PORTABILITY_PATTERNS:
        n = len(re.findall(pp["p"], body))
        if n > 0:
            issues.append(f"{pp['why']} ({n} x)")
    host_k = [k for k in HOST_KEYS if k in keys]
    if host_k:
        issues.append("host-specific frontmatter: " + ", ".join(host_k))
    dims["portability"] = max(0, 10 - 3 * len(issues))
    ev["portability"] = issues if issues else ["no absolute paths or vendor helpers"]

    # ---- size
    band = get_size_band(ps_len(text))
    dims["size"] = band["s"]
    ev["size"] = [band["why"]]

    # ---- a body that cannot run here: hooks calling scripts we do not ship
    dep_scripts = sorted({m.group(1) for m in re.finditer(r'([\w.\-]+\.sh)\b', body)})
    has_hooks = bool(re.search(r'(?mi)^\s*hooks:', text))
    not_executable = False
    if (
        (len(body.strip()) < 300 and re.search(r'(?mi)^\s*(hooks|allowed-tools):', text))
        or (has_hooks and dep_scripts)
    ):
        not_executable = True
        dims["procedure"] = min(dims["procedure"], 2)
        dims["gates"] = min(dims["gates"], 2)
        dims["portability"] = min(dims["portability"], 2)
        ev["procedure"].append("not executable in this install")

    return {
        "dims": dims,
        "evidence": ev,
        "body": body,
        "keys": keys,
        "refs": refs,
        "missing": missing,
        "notExecutable": not_executable,
        "hasHooks": has_hooks,
        "depScripts": dep_scripts,
    }


def get_craft_average(dims: dict, weights: dict) -> float:
    total = 0.0
    w = 0
    for k, wt in weights.items():
        total += wt * dims[k]
        w += wt
    return ps_round(total / w, 1)
