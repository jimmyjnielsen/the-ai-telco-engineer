### Best approaches (metric >= 2.5)
- Recency-weighted MLE + OLLA + per-MCS bias (gen09-0097) - exp(-(N-i)/30) weighted likelihood on 0.25 dB grid window 50 + OLLA + per-MCS log-odds bias (clip ±1, ≥5 obs) + 1.4*target cap - best score: 3.0766
- Recency-weighted MLE + nudge (gen09-0092) - same as 0097 plus -0.2 dB at 1.8*target nudge over last-20 - best score: 3.0594
- Hybrid MLE+OLLA + per-MCS bias + loosened safety (gen03-0030 / gen03-0035 / gen07-0070 / gen07-0075 / gen08-0082 / gen08-0087) - 0.25 dB MLE window 50 + OLLA + per-MCS log-odds bias (clip ±1, ≥5 obs) in selection AND 1.4*target cap, -0.2 dB at 1.8*target - best score: 3.0527
- Hybrid MLE+OLLA + asymmetric MCS+1 probe (gen03-0033 / gen04-0041 family) - gen02-0026 + p=0.05 MCS+1 probe gated ≥10 obs / NACK≤0.5*target / next<5 - best score: 3.0526
- Cap sweep 1.41*target (gen09-0090 / gen09-0095) - gen03-0033 envelope with hard cap tightened to 1.41*target - best score: 3.0508
- Adaptive bias-clip schedule (gen05-0053 / gen06-0060 family) - per-MCS clip ramped ±1.5 (3 obs) → ±1.0 (15 obs) - best score: 3.0506
- Cap sweep 1.43*target + probe (gen08-0080 / gen08-0085) - 1.43*target hard cap, MCS+1 probe - best score: 3.0500
- Hybrid MLE+OLLA + per-MCS log-odds bias (gen02-0026) - 0.25 dB MLE + OLLA + per-MCS bias, 1.3*target cap - best score: 3.0489
- Per-MCS delta_m supplement (gen09-0091) - gen03-0030 envelope + per-MCS additive shift dm updated ±0.02 clipped [-0.5,+0.5], applied when count≥10 - best score: 3.0480
- Cap sweep ~1.5*target + probe (gen07-0071 / gen07-0076) - cap 1.5*target, -0.175 dB at 1.9*target - best score: 3.0485
- Cap sweep 1.45*target + probe (gen06-0064) - 1.45*target cap, -0.18 dB at 1.85*target, MCS+1 probe - best score: 3.0455
- Annealed probe-probability (gen07-0074 / gen07-0079) - p_up 0.10→0.02, p_down 0.08→0.02 - best score: 3.0434
- Hybrid MLE+OLLA + per-MCS bias at selection only (gen02-0021) - best score: 3.0433
- Raised safety cap 1.6*target (gen04-0040 family) - cap 1.6*target, -0.15 dB at 2.0*target - best score: 3.0432
- SINR MLE + OLLA + relaxed safety (gen02-0020 / gen02-0025) - 1.5*target cap, 1.8*target trigger - best score: 3.0425
- Two-tier asymmetric probe (gen06-0061 / gen06-0066) - + MCS-1 downward probe at NACK>1.5*target - best score: 3.0417
- Ensemble/voting meta-controller (gen08-0089) - median of 3 candidates, switch to min/max on extreme NACK - best score: 3.0396
- Per-MCS delta_m at 1.43*cap (gen09-0096) - delta_m supplement variant with 1.43*target cap and stochastic probe - best score: 3.0387
- Kalman SINR + OLLA + per-MCS bias (gen03-0032 / gen03-0037) - best score: 3.0371
- Cap 1.45*target + adaptive clip + probe (gen06-0069) - best score: 3.0371
- Hybrid MLE+OLLA + EMA per-MCS bias (gen03-0031 / gen03-0036) - best score: 3.0359
- Per-MCS EKF logit-bias (gen04-0048 family) - best score: 3.0355
- Kalman + GH quadrature CVaR (gen04-0042) - best score: 3.0345
- SINR MLE + OLLA + safety cap (gen01-0015) - best score: 3.0327
- SINR MLE + OLLA + early-break (gen01-0010) - best score: 3.0265
- Exponentially-weighted MLE 0.97^age (gen03-0034 / gen03-0039) - best score: 3.0192
- Hybrid MLE+OLLA + wider bias clip (gen04-0044 / gen04-0049) - best score: 3.0179
- SINR MLE + OLLA 0.5 dB grid (gen00-0005) - best score: 3.0105
- Kalman SINR posterior alone (gen02-0027) - best score: 2.9590
- TS+OLLA hybrid w/ Kalman pessimistic cap (gen09-0094) - Kalman+TS seeded by len(history) + OLLA + bias + mu-σ cap at 1.4*target - best score: 2.9540
- Joint Kalman+GH+OLLA (gen07-0073) - best score: 2.9542
- Pure GH CVaR without OLLA (gen05-0054) - best score: 2.5592
- Coarse 1 dB SINR + OLLA + safety margin (gen00-0000) - best score: 2.5913

