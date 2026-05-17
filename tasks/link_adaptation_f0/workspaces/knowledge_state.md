### Best approaches (metric >= 2.5)

- **Per-alpha median voting MLE (gen08-0081, gen08-0086)** - Compute MLE SINR independently for each alpha in {0.80, 0.85, 0.95} with exponential decay, take median of three estimates; margins 1.5/0.3/1.5/0.45 dB for all-NACK/all-ACK/over-target/normal - best score: **3.0147**

- **Adaptive-alpha MLE with all-NACK/all-ACK guards (gen04-0042, gen04-0047, gen07-0070, gen07-0075)** - MLE SINR on 101-point grid with alpha from {0.80,0.85,0.95} based on BLER trend, plus explicit 2.0 dB margin for all-NACK and 0.3 dB for all-ACK edge cases, fixed empty-history fallback - best score: **3.0135**

- **Adaptive-alpha MLE with dynamic quantile margin (gen06-0060, gen06-0065)** - Same gen04-0042 MLE core with alpha from {0.80,0.85,0.95}, reduces normal margin from 0.5 dB to 0.3 dB when history>=30 and recent 30-sample BLER < 0.5*bler_target - best score: **3.0107**

- **Adaptive-alpha MLE with variable margin (gen03-0032)** - MLE SINR on 101-point grid with alpha selected from {0.80,0.85,0.95} based on BLER difference between two 10-sample windows, applies 1.5 dB margin when current BLER exceeds target else 0.5 dB - best score: **3.0102**

- **Asymmetric margin variant 0.45/0.22 dB (gen08-0082, gen08-0087)** - Gen04-0042 core with normal margin 0.45 dB and all-ACK margin 0.22 dB, all-NACK 1.5 dB and over-target 1.5 dB unchanged - best score: **3.0072**

- **Adaptive-alpha MLE with two-tier normal margin at 15 samples (gen07-0073, gen07-0078)** - Gen04-0042 core with 0.35 dB normal margin when history>=15 and recent BLER < bler_target, else 0.5 dB; all-NACK 2.0 dB, all-ACK 0.3 dB, over-target 1.5 dB - best score: **3.0067**

- **Three-tier normal margin MLE (gen08-0080, gen08-0085)** - Gen04-0042 core with 0.5/0.38/0.28 dB margins for history<15/>=15+BLER<target/>=30+BLER<0.5*target tiers; all-NACK 1.5 dB, all-ACK 0.3 dB, over-target 1.5 dB - best score: **3.0030**

- **Adaptive-alpha MLE with reduced normal margin 0.4 dB (gen07-0071, gen07-0076)** - Gen04-0042 core with normal margin reduced from 0.5 to 0.4 dB, all other margins unchanged - best score: **3.0047**

- **History-length-adaptive margin MLE with extra BLER guard (gen04-0049)** - MLE SINR on 101-point grid with α=0.85, uses 1.5/1.0/0.7/0.4 dB margins based on history length tiers, plus extra +1.0 dB when current BLER exceeds target - best score: **2.9937**

- **MLE SINR estimation with exponential decay (101-point grid, -0.5 dB margin)** - Scans 101 SINR candidates from -10 to 40 dB, computes weighted log-likelihoods with exponential decay (α=0.85), applies -0.5 dB safety margin - best score: **2.9840**

- **Two-stage MLE + empirical BLER correction with extra margin** - MLE SINR on 51-point grid with α=0.85 decay, adjusts SINR by ±0.5 dB based on recent 20-transmission empirical BLER thresholds, plus ~0.8 dB safety margin - best score: **2.9524**

- **MLE SINR estimation with exponential decay (51-point grid, -1.0 dB margin)** - MLE over 51 SINR candidates with exponential decay (α=0.85) and 1.0 dB safety margin - best score: **2.9511**

