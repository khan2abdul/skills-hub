#!/usr/bin/env python3
"""Compares every shipped skill against the upstream original it was fetched from,
using ONE rubric for both sides.

Port of tools/compare-skills.ps1. Answers three questions the plain rating cannot:

  fidelity  did we copy it faithfully?        body bytes, payload files, frontmatter
  gap       what does the original have that ours does not?
  ceiling   what would it take to reach 10?

The ceiling question matters because our copies are verbatim: when the shipped
skill scores 6, the original also scores 6. The defect is not in our copy, it is
in the choice of source. Only composing a stronger source can move it.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hubcommon as C  # noqa: E402
import hubrubric as R  # noqa: E402

RED, GREEN, YELLOW, CYAN, RESET = "\033[31m", "\033[32m", "\033[33m", "\033[36m", "\033[0m"

WEIGHTS = {"structure": 15, "procedure": 20, "gates": 15, "references": 20, "portability": 15, "size": 15}
CRAFT_SHARE = 0.75


def get_renamed_upstream(raw: str, new_name: str) -> str:
    """Mirror vendor.py exactly: rewrite name: only inside the frontmatter block."""
    m = re.match(r'\A(---\r?\n)(.*?)(\r?\n---\r?\n)', raw, re.S)
    if not m:
        return raw
    yaml2 = re.sub(r'(?m)^name:\s*.*$', f"name: {new_name}", m.group(2))
    return m.group(1) + yaml2 + m.group(3) + raw[m.end():]


def sha256_file(p: str | Path) -> str:
    return hashlib.sha256(C.read_bytes(p)).hexdigest().upper()


def get_payload_diff(up_dir: str | Path, sh_dir: str | Path) -> dict:
    missing, differs, count = [], [], 0
    up_dir = Path(up_dir)
    sh_dir = Path(sh_dir)
    # Get-ChildItem -Recurse walks breadth-ish with directories interleaved, so
    # the original's "first 5" sample listed root files before nested ones. Sort
    # by depth then name to keep that sample order: the reader sees the top-level
    # payload first, which is what "what am I missing" means.
    files = [f for f in up_dir.rglob("*") if f.is_file() and f.name != "SKILL.md"]
    files.sort(key=lambda f: (len(f.relative_to(up_dir).parts), str(f).lower()))
    for f in files:
        count += 1
        rel = f.relative_to(up_dir).as_posix()
        tgt = sh_dir / rel
        if not tgt.exists():
            missing.append(rel)
        elif sha256_file(f) != sha256_file(tgt):
            differs.append(rel)
    return {"count": count, "missing": missing, "differs": differs}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--what-if", action="store_true")
    args = ap.parse_args(argv)

    hub = C.get_hub_root()
    skills_dir = hub / "skills"
    cov = C.get_skill_coverage()
    index, shipped, ignored = cov["index"], cov["shipped"], cov["ignored"]
    cands = {s.get("name"): list(s.get("candidates") or []) for s in cov["manifest"]}

    rows = []
    for d in sorted((p for p in skills_dir.iterdir() if p.is_dir()), key=lambda p: p.name):
        file = d / "SKILL.md"
        if not file.is_file():
            continue
        name = d.name
        text = C.read_text(file)
        ours = R.get_craft_score(text, name, str(d))
        our_craft = R.get_craft_average(ours["dims"], WEIGHTS)

        prov_file = d / "PROVENANCE.md"
        prov = C.read_text(prov_file) if prov_file.is_file() else ""
        is_composed = bool(re.search(r'(?m)^- mode:\s*composed', prov))
        # A verbatim skill's PROVENANCE names its upstream directly. The reverse
        # `shipped` map keeps only the FIRST canonical per upstream, so a source
        # used by two skills left the second one as 'n/a'.
        upstream = (re.search(r'(?m)^- upstream:\s*(.+?)\s*$', prov) or [None, ""])[1]
        if is_composed:
            sources = sorted(k for k, v in shipped.items() if v == name)
        elif upstream:
            sources = [upstream]
        else:
            sources = []
        primary = sources[0] if sources else None

        # ---- fidelity: for a verbatim copy the body must match the original byte
        # for byte once the frontmatter name: line is rewritten.
        fidelity = "n/a"
        body_diff = []
        if not is_composed and primary and primary in index:
            up_renamed = get_renamed_upstream(C.read_text(index[primary]["file"]), name)
            if up_renamed == text:
                fidelity = "exact"
            else:
                fidelity = "differs"
                a = re.split(r'\r?\n', up_renamed)
                b = re.split(r'\r?\n', text)
                for i in range(max(len(a), len(b))):
                    av = a[i] if i < len(a) else "<eof>"
                    bv = b[i] if i < len(b) else "<eof>"
                    if av != bv:
                        body_diff.append(f"L{i + 1}: '{av}' -> '{bv}'")
        elif is_composed:
            fidelity = "composed"

        # ---- upstream baseline: score the original with the same ruler. Reference
        # checks run against the SHIPPED dir: we are asking "is this original fully
        # usable here", and a payload file we already vendored counts as present.
        ups = []
        for sn in sources:
            if sn not in index:
                continue
            u_dir = Path(index[sn]["dir"])
            u_text = C.read_text(index[sn]["file"])
            u = R.get_craft_score(u_text, u_dir.name, str(d))
            pay = get_payload_diff(u_dir, d)
            ups.append({
                "name": sn, "repo": index[sn]["repo"], "dir": str(u_dir), "chars": C.ps_len(u_text),
                "craft": R.get_craft_average(u["dims"], WEIGHTS), "dims": u["dims"], "evidence": u["evidence"],
                "payloadUp": pay["count"], "payloadMissing": pay["missing"], "payloadDiffers": pay["differs"],
            })
        best_up = max(ups, key=lambda u: u["craft"]) if ups else None

        # ---- gap: what does the original have that ours does not
        gaps = []
        for u in ups:
            if u["payloadMissing"]:
                shown = ", ".join(u["payloadMissing"][:5])
                gaps.append({"kind": "payload", "detail": f"original ships {len(u['payloadMissing'])} file(s) we do not: {shown}"})
            if not is_composed:
                for dim in WEIGHTS:
                    if u["dims"][dim] > ours["dims"][dim]:
                        gaps.append({
                            "kind": f"dim:{dim}",
                            "detail": f"original has {'; '.join(u['evidence'][dim])} vs ours {'; '.join(ours['evidence'][dim])}",
                        })
        if is_composed and best_up and best_up["chars"] > C.ps_len(text):
            gaps.append({
                "kind": "truncated",
                "detail": f"composition ({C.ps_len(text)}c) is smaller than '{best_up['name']}' ({best_up['chars']}c) alone",
            })
        if body_diff:
            gaps.append({
                "kind": "body",
                "detail": f"body differs from the original in {len(body_diff)} place(s): {' | '.join(body_diff[:3])}",
            })

        # ---- ceiling: score every alternative the manifest proposed, including the
        # ones that were dropped. If one beats what we shipped, that is the fix.
        alts = []
        for c in cands.get(name) or []:
            if not c or c == name:
                continue
            if c in shipped and shipped[c] != name:
                continue  # used by another skill
            if c not in index:
                continue
            c_dir = index[c]["dir"]
            c_text = C.read_text(index[c]["file"])
            cs = R.get_craft_score(c_text, Path(c_dir).name, c_dir)
            alts.append({
                "name": c, "repo": index[c]["repo"], "chars": C.ps_len(c_text),
                "craft": R.get_craft_average(cs["dims"], WEIGHTS), "dims": cs["dims"],
                "ignored": c in ignored, "shippedElsewhere": c in shipped,
            })
        # Stable sort: on a craft tie, keep the manifest candidates order, which is
        # what Sort-Object -Descending did for equal keys.
        alts.sort(key=lambda a: -a["craft"])
        best_alt = alts[0] if alts else None

        # ---- what would it take to reach 10
        verdict = ""
        actions = []
        if fidelity == "differs":
            verdict = "copy is not faithful"
            actions.append(f"this is a bug in the hub, not in the source: re-run python tools/vendor.py --skill {name} --force")
        if ups and not is_composed and abs(best_up["craft"] - our_craft) < 0.05:
            verdict = "faithful copy; the score IS the original score"
        if is_composed:
            verdict = "composition; measured against its own sources"

        # reachable ceiling = best craft among our own content and any alternative
        targets = [our_craft] + [a["craft"] for a in alts] + [u["craft"] for u in ups]
        reachable = max(targets)
        selection_score = min(10, our_craft / reachable * 10) if reachable > 0 else 10

        if best_alt and best_alt["craft"] > our_craft + 0.05:
            actions.append(f"re-vendor from '{best_alt['name']}' (craft {C.ps_num(best_alt['craft'])}) instead of '{primary}' (craft {C.ps_num(our_craft)})")
            actions.append(f"python tools/vendor.py --skill {name} --force   # after flipping chosen in manifest.yml")
        for dim in WEIGHTS:
            if ours["dims"][dim] < 10:
                fixer = next((a for a in alts if a["dims"][dim] > ours["dims"][dim]), None)
                if fixer:
                    actions.append(f"gains {dim} ({ours['dims'][dim]} -> {fixer['dims'][dim]}) by composing '{fixer['name']}'")
        if ours["notExecutable"]:
            actions.append("not executable here: its hooks call scripts the hub does not ship - replace the source or accept it as read-only guidance")

        score = C.ps_round(CRAFT_SHARE * our_craft + (1 - CRAFT_SHARE) * selection_score, 1)

        rows.append({
            "name": name, "score": score, "craft": our_craft, "selection": C.ps_round(selection_score, 1),
            "chars": C.ps_len(text), "fidelity": fidelity, "composed": is_composed,
            "upstream": best_up, "upstreams": ups, "gaps": gaps, "alts": alts,
            "bestAlt": best_alt, "verdict": verdict, "actions": actions,
            "reachable": C.ps_round(CRAFT_SHARE * reachable + (1 - CRAFT_SHARE) * 10, 1),
            "dims": ours["dims"], "evidence": ours["evidence"],
        })

    if not rows:
        print(f"{RED}no skills found{RESET}")
        return 2

    # --- guard: every shipped skill must appear, or the report hides a gap
    dirs = sum(1 for p in skills_dir.iterdir() if p.is_dir() and (p / "SKILL.md").is_file())
    if len(rows) != dirs:
        print(f"{RED}compared {len(rows)} of {dirs} skill dirs{RESET}")
        return 1

    mean_ours = C.ps_round(sum(r["craft"] for r in rows) / len(rows), 2)
    with_up = [r for r in rows if r["upstream"]]
    mean_up = C.ps_round(sum(r["upstream"]["craft"] for r in with_up) / len(with_up), 2) if with_up else 0
    lossy = [r for r in rows if r["fidelity"] == "differs"]
    with_alts = [r for r in rows if r["bestAlt"] and r["bestAlt"]["craft"] > r["craft"] + 0.05]

    if args.what_if:
        rows_sorted = sorted(rows, key=lambda r: (r["score"], r["name"]))
        heads = ["skill", "ours", "orig", "bestAlt", "fid", "ceil"]
        table = []
        for r in rows_sorted:
            table.append([
                r["name"], str(r["craft"]),
                str(r["upstream"]["craft"]) if r["upstream"] else "-",
                f"{r['bestAlt']['name']}={r['bestAlt']['craft']}" if r["bestAlt"] else "-",
                r["fidelity"], str(r["reachable"]),
            ])
        widths = [max(len(h), *(len(row[i]) for row in table)) for i, h in enumerate(heads)]
        numeric = [False, True, True, False, False, True]
        gap = "  "

        def fmt(cells):
            return gap.join(str(c).rjust(w) if num else str(c).ljust(w)
                            for c, w, num in zip(cells, widths, numeric))

        print(fmt(heads))
        print(fmt(["-" * w for w in widths]))
        for row in table:
            print(fmt(row))
        print(f"{CYAN}WOULD write COMPARISON.md: mean ours {C.ps_num(mean_ours)} vs originals {C.ps_num(mean_up)}, "
              f"lossy {len(lossy)}, improvable {len(with_alts)}{RESET}")
        return 0

    # ---------------------------------------------------------------- output
    md: list[str] = []

    def W(s: str = "") -> None:
        md.append(s)

    exact = sum(1 for r in rows if r["fidelity"] == "exact")
    composed_n = sum(1 for r in rows if r["fidelity"] == "composed")
    W("# Shipped vs original")
    W("")
    W("Every skill compared against the upstream original it was fetched from, scored")
    W("with the same rubric (`tools/hubrubric.py`). Wire: `tools/compare_skills.py`.")
    W("")
    W(f"**Craft: ours {C.ps_num(mean_ours)} vs originals {C.ps_num(mean_up)}.** "
      f"Faithfulness: {exact} exact, {composed_n} composed, {len(lossy)} lossy.")
    W("")
    W("The headline: our copies are verbatim, so a low score is almost never a")
    W("transcription defect. When ours scores 6, the original also scores 6. The")
    W("defect is the **choice of source**, and the only legal fix is to take a better")
    W("one - composing in sections, or re-vendoring from a stronger candidate.")
    W("")
    W("## Fidelity")
    W("")
    W("| check | result |")
    W("|---|---|")
    W(f"| body byte-identical to original | {exact}/{len(rows)} |")
    W(f"| body differs | {len(lossy)} |")
    W(f"| payload files missing vs original | {sum(1 for r in rows if r['upstream'] and r['upstream']['payloadMissing'])} skills |")
    W(f"| payload files altered | {sum(1 for r in rows if r['upstream'] and r['upstream']['payloadDiffers'])} skills |")
    W("")

    W("## Score against the original")
    W("")
    W("| skill | ours | original | from | fidelity | reachable | gaps |")
    W("|---|---|---|---|---|---|---|")
    for r in sorted(rows, key=lambda r: (r["score"], r["name"])):
        u = r["upstream"]
        orig_s = str(C.ps_num(u["craft"])) if u else "-"
        orig_n = f"`{u['name']}` ({u['repo']})" if u else "-"
        W(f"| `{r['name']}` | {C.ps_num(r['craft'])} | {orig_s} | {orig_n} | {r['fidelity']} | {C.ps_num(r['reachable'])} | {len(r['gaps'])} |")
    W("")

    W("## Missing pieces")
    W("")
    any_gap = [r for r in rows if r["gaps"]]
    if not any_gap:
        W("None. Every shipped skill carries everything its original carries.")
    for r in any_gap:
        u = r["upstream"]
        W(f"### `{r['name']}` - {C.ps_num(r['craft'])}/10 (original {C.ps_num(u['craft']) if u else 'n/a'})")
        W("")
        for g in r["gaps"]:
            W(f"- **{g['kind']}** - {g['detail']}")
        W("")

    W("## What would make each one a 10")
    W("")
    W("Reachable is the ceiling with the material already in `repos/`: our own text")
    W("plus every candidate the manifest proposed. A skill whose reachable equals its")
    W("current score is at its ceiling and cannot be improved without new source material.")
    W("")
    W("| skill | now | reachable | the move |")
    W("|---|---|---|---|")
    for r in sorted(rows, key=lambda r: (r["score"], r["name"])):
        move = r["actions"][0].replace("|", "/") if r["actions"] else "at ceiling - no better source in repos/"
        if len(r["actions"]) > 1:
            move += f" (+{len(r['actions']) - 1} more)"
        W(f"| `{r['name']}` | {C.ps_num(r['craft'])} | {C.ps_num(r['reachable'])} | {move} |")
    W("")

    W("## Detail")
    W("")
    for r in sorted(rows, key=lambda r: (r["score"], r["name"])):
        W(f"### `{r['name']}` - {C.ps_num(r['score'])}/10")
        W("")
        W(f"fidelity: {r['fidelity']}{(' - ' + r['verdict']) if r['verdict'] else ''}")
        W("")
        if r["upstreams"]:
            W("| source | repo | chars | craft | " + " | ".join(WEIGHTS) + " |")
            W("|---|---|---|---|" + "|".join("---" for _ in WEIGHTS) + "|")
            for u in r["upstreams"]:
                ds = " | ".join(str(u["dims"][k]) for k in WEIGHTS)
                W(f"| `{u['name']}` | {u['repo']} | {u['chars']} | {C.ps_num(u['craft'])} | {ds} |")
            W("")
            W("ours: " + ", ".join(f"{k} {r['dims'][k]}" for k in WEIGHTS))
            W("")
        if r["alts"]:
            W("alternatives the manifest proposed (best first):")
            W("")
            for a in r["alts"][:4]:
                tag = "in use elsewhere" if a["shippedElsewhere"] else ("rejected" if a["ignored"] else "dropped")
                arrow = " **better than ours**" if a["craft"] > r["craft"] + 0.05 else ""
                W(f"- `{a['name']}` ({a['repo']}, {a['chars']}c) craft {C.ps_num(a['craft'])} - {tag}{arrow}")
            W("")
        if r["actions"]:
            W("to improve:")
            W("")
            for a in r["actions"]:
                W(f"- {a}")
            W("")

    C.write_text(hub / "COMPARISON.md", "\n".join(md) + "\n")

    print(f"{GREEN}wrote COMPARISON.md{RESET}")
    print(f"  craft ours {C.ps_num(mean_ours)} vs originals {C.ps_num(mean_up)}")
    colour = YELLOW if lossy else GREEN
    print(f"  {colour}fidelity: {exact} exact, {len(lossy)} lossy{RESET}")
    print(f"  improvable by taking a better source: {len(with_alts)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
