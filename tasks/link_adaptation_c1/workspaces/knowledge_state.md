**Tried approaches and observed performance ranges**  
- **EMA‑based BLER estimate (Idea 0)** – 0.60–1.08  
- **Kalman‑filter SINR tracker (Idea 1)** – heuristic 2.25 (gen00‑0006); other variants −∞  
- **PLL‑like PID controller (Idea 3)** – PD‑only 0.98; PID + integral 0.98–1.12; PID‑like 1.14–1.40 (gen04‑…/gen06‑…) → ≈ 0.98–1.40  
- **UCB multi‑armed bandit (Idea 2)** – all −∞  
- **Online contextual logistic regression (Idea 4)** – all −∞  
- **Thompson sampling / Bayesian bandit (Idea [7])** – 1.15–1.81 (gen01‑… gen06‑…)  
- **Full/EKF Kalman filter (Idea [5])** – all −∞ (gen04‑0045, gen05‑0050/0055/0059, gen06‑0060/0065)  
- **Adaptive‑window EMA (Idea [9])** – 0.97–2.04 (gen01‑… gen03‑…)  
- **Contextual bandit with linear SGD models (Idea [8])** – all −∞ (gen04‑… gen06‑…)  
- **Particle filter for non‑Gaussian SINR tracking (Idea [14])** – −∞  
- **EKF/UKF with Bernoulli measurement (Idea [15])** – −∞  
- **Constrained Contextual Bandit with Lagrangian relaxation (Idea [23])** – −∞  
- **Fuzzy Logic Controller (Idea [21])** – 1.14 (gen04‑0041)  
- **Reinforcement Learning (Q‑learning) with linear FA (Idea [22])** – −∞  
- **Model Predictive Control for MCS selection (Idea [20])** – 2.60–2.68 (gen04‑0040, gen06‑0064, gen06‑0069)  
- **Idea [26] PID controller (instantaneous BLER estimate)** – 1.14 (gen05‑0051)  
- **Idea [27] Thompson Sampling with sliding‑window Beta priors & Lyapunov margin** – 1.78 (gen05‑0052)  
- **Idea [28] Contextual bandit with per‑arm logistic regression (SGD)** – −∞  
- **Idea [29] MPC scheme (AR‑based SINR prediction)** – 2.60–2.68 (gen05‑0054, gen06‑0064, gen06‑0069)  
- **Idea [30] PID‑like with proper safe projection** – 0.98–1.40 (gen05‑0056, gen06‑0061, gen06‑0066)  
- **Idea [31] Thompson Sampling with Lyapunov‑inspired safety margin** – 1.15–1.81 (gen05‑0057, gen06‑0062/0063/0067)  
- **Idea [32] Contextual bandit with logistic regression (bias, EMA‑NACK, MCS index)** – −∞  
- **Idea [33] Per‑arm logistic regression contextual bandit** – 0.49 (gen06‑0063) – clear failure  
- **Idea [34] True MPC scheme** – 2.63–2.68 (gen06‑0064, gen06‑0069); deviations ≤1.55 or −∞  
- **Idea [35] True MPC (attempt)** – −∞ (gen07‑0070)  
- **Idea [36] Full EKF/UKF with exact Bernoulli likelihood** – −∞ (gen07‑0071, gen07‑0076)  
- **Idea [37] Adaptive‑window EMA estimator (volatility‑driven α)** – 2.4204 (gen07‑0072), 2.5950 (gen07‑0077) → ≈ 2.42–2.60  
- **Idea [38] Thompson Sampling with sliding‑window Beta priors + LS fit + safety margin** – 1.5724 (gen07‑0073), 1.5608 (gen07‑0078) → ≈ 1.56–1.57  
- **Idea [39] Hybrid PID‑MPC** – 2.6350 (gen07‑0074), 2.6843 (gen07‑0079) → ≈ 2.63–2.68  
- **Idea [40] Full EKF/UKF with exact Bernoulli likelihood (auto‑diff)** – −∞ (gen08‑0080)  
- **Idea [41] True MPC (enumerate 3‑5 step MCS sequences)** – 2.6241 (gen08‑0081, gen08‑0086)  
- **Idea [42] Refine adaptive‑window EMA (volatility‑driven α, grid‑search BLER→SINR, safety margin)** – **2.7411** (gen08‑0082), 2.6874 (gen08‑0087) → ≈ 2.69–2.74  
- **Idea [43] Thompson Sampling with sliding‑window Beta priors + contextual features** – 1.5480 (gen08‑0083)  
- **Idea [44] Hybrid PID‑MPC (PID proposal + 5‑step MPC safety check)** – 2.6843 (gen08‑0084), 2.6843 (gen08‑0089)  
- **Idea [45] Recursive Gaussian approx EKF (finite‑diff)** – −∞ (gen08‑0085)  
- **Idea [46] Thompson Sampling sliding‑window Beta priors + LS fit + Lyapunov margin** – 1.5515 (gen08‑0088)  
- **Generation 9 results**  
  - Idea [45] (refined adaptive‑window EMA, no MPC) – metric 2.7411 (gen09‑0090)  
  - Idea [46] (TS with contextual features, LS fit, Lyapunov margin) – 1.5478 (gen09‑0091)  
  - Idea [48] (Hybrid PID‑MPC, single‑step AR prediction) – 2.6843 (gen09‑0093)  
  - Idea [47] (True MPC, single‑step prediction) – 2.6386 (gen09‑0092)  
  - Idea [49] (Particle filter, 800 particles) – −∞ (gen09‑0094)  
  - Idea [45] (adaptive‑window EMA + AR trend, single‑step MPC) – 2.6479 (gen09‑0095)  
  - Idea [46] (TS sliding‑window, LS fit, Lyapunov) – 1.5703 (gen09‑0096)  
  - Idea [48] (Hybrid PID‑MPC, linear trend) – 2.6843 (gen09‑0098)  
  - Idea [47] (Kalman + AR trend, single MCS) – 2.6404 (gen09‑0097)  
  - Idea [49] (Particle filter, 100 particles) – −∞ (gen09‑0099)  