- **MLE SINR with adaptive safety margin (51-point grid)** - MLE SINR on 51-point grid with α=0.85 decay, empirical BLER-driven adaptive margin (0.3/0.8/1.5 dB) - best score: **2.9464**

- **Sliding-window MLE with weighted window averaging (6.5 dB margin)** - Three history windows combined with weights 0.6/0.3/0.1, unintended 6.5 dB safety margin - best score: **2.7844**

- **MLE SINR estimation with exponential decay (101-point grid, -0.8 dB margin)** - 101-point MLE with α=0.85 and 0.8 dB safety margin - best score: **2.5726**

- **History-length-adaptive margin MLE (gen04-0044, inflated margins)** - MLE on 101-point grid with α=0.85 and 2.5/2.0/1.5/1.0 dB margins for history tiers - best score: **2.5058**

### Moderate approaches (metric 1.0-2.5)
*(none observed)*

### Implementation failures (score N/A or <1.0, but algorithmically plausible)

- **Per-alpha median voting with two-tier/three-tier margin variants (gen09-0090, gen09-0092, gen09-0095, gen09-0097)** - All crash with metric=-inf; likely numerical overflow in log-likelihood accumulation or edge case in margin branching logic; retry with explicit np.isfinite guards and simplified margin logic.

- **Per-alpha median voting with reduced margins 0.38/0.22 dB (gen09-0091, gen09-0096)** - Crashes with metric=-inf despite close alignment to working gen08-0081; likely subtle indexing or dtype issue introduced during margin refactoring; retry copying gen08-0081 exactly and only changing margin constants.

- **Alpha-ensemble weighted average MLE (gen09-0093, gen09-0098)** - Crashes with metric=-inf; weighted average of SINR point estimates across alphas may introduce NaN when all log-likelihoods are -inf for some alpha; retry with fallback to equal weights if any per-alpha MLE fails.

- **Per-alpha median voting with confidence-based margin reduction (gen09-0094, gen09-0099)** - Crashes with metric=-inf; range computation over three SINR estimates may fail if any estimate is NaN/inf; retry with explicit isfinite checks before range calculation.

- **Direct MCS binary search via per-MCS empirical BLER (gen08-0083, gen08-0088)** - Crashes (-inf); sparse per-MCS history makes interpolation unstable; retry with global exponential-weighted BLER mapped through get_bler lookup table.

- **Thompson Sampling / Bayesian bandit MCS selector (gen08-0084, gen08-0089)** - Crashes (-inf); likely MCS index out of range or API mismatch; retry ensuring MCS indices stay within valid range.

- **Stateless OLLA-corrected MLE (gen07-0072, gen07-0077)** - Crashes with metric=-inf; likely numerical issue in OLLA offset loop; retry with explicit bounds checking.

- **Bayesian Gaussian MAP SINR estimator (gen06-0063, gen06-0068)** - Numpy array shape mismatch; retry with explicit scalar operations.

### Algorithmic dead ends (fundamentally unsuitable for this task)
*(none identified)*

### Unexplored territory

1. **Simplified retry of per-alpha median voting with reduced margins** - Copy gen08-0081 code exactly, change only the margin constants (normal=0.38, all-ACK=0.22), avoiding any structural refactoring that may have introduced crashes in gen09.

2. **Per-alpha median voting with soft BLER-weighted margin interpolation** - Instead of discrete margin tiers, interpolate margin linearly between 0.45 dB (BLER=bler_target) and 0.25 dB (BLER=0) based on recent BLER ratio, avoiding branching logic that causes crashes.

3. **Weighted average of MLE and empirical BLER-implied SINR** - Compute MLE SINR estimate and separately invert the exponentially weighted empirical BLER to an implied SINR via get_bler lookup, then blend 70/30; may reduce estimation variance in steady state.

4. **Dual-alpha MLE (drop α=0.95, use only 0.80 and 0.85, take minimum)** - Taking the more conservative of two estimates may provide robustness without the instability introduced by including the high-recency α=0.95 estimate.