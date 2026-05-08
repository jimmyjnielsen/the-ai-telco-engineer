"""Evaluation harness for the cell sleep scheduling task.

Loads the agent's ``draft.py``, runs the sleep policy across multiple traffic
scenarios, and prints a result line in the format expected by EvalTool:

    SUCCESS, <metric>
    <optional detail lines>

or

    FAILURE,
    <reason>

The metric is the average energy savings percentage (higher is better).
Energy savings are only counted for time steps where both constraints hold:
  - Coverage: every sleeping cell has at least one active neighbour.
  - Overload: cells with PRB utilisation above OVERLOAD_THRESHOLD stay active.
"""

import importlib.util
import sys
import numpy as np
from utils import make_hex_topology, generate_traffic, compute_effective_loads

OVERLOAD_THRESHOLD = 0.80   # cells above this load must not sleep
SWITCH_COST = 2             # active-cell time steps charged per state transition
EVAL_SEEDS = [42, 123, 456]  # three independent traffic scenarios
T = 288                      # time steps (5-min intervals = 24 h)


def load_policy(filename: str):
    spec = importlib.util.spec_from_file_location("draft", filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "sleep_policy"):
        raise AttributeError("draft.py must define a function named 'sleep_policy'")
    return mod.sleep_policy


def check_coverage(active: np.ndarray, neighbor_matrix: np.ndarray) -> bool:
    """Every sleeping cell must have at least one active neighbour."""
    sleeping = np.where(active == 0)[0]
    for i in sleeping:
        if not np.any((neighbor_matrix[i] == 1) & (active == 1)):
            return False
    return True


def run_scenario(policy, traffic: np.ndarray, neighbor_matrix: np.ndarray):
    """Run one 24-h scenario.  Returns (savings_pct, ok, fail_reason)."""
    N = neighbor_matrix.shape[0]
    total_sleeping = 0
    total_transitions = 0
    prev_active = np.ones(N, dtype=int)  # network starts fully active

    for t in range(T):
        loads = traffic[t]

        # Policy observes effective loads based on the previous active set
        effective_prev = compute_effective_loads(loads, prev_active, neighbor_matrix)

        try:
            active = np.asarray(
                policy(effective_prev, neighbor_matrix, prev_active), dtype=int
            ).flatten()
        except Exception as exc:
            return 0.0, False, f"policy raised exception at step {t}: {exc}"

        if active.shape != (N,):
            return 0.0, False, f"policy returned shape {active.shape}, expected ({N},)"

        active = np.clip(active, 0, 1)

        # Overload constraint: offloaded traffic must not push any active cell above threshold
        effective_now = compute_effective_loads(loads, active, neighbor_matrix)
        offload_overloaded = (effective_now > OVERLOAD_THRESHOLD) & (effective_now > loads) & (active == 1)
        if np.any(offload_overloaded):
            bad = np.where(offload_overloaded)[0].tolist()
            return 0.0, False, (
                f"overload constraint violated at step {t}: offloaded traffic pushed "
                f"cells {bad} to effective loads {effective_now[bad].round(3).tolist()}"
            )

        # Coverage constraint
        if not check_coverage(active, neighbor_matrix):
            sleeping_no_nbr = [
                i for i in range(N)
                if active[i] == 0 and not np.any((neighbor_matrix[i] == 1) & (active == 1))
            ]
            return 0.0, False, (
                f"coverage constraint violated at step {t}: "
                f"cells {sleeping_no_nbr} are sleeping with no active neighbour"
            )

        total_sleeping += int(N - active.sum())
        total_transitions += int(np.sum(active != prev_active))
        prev_active = active.copy()

    # Net savings after switching penalty
    net_sleeping = total_sleeping - SWITCH_COST * total_transitions
    savings_pct = 100.0 * net_sleeping / (N * T)
    return savings_pct, True, f"transitions={total_transitions} penalty={SWITCH_COST * total_transitions}"


def main():
    filename = sys.argv[1] if len(sys.argv) > 1 else "draft.py"

    try:
        policy = load_policy(filename)
    except Exception as exc:
        print(f"FAILURE,\nFailed to load {filename}: {exc}")
        return

    _, neighbor_matrix = make_hex_topology()
    per_scenario = []

    for seed in EVAL_SEEDS:
        traffic = generate_traffic(neighbor_matrix.shape[0], T, seed=seed)
        savings, ok, reason = run_scenario(policy, traffic, neighbor_matrix)
        if not ok:
            print(f"FAILURE,\nScenario seed={seed}: {reason}")
            return
        per_scenario.append((savings, reason))

    avg = float(np.mean([s for s, _ in per_scenario]))
    detail = "  ".join(
        f"seed={s}: {v:.1f}% ({info})"
        for s, (v, info) in zip(EVAL_SEEDS, per_scenario)
    )
    print(f"SUCCESS, {avg:.4f}")
    print(f"Net energy savings per scenario — {detail}")
    print(f"Average net energy savings: {avg:.1f}%  (SWITCH_COST={SWITCH_COST})")


if __name__ == "__main__":
    main()
