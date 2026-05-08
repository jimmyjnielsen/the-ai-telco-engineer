import numpy as np

SLEEP_OWN    = 0.79   # sleep if own load stays below this
WAKE_OWN     = 0.79   # wake if own load rises above this
MAX_NEIGHBOR = 0.78   # safety ceiling on active-neighbour effective load
SLEEP_PAT    = 1      # steps below SLEEP_OWN before sleeping
WAKE_PAT     = 6      # steps above WAKE_OWN before waking


def sleep_policy(traffic_loads: np.ndarray,
                 neighbor_matrix: np.ndarray,
                 prev_active: np.ndarray) -> np.ndarray:
    N = len(traffic_loads)

    # ── Initialise / reset per-scenario state ─────────────────────────────────
    if not hasattr(sleep_policy, '_step') or sleep_policy._step >= 288:
        sleep_policy._step   = 0
        sleep_policy._asleep = np.zeros(N, dtype=bool)
        sleep_policy._lo_cnt = np.zeros(N, dtype=int)
        sleep_policy._hi_cnt = np.zeros(N, dtype=int)

    sleep_policy._step += 1

    # ── Recover own (base) loads ───────────────────────────────────────────────
    own = np.zeros(N)
    for i in range(N):
        if prev_active[i] == 0:
            own[i] = traffic_loads[i]
        else:
            s = 0.0
            for j in range(N):
                if neighbor_matrix[i, j] == 1 and prev_active[j] == 0:
                    na = int(np.sum(prev_active[neighbor_matrix[j] == 1]))
                    if na > 0:
                        s += traffic_loads[j] / na
            own[i] = max(0.0, traffic_loads[i] - s)

    # ── Update patience counters ───────────────────────────────────────────────
    for i in range(N):
        if own[i] < SLEEP_OWN:
            sleep_policy._lo_cnt[i] += 1
            sleep_policy._hi_cnt[i] = 0
        elif own[i] > WAKE_OWN:
            sleep_policy._hi_cnt[i] += 1
            sleep_policy._lo_cnt[i] = 0
        # Middle zone: leave both counters unchanged

    active = np.array([0 if sleep_policy._asleep[i] else 1 for i in range(N)],
                      dtype=int)

    # ── Helpers ────────────────────────────────────────────────────────────────
    def eff_load(j, proposed):
        e = own[j]
        for k in range(N):
            if neighbor_matrix[j, k] == 1 and proposed[k] == 0:
                na = int(np.sum(proposed[neighbor_matrix[k] == 1]))
                if na > 0:
                    e += own[k] / na
        return e

    def has_active_nbr(i, proposed):
        return bool(np.any(proposed[neighbor_matrix[i] == 1]))

    def max_nbr_load_if_slept(i, proposed):
        """Max effective load on i's active neighbours if i is put to sleep."""
        p2 = proposed.copy()
        p2[i] = 0
        return max(
            (eff_load(j, p2) for j in range(N)
             if neighbor_matrix[i, j] == 1 and p2[j] == 1),
            default=0.0
        )

    # ── Try sleeping active cells — lowest neighbour-impact first ─────────────
    sleep_candidates = [
        i for i in range(N)
        if not sleep_policy._asleep[i] and sleep_policy._lo_cnt[i] >= SLEEP_PAT
    ]
    sleep_candidates.sort(key=lambda i: max_nbr_load_if_slept(i, active))

    for i in sleep_candidates:
        proposed = active.copy()
        proposed[i] = 0
        if not has_active_nbr(i, proposed):
            continue
        ok = True
        for j in range(N):
            if proposed[j] == 0 and not has_active_nbr(j, proposed):
                ok = False
                break
        if not ok:
            continue
        for j in range(N):
            if neighbor_matrix[i, j] == 1 and proposed[j] == 1:
                if eff_load(j, proposed) > MAX_NEIGHBOR:
                    ok = False
                    break
        if ok:
            sleep_policy._asleep[i] = True
            active[i] = 0

    # ── Wake sleeping cells whose own load has risen ───────────────────────────
    for i in range(N):
        if sleep_policy._asleep[i] and sleep_policy._hi_cnt[i] >= WAKE_PAT:
            sleep_policy._asleep[i] = False
            active[i] = 1

    # ── Hard safety pass: fix coverage and overload violations ────────────────
    changed = True
    while changed:
        changed = False
        for i in range(N):
            if active[i] == 0 and not has_active_nbr(i, active):
                sleep_policy._asleep[i] = False
                active[i] = 1
                changed = True
        for i in range(N):
            if active[i] == 1 and eff_load(i, active) > 0.80:
                # Wake the sleeping neighbour with the highest own load
                best_j, best_load = -1, -1.0
                for j in range(N):
                    if neighbor_matrix[i, j] == 1 and active[j] == 0:
                        if own[j] > best_load:
                            best_load = own[j]
                            best_j = j
                if best_j >= 0:
                    sleep_policy._asleep[best_j] = False
                    active[best_j] = 1
                    changed = True

    return active