**Current best**  
- Score **2.7411** from **gen08‑0082** (Idea [42] Refined adaptive‑window EMA) and reproduced in gen09‑0090 (Idea [45] without the MPC step). The method adapts the EMA smoothing factor α to recent NACK‑rate variance, inverts `get_bler` via grid search to obtain instantaneous SINR, applies a safety margin, and selects the highest safe MCS via `bler_2_mcs`.  

**What clearly failed and should be deprioritized**  
- All −∞ outcomes: Ideas 2, 4, 5, 8, 14, 15, 22, 23, 28, 32, 33, 35, 36, 40, 45 (recursive Gaussian EKF), plus any exact‑Bernoulli EKF/UKF attempts without auto‑diff.  
- Low‑performing plateau methods: PID‑only/PD‑only controllers (≈ 0.98–1.40), fuzzy‑logic controller (1.14), Thompson‑sampling variants that maximise an expected‑throughput proxy instead of sampling, and approaches that omit the arm‑selection step or use insufficient feature sets.  
- Approximate EKF/UKF attempts using finite‑difference gradients or limited histories (all −∞).  
- Pure UCB bandit formulations and direct BLER‑as‑probability logistic regression.  

**Promising unexplored directions**  
- **True Model Predictive Control** that enumerates multiple MCS sequences over a 3‑5 step horizon, predicts SINR with a Kalman/AR model, computes expected spectral efficiency and BLER for each candidate sequence (via `get_bler` and `bler_2_mcs`), and selects the first MCS of the optimal sequence.  
- **Hybrid PID‑MPC extensions**: use PID to generate a candidate MCS adjustment, then run a slightly longer‑horizon MPC safety check (e.g., 5‑step) that evaluates multiple MCS options; accept the PID proposal only if it passes the safety test, otherwise use the MPC‑selected safe MCS.  
- **Refined adaptive‑window EMA**: combine volatility‑driven α with variable window length or exponential weighting, and directly invert `get_bler` to obtain instantaneous SINR for safe MCS selection (already showing >2.74).  
- **Thompson Sampling with sliding‑window Beta priors + Lyapunov safety margin**: systematic tuning of window size, prior strength, and safety‑margin coefficient; optional fallback to the highest safe MCS derived from current SINR estimate.  
- **Contextual bandits with per‑arm logistic regression or shallow neural nets**, trained online on features such as recent NACK rate, EMA‑based SINR, MCS trend, and channel‑quality indicators; compute expected SE = MCS × P(ACK) and select the arm maximizing SE under the BLER constraint (checked with `bler_2_mcs`).  
- **Improved particle filter**: increase particle count (≥ 500), employ a proposal that incorporates the latest ACK/NACK, weight by exact Bernoulli likelihood, estimate SINR (weighted mean or MAP), and map to MCS via `bler_2_mcs` while enforcing the BLER bound.  
- **Recurrent neural network (RNN) or Temporal Convolution Network** for short‑term SINR prediction, feeding the predicted distribution into a MPC or Thompson‑sampling decision layer.  

These avenues build on the strongest elements observed—adaptive EMA estimation, Kalman‑like state prediction, integral/predictive control, Bayesian exploration, and horizon‑based optimization—while addressing the gaps that have kept performance below the current best.