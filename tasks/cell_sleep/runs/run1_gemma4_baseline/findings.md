# Run 1 Findings — Baseline (gemma-4-26B-A4B-it, May 2026)

## Setup

| Parameter | Value |
|---|---|
| Model | google/gemma-4-26B-A4B-it (MoE, 26B total / ~4B active params) |
| Inference server | vLLM on DGX Spark GB10 (sm_121, 120 GB unified memory) |
| Generations completed | 5 (gen00–gen05, 10 agents each) |
| Parallel workers | 5 |
| Aggregate throughput | ~64 tok/s (5 concurrent agents, 89.7% prefix cache hit rate) |
| Total candidates | 57 (38 successful, 19 failed/timeout) |

## Scores by generation

| Generation | Best | Mean | n |
|---|---|---|---|
| gen00 | 26.5% | 22.3% | 2 |
| gen01 | 30.5% | 19.8% | 5 |
| gen02 | 36.1% | 33.4% | 4 |
| gen03 | 36.9% | 34.9% | 7 |
| gen04 | 36.9% | 35.7% | 10 |
| gen05 | 36.9% | 35.1% | 7 |

The loop converged at **36.9% net savings** from gen03 onward.

## Metric definition

```
net_savings_pct = 100 × (sleeping_cell_steps − 2 × transitions) / (N × T)
```

N = 7 cells, T = 288 time steps (5-min intervals, 24 h), SWITCH_COST = 2.
Averaged across three traffic scenarios (seeds 42, 123, 456).

A cell asleep for S consecutive steps pays only 2 penalty total (one transition
in, one out), so net gain = S − 2.  For S ≥ 3 the gain is positive; a typical
low-traffic bout of 20–50 steps yields large net gain.  This is why per-step
greedy maximisation fails: from all-active, sleeping k cells immediately costs
2k penalty for k gain, netting −k < 0.

## Why agents converged at ~37%

All high-scoring agents implemented a variant of the **precomputed config +
three-zone hysteresis** approach described in the prompt.  The common failure
mode was a subtle bug in the patience counter:

```python
# Bug: patience reset in WRONG branch
if load > HARD_LIMIT:
    step_down(); patience = 0
elif load > SOFT_LIMIT:
    patience += 1
    if patience >= WAKE_PATIENCE:
        step_down(); patience = 0
    # BUG: no reset on the else branch — patience keeps accumulating
else:
    # should reset here but doesn't
    pass
```

The prompt was updated to include an explicit three-zone pseudocode with the
comment "infeasible_streak is only reset to 0 in the else branch and after a
step-down, never during the elif branch."  Despite this, the 4B active-parameter
model consistently reproduced the bug — it hit a reasoning ceiling on the
structure.

## Oracle bound analysis

The theoretical maximum gross savings (perfect knowledge of all future traffic,
no constraint on transitions) was computed by enumering all 2^7 = 128 possible
cell configurations at every time step:

| Seed | Max avg sleep | Oracle gross | Notes |
|---|---|---|---|
| 42 | 3.05 cells / step | 43.6% | 6 steps with 6 sleeping |
| 123 | 3.35 cells / step | 47.9% | 31 steps with 6 sleeping |
| 456 | 3.12 cells / step | 44.5% | 3 steps with 6 sleeping |
| **Average** | **3.17** | **45.3%** | |

With zero transitions, the theoretical net maximum ≈ 45%.  With realistic
transitions (~ 20/scenario), net maximum ≈ 43–44%.

**The ">65% reference in the prompt is not achievable for this traffic model.**
The mean total system load is 2.1–2.3 PRB units across all 7 cells.  Since no
active cell can exceed 0.80, approximately 2.1/0.80 ≈ 2.6 active cells are
needed on average, leaving at most 4.4 sleeping — 63% gross — before even
counting that offloading concentrates load unevenly.  In practice the bound is
lower (~45%) because load is non-uniform and coverage must be maintained.

The reference values should be revised to:
- **~25–35%** — naive / buggy implementations
- **~37%** — stateless or slightly-hysteretic per-step policies
- **~40–44%** — near-optimal temporal policies for this traffic model

## Hand-crafted near-optimal policy (best_policy.py)

A hand-crafted implementation was developed and reaches **41.0% net** averaged
across the three seeds:

| Seed | Net | Transitions | Gross |
|---|---|---|---|
| 42 | 37.5% | 39 | 41.4% |
| 123 | 43.1% | 42 | 47.3% |
| 456 | 42.5% | 31 | 45.6% |
| **Average** | **41.0%** | **37** | **44.8%** |

This is **90% of the oracle bound** (41.0 / 45.3).

### Policy structure (center-biased per-cell hysteresis)

- Each cell maintains a patience counter (`lo_cnt` / `hi_cnt`).
- Sleep attempt: cell tries to sleep when `lo_cnt ≥ SLEEP_PAT` (own load below
  `SLEEP_OWN` for enough steps). Sleep candidates are sorted by **impact on
  neighbours** (max effective load created on any active neighbour if slept) so
  the safest cells go first.
- Wake attempt: soft wake via `hi_cnt ≥ WAKE_PAT`.
- Hard safety pass: enforces coverage and the 0.80 overload constraint every
  step, waking the sleeping cell with the highest own load (largest offload
  contributor) first.
- All cells (including cell 0) can sleep; no "always-active" constraint.
- Key parameters: SLEEP_OWN = 0.79, WAKE_OWN = 0.79, MAX_NEIGHBOR = 0.78,
  SLEEP_PAT = 1, WAKE_PAT = 6.

### Seeding attempt

The policy was injected into the running leaderboard (as `seed-0000`, metric
41.04%) during gen05.  The entry was subsequently overwritten when the
experiment completed gen05 and rewrote the leaderboard file from scratch.  For
a future run, seeding should be done **between generations** (after the manager
log shows "Generation N complete") or via a mechanism that survives a full
leaderboard rewrite.

## Model realism issue — offloading PRB overhead

The current simulation assumes offloaded traffic from a sleeping cell uses the
same number of PRBs at the neighbouring BS.  In reality, users served from a
neighbour experience higher path loss and worse SINR, requiring lower MCS and
more PRBs for the same data rate.

Realistic PRB overhead factor: **~2×** (range 1.5–3× depending on cell size,
path loss exponent, and user distribution).

With a 2× overhead the effective load formula becomes:

```python
share = own_load[sleeping_cell] * 2.0 / num_active_neighbours
```

Impact on the alternating 3-ring-cells-sleep configuration: the constraint on
cell 0 becomes `x + 2x = 3x ≤ 0.80`, reducing the feasibility threshold from
x ≤ 0.40 to x ≤ 0.267.  This roughly **halves the window during which cells can
sleep**, cutting maximum achievable savings from ~45% to ~20–25%.

This is planned as the next model update (Run 2).

## Infrastructure notes

- vLLM achieved ~6× throughput over Ollama for this multi-agent workload
  (64 tok/s aggregate vs. ~10 tok/s; 89.7% prefix cache hit rate).
- DGX Spark GB10 uses unified memory (120 GB shared CPU/GPU); `nvidia-smi`
  reports "Memory-Usage: Not Supported".
- vLLM must be built from source for GB10 (sm_121) as of May 2026;
  `transformers ≥ 5.8.0` required for gemma4 architecture.
- SSH tunnel with `-o ServerAliveInterval=30` needed for stable long-running
  connections; experiment runs in `tmux` on the Spark to survive disconnects.
- Setup documented in:
  `jjn-vault/research/ai-telco-engineer-setup-guide.md`
  `jjn-vault/research/vllm-vs-ollama-dgx-spark.md`
