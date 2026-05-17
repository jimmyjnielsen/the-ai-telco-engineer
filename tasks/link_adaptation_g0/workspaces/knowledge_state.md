### Best approaches (metric >= 2.5)
- Thompson-flavored stochastic override on 0.40/3.60 (gen09-0093) - gen07-0070 baseline + raw empirical override n_m>=4 with unseeded coin-flip bumping to baseline+2 or m_emp+1 - best score: 3.0645
- Frequency-anchor OLLA 0.40/3.60 + empirical override (gen07-0070/0075) - most-frequent MCS anchor, binary-search nominal SINR, asymmetric 0.40/3.60 delta, bler_2_mcs baseline, override min(m_emp, baseline+2) for n_m>=8 - best score: 3.0640
- Raw-empirical override on 0.40/3.60 winner with m_emp>baseline gating (gen08-0086/0082, gen09-0097) - gen07-0070 base with n_m>=4/8 override applied only when m_emp exceeds baseline - best score: 3.0638
- Gating-only override n_m>=4 on 0.40/3.60 (gen09-0092) - lowered threshold + explicit m_emp>baseline gating, min(m_emp, baseline+2) - best score: 3.0608
- Frequency-anchor OLLA 0.30/2.70 + empirical override (gen06-0060) - same structure at ratio-9 magnitude 0.30/2.70 - best score: 3.0606
- Grid-scan + asymmetric 0.30/2.70 stack (gen07-0071) - SINR grid scan, median-anchor MCS, override at n_m>=8 - best score: 3.0603
- Grid-scan frequency-anchor OLLA 0.25/2.25 + override (gen06-0062) - best score: 3.0573
- Raw-empirical override n_m>=4 on 0.40/3.60 with raw-BLER gating (gen08-0087) - best score: 3.0566
- Wilson-UB-substituted raw-empirical override on 0.40/3.60 (gen09-0096) - intended Wilson UB collapsed to raw k/n at n_m>=5 - best score: 3.0566
- Raw empirical override n_m>=5 on 0.25/2.25 (gen06-0068, gen07-0072) - best score: 3.0568
- Asymmetric 0.45/4.0 fine-tune on gen07-0070 (gen09-0095) - intended 0.43/3.87 implemented as 0.45/4.0 with m_emp>baseline gating - best score: 3.0437
- Frequency-anchor OLLA 0.25/2.25 + empirical override (gen05-0051/0056) - best score: 3.0545
- Asymmetric 0.43/3.87 with median-probe anchor (gen09-0090) - gen07-0070 structure at 0.43/3.87, n_m>=8 gated override - best score: 3.0542
- Position-weighted OLLA 0.25/2.25 (gen06-0061) - best score: 3.0539
- Frequency-anchor OLLA 0.20/1.80 lowered-threshold override (gen08-0081) - best score: 3.0493
- Grid-scan anchor + 0.40/3.60 stack with m_emp>baseline gating (gen08-0083/0088) - best score: 3.0464
- Frequency-anchor OLLA 0.22/1.98 (gen05-0050/0055) - best score: 3.0508
- Wilson-UB single-MCS check on 0.25/2.25 (gen06-0063) - best score: 3.0423
- Raw empirical n_m>=5 on 0.25/2.50 (gen07-0077) - best score: 3.0382
- Wilson-style partial override on 0.30/2.70 with 0.85 delta scale (gen07-0078) - best score: 3.0355
- Frequency-anchor OLLA 0.35/3.15 (gen06-0065) - best score: 3.0352
- Asymmetric OLLA 0.50/4.50 on gen07-0070 (gen08-0080/0085) - best score: 3.0353
- Wilson UB partial override on 0.30/2.70 (gen07-0073) - best score: 3.0286
- Wilson-lower-bound override 0.15/1.4 (gen05-0059) - best score: 3.0310
- Frequency-anchor OLLA 0.20/1.80 + override (gen04-0047) - best score: 3.0290
- Frequency-anchor OLLA dynamic-scaled 0.20/1.80 (gen04-0041) - best score: 3.0268
- Frequency-anchor OLLA 0.15/1.4 + override +1 (gen04-0042) - best score: 3.0241
- Frequency-anchor OLLA 0.18/1.62 (gen04-0040/0045) - best score: 3.0207
- Frequency-anchor OLLA 0.15/1.4 (gen03-0031) - best score: 3.0106
- Frequency-anchor OLLA 0.111/1.0 (gen03-0036) - best score: 3.0010
- Hybrid frequency-anchor OLLA + override +1 (gen03-0034/0039) - best score: 2.9964
- OLLA-lite frequency-anchored binary-search (gen01-0015) - best score: 2.9911
- Correctly-signed windowed ML + OLLA (gen03-0032) - best score: 2.9812
- OLLA-lite fixed median-MCS nominal - best score: 2.9774
- Grid-scan 0.20/2.80 partial (gen07-0076) - best score: 2.9653
- Windowed ML mis-signed + asymmetric OLLA (gen02-0027) - best score: 2.8626
- Bayesian posterior 10th-pct -1.5 dB margin module-level cache (gen08-0089) - vectorized weighted log-likelihood on 0.5 dB grid, 0.98 decay - best score: 2.6149

