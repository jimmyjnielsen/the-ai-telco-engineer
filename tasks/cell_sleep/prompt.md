# Cell Sleep Scheduling Task

## CRITICAL: Why the obvious approach fails — read this first

> **Do not optimise `sleeping_cells − 2 × transitions` greedily at each step.**
>
> At t=0 all cells are active (0 sleeping). If you sleep k cells at step 1:
> - Gain: k sleeping cell-steps
> - Cost: 2k switching penalty (k wake→sleep transitions)
> - Net at step 1: k − 2k = **−k < 0**
>
> A policy that maximises this score independently at every step will therefore
> **never initiate sleep** and score **0 %**.
>
> Concrete example: sleeping 3 cells gives score = 3 − 6 = −3 < 0.  Any greedy
> per-step maximiser stays all-active forever.
>
> **The fix is temporal commitment:**
> - Sleep a cell when load is clearly low; keep it sleeping for many steps.
> - A cell asleep for S consecutive steps pays only 2 penalty total (one
>   transition in, one out) for S sleep steps: **net gain = S − 2**.
> - For S ≥ 3 the gain is already positive. With autocorrelated traffic, a
>   typical low-load bout lasts 20–50+ steps, so the net gain is large.
> - **Never decide whether to sleep based on the per-step reward.** Decide
>   based on whether load is low enough to justify a long commitment.

## Objective

Implement a **cell sleep scheduling policy** for a 7-cell hexagonal mobile network that
**maximises net energy savings** while satisfying coverage and overload constraints at every
time step.

**Higher net energy savings percentage is better**, subject to both constraints being met at
all times.  State transitions between active and sleep carry a switching cost, so policies
that hold cells in a stable state for long periods outperform those that toggle frequently.

## Context

In mobile networks, base stations (cells) can be put into a low-power sleep mode during
periods of low traffic.  A Non-RT RIC rApp in an O-RAN architecture is a natural home for
this policy: it observes network KPIs via the O1 interface and issues sleep/wake decisions
as A1 policies to the Near-RT RIC.

The network consists of 7 cells arranged in a hexagonal layout: one centre cell (index 0)
surrounded by six ring cells (indices 1–6).  Each cell knows its neighbours.

Your policy is called once per time step with the current traffic load, the fixed neighbour
topology, and the **state from the previous time step**.  It must return a binary
active/sleep decision for every cell.

## Constraints

**Coverage:** A sleeping cell must have at least one active neighbour so that its users
can be served by an adjacent cell.  Any time step where a sleeping cell has no active
neighbour is a constraint violation → FAILURE.

