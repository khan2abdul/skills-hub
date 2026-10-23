#!/usr/bin/env python3
"""Scores every shipped skill out of 10 and writes RATING.md + RATING.json.

Port of tools/rate-skills.ps1.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hubcommon as C  # noqa: E402
import hubrubric as R  # noqa: E402

RED, GREEN, YELLOW, CYAN, RESET = "\033[31m", "\033[32m", "\033[33m", "\033[36m", "\033[0m"

RUBRIC_VERSION = 2
CRAFT_SHARE = 0.75
# Craft weights sum to 100.
WEIGHTS = {
    "structure": 15, "procedure": 20, "gates": 15,
    "references": 20, "portability": 15, "size": 15,
}
DIM_HELP = {
    "structure": "frontmatter parses, name matches dir, description usable",
    "procedure": "numbered steps and headings - does it say what to do",
    "gates": "STOP/MUST/NEVER and verification language",
    "references": "files the body names exist in the skill dir",
    "portability": "no absolute paths or uninstalled vendor helpers",
    "size": "big enough to be a procedure, small enough to load",
}
GAIN_BY_FINDING = {
    "EMPTY-BODY": 3.0, "REF-MISSING": 2.5, "VENDOR-HELPER": 2.0,
    "BIGGER-CANDIDATE": 1.5, "SLASH-ONLY": 0.8,
}


def r1(x: float) -> float:
    return C.ps_round(x, 1)


def r2(x: float) -> float:
    return C.ps_round(x, 2)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--what-if", action="store_true")
    args = ap.parse_args(argv)

    hub = C.get_hub_root()
    skills_dir = hub / "skills"
    if not skills_dir.is_dir():
        print(f"{RED}no skills/ directory{RESET}")
        return 2

    cov = C.get_skill_coverage()
    index, shipped, ignored = cov["index"], cov["shipped"], cov["ignored"]

    # canonical -> candidate upstream names, from the manifest
    cands = {s.get("name"): list(s.get("candidates") or []) for s in cov["manifest"]}

    rows = []
    for d in sorted((p for p in skills_dir.iterdir() if p.is_dir()), key=lambda p: p.name):
        file = d / "SKILL.md"
        if not file.is_file():
            continue
        name = d.name
        text = C.read_text(file)
        findings: list[dict] = []
        fixes: list[dict] = []

        # All six craft dimensions come from the shared rubric so that this tool
        # and compare_skills.py cannot disagree about the same file.
        craft0 = R.get_craft_score(text, name, str(d))
        body = craft0["body"]
        dims = craft0["dims"]
        ev = craft0["evidence"]
        missing = craft0["missing"]

        # ---- body that cannot run here: frontmatter plus instructions to call
        # scripts the hub does not ship. Prose and bullets do not make it executable.
        dep_scripts, has_hooks = craft0["depScripts"], craft0["hasHooks"]
        if craft0["notExecutable"]:
            why = (
                f"hooks plus {len(dep_scripts)} helper script(s) the hub does not ship"
                if has_hooks
                else f"body is {C.ps_len(body.strip())} chars; the skill is its frontmatter"
            )
            findings.append({
                "id": "EMPTY-BODY", "severity": "high", "auto": False,
                "message": f"{why} - the skill does nothing in this install",
                "suggest": "re-vendor a prose skill for this capability, or drop the entry",
            })

        # ---- broken references: copy the file from upstream, body untouched
        # The manifest's `composed` list is authoritative and is what verify.py
        # re-hashes against. get_shipped_sources cannot answer this: it maps each
        # upstream skill to ONE canonical name, so when two skills compose the
        # same upstream (frontend-ui-engineering feeds both check-my-ui and
        # polish-the-ui) only the first keeps the link.
        me = [s for s in cov["manifest"] if s.get("name") == name]
        if me and (me[0].get("composed") or []):
            sources = list(me[0]["composed"])
        else:
            sources = [k for k, v in shipped.items() if v == name]

        for r in missing:
            src = None
            for sname in sources:
                if sname not in index:
                    continue
                srcdir = Path(index[sname]["dir"])
                candidate = srcdir / r.replace("/", "\\")
                if candidate.exists():
                    src = candidate
                    break
                # upstream may keep the payload at the repo root (gstack ships
                # scripts/ and bin/ there, not inside each skill dir), so walk up
                # a bounded number of levels
                probe = srcdir
                for _up in range(4):
                    probe = probe.parent
                    if not probe or probe == probe.parent:
                        break
                    try_it = probe / r.replace("/", "\\")
                    if try_it.exists():
                        src = try_it
                        break
                if src:
                    break
                found = next((p for p in srcdir.rglob(Path(r).name) if p.is_file()), None)
                if found:
                    src = found
                    break
            findings.append({
                "id": "REF-MISSING", "severity": "high", "auto": src is not None,
                "message": f"body names `{r}` but the skill does not ship it", "suggest": "",
            })
            if src:
                rel = str(src)[len(str(hub)):].lstrip("\\/")
                fixes.append({
                    "kind": "payload", "skill": name, "ref": r,
                    "source": rel,
                    "target": f"{name}/{r.replace('/', chr(92))}",
                    "finding": "REF-MISSING",
                })

        # ---- vendor helpers that are not installed
        helpers = sorted({m.group(1) for m in re.finditer(r'gstack/bin/([A-Za-z0-9_.\-]+)', body)})
        if helpers:
            findings.append({
                "id": "VENDOR-HELPER", "severity": "high", "auto": False,
                "message": f"calls {len(helpers)} gstack helper(s) the hub does not install; vendor bin/ or drop the calls",
                "suggest": "vendor gstack bin/ for this skill, or re-vendor a prose-only alternative",
            })

        craft = sum(w * dims[k] for k, w in WEIGHTS.items()) / sum(WEIGHTS.values())

        # ---- selection: was this the strongest source for the job?
        # Scored on CRAFT, not byte count. Size was a bad proxy: `spec` is 18x
        # larger than `to-spec` and scores 6.9 vs 8.4.
        better = []
        for c in cands.get(name, []):
            if not c:
                continue
            if c in shipped or c in ignored or c == name:
                continue
            if c not in index:
                continue
            cf = index[c]["file"]
            cs = R.get_craft_score(C.read_text(cf), c, str(Path(cf).parent))
            better.append({
                "name": c,
                "chars": Path(cf).stat().st_size,
                "craft": r2(R.get_craft_average(cs["dims"], WEIGHTS)),
            })
        # highest craft first; name breaks ties so output is reproducible
        better.sort(key=lambda b: (-b["craft"], b["name"]))

        sel = 10
        sel_note = "no candidate scores higher"
        sel_problem = False
        # A composed skill already absorbed its candidates. Judge it on craft: if
        # it writes at least as well as the best source it used, the choice was right.
        is_composed = len(sources) > 1
        if is_composed:
            best_src, best_name = 0.0, ""
            for sname in sources:
                if sname not in index:
                    continue
                sf = index[sname]["file"]
                ss = R.get_craft_score(C.read_text(sf), sname, str(Path(sf).parent))
                sc = R.get_craft_average(ss["dims"], WEIGHTS)
                if sc > best_src:
                    best_src, best_name = r2(sc), sname
            if craft >= best_src - 0.05:
                sel = 10
                sel_note = f"composed from {len(sources)} sources, craft matches best source ({best_name} {C.ps_num(best_src)})"
            else:
                sel = 7
                sel_note = f"composition craft {C.ps_num(r1(craft))} is below its best source ({best_name} {C.ps_num(best_src)})"
                sel_problem = True
        # A very large body costs context even when it is the best available: it
        # is not a wrong choice, but it is not a 10 either.
        elif C.ps_len(text) > 45000:
            sel = 8
            sel_note = f"largest body in the hub ({C.ps_len(text)}c); right choice, heavy to load"
            sel_problem = True
        elif better:
            gap = r1(better[0]["craft"] - craft)
            best = better[0]
            if gap >= 1.0:
                sel = 4
                sel_note = f"candidate '{best['name']}' writes better (craft {C.ps_num(best['craft'])} vs {C.ps_num(r1(craft))})"
                sel_problem = True
            elif gap >= 0.3:
                sel = 7
                sel_note = f"candidate '{best['name']}' writes slightly better (craft {C.ps_num(best['craft'])} vs {C.ps_num(r1(craft))})"
                sel_problem = True
            else:
                sel = 10
                sel_note = f"no candidate writes better (best is {best['name']} at {C.ps_num(best['craft'])} vs {C.ps_num(r1(craft))})"
        # Only a real selection problem is a finding; "-1 for being smaller" is noise.
        if sel_problem:
            findings.append({
                "id": "BIGGER-CANDIDATE", "severity": "medium", "auto": False,
                "message": sel_note,
                "suggest": f"python tools/compose.py --name {name}   # add its sections, or re-vendor from it",
            })

        if re.search(r'(?m)^disable-model-invocation:\s*true', text):
            findings.append({
                "id": "SLASH-ONLY", "severity": "medium", "auto": False,
                "message": f"model cannot select this skill; only /{name} runs it",
                "suggest": "decide: human-invoked by design, or drop that line in the compose spec",
            })

        score = r1(CRAFT_SHARE * craft + (1 - CRAFT_SHARE) * sel)

        rows.append({
            "name": name, "score": C.ps_num(score), "grade": R.get_grade(score),
            "craft": C.ps_num(r1(craft)), "selection": sel, "selection_note": sel_note,
            "chars": C.ps_len(text), "dimensions": dims, "evidence": ev,
            "findings": findings, "fixes": fixes,
        })

    if not rows:
        print(f"{RED}no skills found{RESET}")
        return 2

    # Guard: a report that silently skips a skill is worse than no report.
    dirs = sum(1 for p in skills_dir.iterdir() if p.is_dir() and (p / "SKILL.md").is_file())
    if len(rows) != dirs:
        print(f"{RED}rated {len(rows)} of {dirs} skill dirs{RESET}")
        return 1

    # ---------------------------------------------------------------- plan
    plan = []
    for r in rows:
        for f in r["findings"]:
            plan.append({
                "skill": r["name"], "finding": f["id"], "severity": f["severity"],
                "auto": f["auto"], "gain": GAIN_BY_FINDING.get(f["id"], 1.0),
                "message": f["message"], "command": f["suggest"],
            })
    plan.sort(key=lambda p: (-p["gain"], p["severity"], p["skill"]))

    scores = [r["score"] for r in rows]
    mean = r2(sum(scores) / len(scores))
    auto_count = sum(1 for p in plan if p["auto"])

    if args.what_if:
        rows_sorted = sorted(rows, key=lambda r: (-r["score"], r["name"]))
        heads = ["skill", "score", "grade", "craft", "sel", "chars"]
        table = [[r["name"], str(r["score"]), r["grade"], str(r["craft"]), str(r["selection"]), str(r["chars"])] for r in rows_sorted]
        widths = [max(len(h), *(len(row[i]) for row in table)) for i, h in enumerate(heads)]
        numeric = [False, True, False, True, True, True]
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
        print(f"{CYAN}WOULD write RATING.md + RATING.json: {len(rows)} skills, mean {mean}/10, {auto_count} auto-fixable{RESET}")
        return 0

    # ---------------------------------------------------------------- output
    grade_counts: dict[str, int] = {}
    for r in rows:
        grade_counts[r["grade"]] = grade_counts.get(r["grade"], 0) + 1

    doc = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rubric_version": RUBRIC_VERSION,
        "craft_share": CRAFT_SHARE,
        "weights": WEIGHTS,
        "dim_help": DIM_HELP,
        "summary": {
            "count": len(rows),
            "mean": mean,
            "min": C.ps_num(min(scores)),
            "max": C.ps_num(max(scores)),
            "by_grade": [{"grade": g, "count": c} for g, c in sorted(grade_counts.items())],
            "auto_fixes": auto_count,
        },
        "skills": rows,
        "plan": plan,
    }
    C.write_text(hub / "RATING.json", json.dumps(doc, indent=2, ensure_ascii=False) + "\n")

    md: list[str] = []

    def W(s: str = "") -> None:
        md.append(s)

    W("# Skill rating")
    W("")
    W(f"Every shipped skill scored out of 10 by `tools/rate_skills.py` (rubric v{RUBRIC_VERSION}).")
    W("Wire: `tools/apply_rating.py`. Do not edit by hand - re-run the tool.")
    W("")
    grades = ", ".join(f"{g} {c}" for g, c in sorted(grade_counts.items()))
    W(f"**Mean {mean}/10** over {len(rows)} skills. Grades: {grades}.")
    W("")
    W("The score has two halves, because \"is this a good skill\" and \"was this the")
    W("best skill available\" are different questions:")
    W("")
    W("- **craft (75%)** - is the shipped text well made?")
    W("- **selection (25%)** - did we take the strongest source for the job?")
    W("")
    W("A well-made copy of the wrong skill is still the wrong skill. Selection is")
    W("where a wrong-but-well-made choice shows up.")
    W("")
    W("## Craft dimensions")
    W("")
    W("| dimension | weight | measures |")
    W("|---|---|---|")
    for k, w in WEIGHTS.items():
        W(f"| {k} | {w} | {DIM_HELP[k]} |")
    W("")
    W("## Scoreboard")
    W("")
    W("| # | skill | score | grade | craft | sel | struc | proc | gates | refs | port | size | chars |")
    W("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(sorted(rows, key=lambda r: (-r["score"], r["name"])), 1):
        d = r["dimensions"]
        W(f"| {i} | `{r['name']}` | **{r['score']}** | {r['grade']} | {r['craft']} | {r['selection']} | "
          f"{d['structure']} | {d['procedure']} | {d['gates']} | {d['references']} | "
          f"{d['portability']} | {d['size']} | {r['chars']} |")
    W("")

    W("## How to improve")
    W("")
    W("Ranked by score gain. `auto` fixes are applied by `python tools/apply_rating.py --apply`;")
    W("`no` ones need a decision from you.")
    W("")
    W("| # | skill | finding | gain | auto | what to do |")
    W("|---|---|---|---|---|---|")
    for i, p in enumerate(plan, 1):
        how = p["command"] if p["command"] else p["message"]
        W(f"| {i} | `{p['skill']}` | {p['finding']} | +{p['gain']} | {'yes' if p['auto'] else 'no'} | {how} |")
    W("")

    worst = sorted(
        (r for r in rows if r["findings"]), key=lambda r: (r["score"], r["name"])
    )[:8]
    if worst:
        W("## Why the weakest skills are weak")
        W("")
        for r in worst:
            W(f"### `{r['name']}` - {r['score']}/10 ({r['grade']})")
            W("")
            W(f"- selection {r['selection']}/10 - {r['selection_note']}")
            for k in WEIGHTS:
                if r["dimensions"][k] < 10:
                    W(f"- **{k} {r['dimensions'][k]}/10** - {'; '.join(r['evidence'][k])}")
            for f in r["findings"]:
                W(f"- `{f['id']}` {f['message']}")
            W("")

    C.write_text(hub / "RATING.md", "\n".join(md) + "\n")

    print(f"{GREEN}wrote RATING.md + RATING.json{RESET}")
    print(f"  {len(rows)} skills, mean {mean}/10, {auto_count} auto-fixable")
    weakest = min(rows, key=lambda r: (r["score"], r["name"]))
    print(f"  {YELLOW}weakest: {weakest['name']}{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