### Moderate approaches (metric 1.0-2.5)
- Thompson sampling 0.85 threshold on 0.40/3.60 (gen09-0098) - Beta(1+k,1+n-k) per MCS n>=5, 200 samples, P(BLER<=target)>=0.85, cap baseline+2 - best score: 1.8521
- Bayesian posterior without module-level cache (gen07-0079) - best score: 1.5045
- Empirical-anchor + bler_target-scaled OLLA (gen02-0026) - best score: 2.4418
- OLLA bler_target-scaled, fixed -5 dB nominal - best score: 1.2640
- Windowed ML SINR estimator (gen01-0018) - best score: 1.2603

### Implementation failures (score N/A or <1.0, but algorithmically plausible)
- True Wilson UPPER-bound override (gen06-0063, gen07-0073/0078, gen08-0082, gen09-0091/0096) - agents persistently substitute raw k/n or Laplace+noise; explicit math.sqrt z-score formula needed; gen09-0091 also had syntax error.
- Aggressive Bayesian posterior 15th-pct/-1.0 dB (gen09-0094/0099) - both runs introduced indentation/dead-code bugs preventing execution; vectorized core was correct, just needs clean rewrite.
- Vectorized Bayesian posterior 5th-pct/-1.0 dB (gen08-0084) - scored -inf; quantile too optimistic.
- Per-MCS Wilson UCB direct bandit (gen02-0024/0029) - agents substitute anchor+OLLA.
- Hybrid ML+OLLA two-stage (gen01-0014/0016/0019) - ML stage replaced with placeholder.
- Seeded reproducible Thompson sampling - gen09-0093 used unseeded random and won; properly seeded variant at threshold 0.80 untested.

### Algorithmic dead ends (fundamentally unsuitable for this task)
- Pushing asymmetric ratio-9 magnitude beyond 0.40 - 0.45/4.0 (3.0437) and 0.50/4.50 (3.0353) both regress; peak is at 0.40/3.60.
- Thompson sampling with high probability threshold (>=0.85) - gen09-0098 dropped to 1.8521; threshold too strict starves exploration.

### Unexplored territory
- Stochastic perturbation hypothesis: gen09-0093's unseeded coin-flip bumping (baseline+2 or m_emp+1) scored highest at 3.0645; deliberately test seeded version with tunable bump probability (0.3, 0.5, 0.7) to confirm signal vs. noise.
- Clean Bayesian posterior retry at 15th-pct/-1.0 dB with strict indentation review, plus intermediate 12th-pct/-1.2 dB sweep.
- Properly seeded Thompson sampling at threshold 0.70-0.80 with cap baseline+2.
- Explicit Wilson UB with inline math.sqrt formula in a single tight loop, no helper functions, to defeat agent substitution.