**Overload:** No active cell's **effective** PRB utilisation may exceed 0.8 (80 %).
Effective load = own traffic + OFFLOAD_OVERHEAD × (equal share of each sleeping neighbour's traffic).
Users handed off to a neighbouring BS experience higher path loss and lower SINR, so they
require more PRBs at the same data rate.  The evaluator uses **OFFLOAD_OVERHEAD = 2.0**
(consistent with 3GPP macro-cell path loss exponent ~3.5, inter-site distance ~500 m).
Sleeping a heavily-loaded cell concentrates that load on its active neighbours; if any
active cell's effective load exceeds 0.8 the step is a constraint violation → FAILURE.

## Requirements

### Function Signature

Your solution must define a function with the following signature in ``draft.py``:

```python
import numpy as np

def sleep_policy(traffic_loads: np.ndarray,
                 neighbor_matrix: np.ndarray,
                 prev_active: np.ndarray) -> np.ndarray:
    """Decide which cells sleep and which stay active.

    Parameters
    ----------
    traffic_loads : np.ndarray, shape (N,)
        Effective PRB utilisation at this time step, computed as if the
        *previous* active configuration is maintained:
        - Cells that were **sleeping** in prev_active carry only their own
          traffic (traffic_loads[i] == own_load[i]).
        - Cells that were **active** in prev_active carry own traffic plus an
          equal share of each sleeping neighbour's load.
        Values may exceed 1.0 under heavy offloading.

        To recover own (base) loads for headroom calculations:
          OFFLOAD_OVERHEAD = 2.0
          own_load[i] = traffic_loads[i]  if prev_active[i] == 0
          own_load[i] = traffic_loads[i] - sum over sleeping neighbours j of
                        (traffic_loads[j] * OFFLOAD_OVERHEAD / active_neighbour_count_of_j)
                                          if prev_active[i] == 1
        Note the OFFLOAD_OVERHEAD factor in the subtraction — without it you will
        over-estimate own load for active cells and under-estimate sleep headroom.
    neighbor_matrix : np.ndarray, shape (N, N)
        Binary adjacency matrix.  neighbor_matrix[i, j] == 1 means cell j
        is a direct neighbour of cell i.
    prev_active : np.ndarray, shape (N,)
        Active/sleep state at the previous time step (1 = active, 0 = sleep).
        All-ones at t=0 (network starts fully active).

    Returns
    -------
    np.ndarray, shape (N,)
        Integer array: 1 = cell stays/becomes active, 0 = cell sleeps.
    """
    pass
```

**Important:** Do not import ``utils`` or ``eval`` — those modules are provided by the
evaluator and are not present in your workspace.  Your ``draft.py`` only needs ``numpy``.

## Switching cost

Every state transition (active → sleep **or** sleep → active) for any cell incurs a
penalty of **SWITCH_COST = 2** equivalent active-cell time steps deducted from the energy
savings.  This models the energy overhead and latency of real base-station sleep-mode
transitions.

The metric is therefore:

```
net_savings_pct = 100 × (sleeping_cell_steps − 2 × total_transitions) / (N × T)
```

A policy that puts 6 cells to sleep for the whole day but toggles each of them twice
loses 2 × 12 = 24 cell-steps to switching costs.

## Evaluation

The policy is tested across **three independent 24-hour traffic scenarios** (different
random seeds → different per-cell load profiles with AR(1)-correlated variation).  For each
scenario:

1. The policy is called for every one of the T = 288 time steps (5-minute intervals).
2. Both constraints are checked at every step; a single violation → FAILURE.
3. Net energy savings = (sleeping cell-steps − 2 × transitions) / (N × T) × 100 %.

The reported metric is the **average net savings (%) across the three scenarios**.

Reference values:
- **0 %** — always active (no savings, no switching cost)
- **~15–22 %** — naive / poorly-tuned implementations
- **~28–32 %** — good temporal policy (near-oracle for this traffic and overhead model)
- **> 33 %** — oracle bound (theoretical maximum with perfect future knowledge, no transition cost)

## Suggested approaches

Use **one** of the following. All of them rely on temporal commitment, not per-step greedy.

1. **Precomputed valid sleep sets + hysteresis streak.** At startup, enumerate all 2^7
   configurations that satisfy the coverage constraint (a small fixed set given the
   hex topology). At each step, check the overload constraint only over this pre-filtered
   list. Track how many consecutive steps each configuration has been feasible. Pick the
   configuration with the most sleeping cells whose feasibility streak is ≥ k (e.g. k=3).
   This prevents rapid switching because a config must be continuously safe for k steps
   before it is adopted.

2. **Circadian schedule with reactive guard.** The traffic follows a 24 h sinusoidal
   pattern, so low-traffic periods are predictable. Identify the low-traffic window from
   the first few steps and sleep aggressively during it (only ~2 transitions per cell per
   day). Outside low-traffic hours fall back to a conservative threshold policy.

3. **Center-biased hysteresis.** Keep cell 0 (centre) active at all times — it neighbours
   all 6 ring cells and acts as a universal offload sink. For each ring cell, maintain a
   persistent sleep/wake state: sleep the cell when its own load is below a low threshold
   (e.g. 0.55) AND active neighbours can absorb its traffic below 0.76; wake it only when
   load rises above a high threshold (e.g. 0.70). The two-threshold hysteresis means the
   cell stays asleep through brief load spikes, making decisions stable across many steps.
   Store per-cell state with `if not hasattr(sleep_policy, 'state'): sleep_policy.state = {}`.
   Note: with OFFLOAD_OVERHEAD = 2.0, each sleeping cell's traffic contributes 2× to its
   active neighbours, so the feasibility window is tighter than it appears — use a generous
   internal margin (≤ 0.76) relative to the hard limit (0.80).

4. **Minimum sleep duration commitment.** Once you decide to sleep a cell, commit to
   keeping it asleep for at least `min_sleep = 6` steps before reconsidering. The
   switching cost makes short sleep bouts actively harmful (a 2-step sleep incurs penalty
   4 for only 2 benefit). A minimum commitment converts a noisy reactive policy into a
   stable one without losing much flexibility.

## CRITICAL: Hysteresis on waking — the key to high scores

Policies that score ~37 % all share the same bug: **they wake sleeping cells immediately
the first time the current configuration becomes infeasible.**  With AR(1)-correlated
traffic there are frequent brief load spikes.  Each spike triggers a wake (paying
transition cost), and the next quiet step triggers sleep again (paying again).  These
round-trips destroy the score.

**The fix: tolerate a few infeasible steps before waking.**

```python
# Track how many consecutive steps the current config has been infeasible
if current_config_is_infeasible:
    sleep_policy.infeasible_streak += 1
else:
    sleep_policy.infeasible_streak = 0

# Only fall back to a less-aggressive config after N consecutive infeasible steps
WAKE_PATIENCE = 4   # ride out up to 4 steps of infeasibility before waking
if sleep_policy.infeasible_streak >= WAKE_PATIENCE:
    # switch to next-less-aggressive feasible config (not all the way to all-active)
    sleep_policy.infeasible_streak = 0
```

But **the overload constraint must never be violated**.  Use a three-zone structure
based on two thresholds — a soft internal limit (0.74) and the hard evaluator limit (0.80):

```python
SOFT_LIMIT = 0.74   # start counting patience above this
HARD_LIMIT = 0.80   # evaluator will FAIL above this — must act immediately
WAKE_PATIENCE = 4   # tolerate up to 4 steps above SOFT_LIMIT before stepping down

current_max_load = max effective load across active cells in current config

if current_max_load > HARD_LIMIT:
    # Cannot stay — evaluator would fail. Step down one level immediately.
    step_down_one_config()
    sleep_policy.infeasible_streak = 0

elif current_max_load > SOFT_LIMIT:
    # Getting uncomfortable but still safe. Increment patience counter.
    sleep_policy.infeasible_streak += 1
    if sleep_policy.infeasible_streak >= WAKE_PATIENCE:
        # Genuine sustained load rise — step down one level.
        step_down_one_config()
        sleep_policy.infeasible_streak = 0
    # else: stay in current config and wait

else:
    # Load is comfortably below soft limit — reset patience counter.
    sleep_policy.infeasible_streak = 0
    # Consider upgrading to more aggressive config if streak is long enough.
    try_upgrade_if_stable(k=5)
```

The key is that `infeasible_streak` is only reset to 0 in the **else** branch (load below
SOFT_LIMIT) and after a step-down, never during the `elif` branch.  A brief spike that
recovers within WAKE_PATIENCE steps costs zero transitions.

Combined with a sleep-upgrade stability requirement (k ≥ 5 feasible steps before
adopting a more aggressive config), this produces stable, long sleep bouts.

## Tips

- Use `prev_active` to avoid unnecessary transitions: if a cell was sleeping last step
  and the load is still low, keep it sleeping rather than waking and re-sleeping it.
- The traffic has ~50-minute autocorrelation, so a decision made now is likely still
  correct 2–3 steps later — stability is rewarded.
- Sleeping the centre cell (index 0) saves one cell but requires all ring cells with
  sleeping neighbours to have another active ring neighbour covering them.
- **Offloading headroom:** before sleeping a cell, check whether its active neighbours
  can absorb its traffic without exceeding 0.8.
- **Use a safety margin:** use 0.76 rather than 0.80 as your internal threshold for
  the sleep-upgrade feasibility check. The evaluator uses exactly 0.80. With
  OFFLOAD_OVERHEAD = 2.0 the effective load can jump sharply when a cell sleeps, so
  the margin matters more than in a 1× model.
- **Array comparisons:** use `.any()` or `.all()` when comparing numpy arrays in boolean
  contexts to avoid `ValueError: truth value of array is ambiguous`.