### Moderate approaches (metric 1.0-2.5)
- Kalman+GH+EKF-bias with broken OLLA loop (gen07-0078) - best score: 1.8380
- Pure OLLA on float MCS + model cap (gen00-0008) - best score: 1.2619
- TS+OLLA hybrid with asymmetric step (gen09-0099) - Kalman+TS+OLLA+bias+pessimistic cap but extra OLLA in cap path destabilized - best score: 1.1339
- Thompson Sampling on Kalman SINR + bias, no OLLA (gen08-0088) - best score: 1.0914

### Implementation failures (score N/A or <1.0, but algorithmically plausible)
- UCB1 MCS bandit (gen09-0093, gen09-0098) - Crude linear SE table and missing/inverted safety cap; retry with real SE table derived from get_bler and 1.4*target safety floor.
- TS on SINR (gen08-0083) - nudge missing in cap.
- Placeholder stubs (gen08-0081 / gen08-0086) - return-0 stub.
- Per-MCS residual delta_m earlier attempts (gen06-0062 / gen06-0067 / gen07-0072 / gen07-0077) - now superseded by working gen09-0091.
- Contextual online logistic regression per-MCS (gen08-0082 / gen08-0087 / gen07-0070 / gen07-0075) - agent falls back to gen03-0030; needs pre-filled snippet.
- Joint Kalman+EKF+GH+OLLA full stack (gen06-0063 / gen06-0068) - compounded optimism.
- GH selector with inverted cap (gen05-0059).
- Beta-Bernoulli bandits (gen02-0023/0024/0028/0029, gen01-0014/0019).
- Particle/adaptive-window MLE (gen01-0011/0016).
- Thompson/posterior-percentile SINR (gen00-0001/0006, gen01-0013/0018).
- Bootstrap LCB SINR (gen00-0004/0009).

### Algorithmic dead ends
- Pure GH CVaR without OLLA (gen05-0054 at 2.56) - residual correction essential.
- TS sampling without OLLA residual (gen08-0088 at 1.09; gen09-0099 at 1.13) - single-sample variance hurts vs deterministic OLLA tracking even with Kalman cap.

### Unexplored territory
- Tune recency-weighted MLE: sweep τ ∈ {15, 20, 40, 60} and window ∈ {30, 75, 100} around gen09-0097's τ=30/window=50 (current best 3.0766).
- Combine recency-weighted MLE (gen09-0097) with MCS+1 probe + 1.41*target cap stack from gen09-0090.
- Add per-MCS delta_m supplement (gen09-0091 mechanism) on top of recency-weighted MLE envelope.
- Two-timescale OLLA: fast delta (step 0.1) for last-10 + slow delta (step 0.02) for full history, combined additively.