#!/usr/bin/env python3
"""Extract oldest-referenced-workspace-gen per generation for Op-G4* (f2).

Outputs paper/figures/ref_oldest_gen.json with per-gen data for the
run-2 portion of f2 (the complete 10-gen run, workspaces gen04-gen13).

Usage (run from repo root on connectivity1):
    python ref_oldest_gen.py
"""

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent
LOG = REPO / "tasks" / "link_adaptation_f2" / "workspaces" / "manager.log"
OUTPUT = REPO / "paper" / "figures" / "ref_oldest_gen.json"


def main():
    log = LOG.read_text(errors="replace")

    pattern = re.compile(
        r"\[RESPONSE \((initial ideas|ideas from results)\)\]\n(\[.*?\])\n\n={60}",
        re.DOTALL,
    )
    all_responses = list(pattern.finditer(log))
    # Run 2 starts at index 4 (fresh "initial ideas" after 3 from-results + 1 initial)
    run2_responses = all_responses[4:]

    data = []
    for i, m in enumerate(run2_responses):
        abs_gen = i + 4          # absolute workspace gen (gen04 = run2 gen 0, etc.)
        current_ws_gen = abs_gen # workspace IDs for this gen are genXX-YYYY
        try:
            ideas = json.loads(m.group(2))
        except json.JSONDecodeError:
            data.append({"rel_gen": i, "abs_gen": abs_gen, "oldest_ref": None, "all_refs": []})
            continue

        ref_gens = set()
        for idea in ideas:
            for ref in re.findall(r"gen(\d+)-\d+", idea.get("reference_workspaces", "")):
                ref_gens.add(int(ref))

        oldest = min(ref_gens) if ref_gens else None
        data.append({
            "rel_gen": i,
            "abs_gen": abs_gen,
            "oldest_ref": oldest,
            "all_refs": sorted(ref_gens),
        })
        print(f"rel gen {i:2d} (abs gen{abs_gen:02d}): oldest_ref={oldest}  all={sorted(ref_gens)}")

    with open(OUTPUT, "w") as f:
        json.dump(data, f, indent=2)
    print(f"\nWrote {OUTPUT}")


if __name__ == "__main__":
    main()
