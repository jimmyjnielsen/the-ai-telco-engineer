#!/usr/bin/env python3
"""Compute per-generation held-out eval SE for link_adaptation_f2 (Op-G4*).

For each generation finds the running-best workspace (by training metric),
evaluates it with evaluate_final.py, and appends an "Op-G4*" entry to
paper/figures/per_gen_eval_se.json.

Usage (run from repo root on connectivity1):
    python per_gen_eval_f2.py
"""

import json
import subprocess
import sys
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent
TASK_DIR = REPO / "tasks" / "link_adaptation_f2"
EVAL_SCRIPT = REPO / "tasks" / "link_adaptation" / "evaluate_final.py"
WORKSPACES = TASK_DIR / "workspaces"
OUTPUT_JSON = REPO / "paper" / "figures" / "per_gen_eval_se.json"
LABEL = "Op-G4*"


def get_running_best(leaderboard: dict) -> list[tuple[int, str, float]]:
    """Return [(gen, workspace_id, train_metric)] for the running-best at each gen."""
    candidates = [
        c
        for cluster in leaderboard["clusters"].values()
        for c in cluster
        if c.get("metric") is not None and c["metric"] > 0
    ]
    max_gen = max(c["generation"] for c in candidates)

    running_best_metric = -float("inf")
    running_best_ws = None
    result = []
    for g in range(max_gen + 1):
        gen_candidates = [c for c in candidates if c["generation"] == g]
        for c in gen_candidates:
            if c["metric"] > running_best_metric:
                running_best_metric = c["metric"]
                running_best_ws = c["workspace_id"]
        result.append((g, running_best_ws, running_best_metric))
    return result


def eval_workspace(workspace_id: str) -> float | None:
    """Run evaluate_final.py on a workspace, return mean eval-set SE."""
    ws_path = WORKSPACES / workspace_id
    solution = ws_path / "solution.py"
    if not solution.exists():
        solution = ws_path / "draft.py"
    if not solution.exists():
        print(f"  [{workspace_id}] no solution.py or draft.py — skipping")
        return None

    cmd = [
        sys.executable, str(EVAL_SCRIPT),
        str(solution),
        "--split", "evaluation",
        "--no-olla",
        "--workers", "10",
        "--output-dir", str(ws_path / "eval_results"),
        "--label", workspace_id,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  [{workspace_id}] evaluate_final.py failed:\n{result.stderr[-500:]}")
        return None

    # Parse "Mean SE: X.XXXX bps/Hz" from stdout
    m = re.search(r"Mean SE:\s+([\d.]+)", result.stdout)
    if not m:
        print(f"  [{workspace_id}] could not parse Mean SE from output")
        print(result.stdout[-300:])
        return None
    return float(m.group(1))


def main():
    lb = json.load(open(WORKSPACES / "leaderboard.json"))
    running_best = get_running_best(lb)

    per_gen = []
    cache: dict[str, float | None] = {}

    for g, ws_id, train_metric in running_best:
        if ws_id is None:
            print(f"  gen {g}: no successful candidate — skipping")
            per_gen.append([g, None, None, None])
            continue

        if ws_id not in cache:
            print(f"  gen {g}: evaluating {ws_id} (train={train_metric:.4f}) ...")
            cache[ws_id] = eval_workspace(ws_id)
        else:
            print(f"  gen {g}: reusing cached result for {ws_id}")

        eval_se = cache[ws_id]
        print(f"    -> eval SE = {eval_se}")
        per_gen.append([g, ws_id, round(train_metric, 4), eval_se])

    # Update per_gen_eval_se.json
    data = json.load(open(OUTPUT_JSON))
    data[LABEL] = {"task_dir": "link_adaptation_f2", "per_gen": per_gen}
    with open(OUTPUT_JSON, "w") as f:
        json.dump(data, f, indent=2)
    print(f"\nWrote {LABEL} entry ({len(per_gen)} gens) to {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
