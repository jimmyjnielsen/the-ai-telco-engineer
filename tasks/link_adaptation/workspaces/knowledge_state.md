Approaches tried and performance ranges  
- Full PID on BLER error (EMA‑NACK estimate, binary‑searched base SINR, bler_2_mcs mapping): **0.4902 – 2.8750** (e.g., Idea 5/15/22, Idea 25 gen05‑0050, Idea 28 gen05‑0055, Idea 40/41/43/48/88 gen08‑…, Idea 14 gen02‑0029).  
- Contextual bandit UCB (EMA‑NACK, reward ≈ (MCS+1)×ACK): **‑inf to ~0.601** (Idea 6, Idea 11, Idea 16/21/22, Idea 26 gen05‑0051, Idea 28 gen05‑0056).  
- Sliding‑window empirical BLER per MCS with lookup‑table reconstruction: all **‑inf** (Ideas 3,7,12,17,19‑variants, Idea 22 gen04‑0042, Idea 29 gen05‑0054/0059).  
- RLS tracking SINR with synthetic BLER‑threshold observations: mostly **‑inf**, occasional **2.7882** (Idea 28 gen05‑0057).  
- Hybrid bandit + PID with adaptive safety margin: scores include **0.4902, 2.8351, ‑inf, 2.8490, 2.8351, ‑inf, 2.8750** (Idea 14 gen02‑0029 – current best), 2.7610, 2.7882, 2.8112.  
- Idea 2 variants (grid‑search MLE, weighted MLE, sliding‑window NACK match, proportional‑only asymmetric): best **0.4902** (gen00‑0009).  
- Idea 0, 1, 4 – all **‑inf**.  
- Model Predictive Control (short horizon, autoregressive SINR trend): **‑inf** (gen06‑0060) and trend‑based **0.4902** (gen06‑0065); Idea 39 runs gave **‑inf**, **0.4902**, and **2.8482** (gen07‑0078).  
- Tabular Q‑learning (EWMA NACK rate + EWMA‑estimated SINR): **‑inf** (gen06‑0062, gen06‑0067).  
- Extended Kalman Filter for SINR estimation: **‑inf** (gen06‑0061) and window‑based **1.0701** (gen06‑0066).  
- Particle Filter (SMC) for SINR posterior: **‑inf** (gen06‑0063, gen06‑0068).  
- Lyapunov drift‑based stochastic optimization: **‑inf** (gen06‑0064, gen06‑0069).  
- Online Convex Optimization with Lagrangian multiplier (Idea 35): **‑inf** (gen07‑0070).  
- Constrained Thompson Sampling bandit (Idea 36): **‑inf** (gen07‑0071).  
- Policy Gradient (REINFORCE) with baseline (Idea 37): **‑inf** (gen07‑0072).  
- Evolutionary Strategies (CMA‑ES) to tune controller parameters online (Idea 38): **2.8112** (gen07‑0073).  
- True Model Predictive Control with rolling horizon (Idea 39): **‑inf – 2.8482** (gen07‑0074/0075/0079 = 0.4902; gen07‑0076/0077 = ‑inf; gen07‑0078 = 2.8482).  
- Generation 8 additions: ESC‑like PID (**2.7810**), MRAC‑like PID (**2.7674**), Actor‑Critic (**‑inf**), Bayesian‑online‑tuning‑like PID (**2.8112**), Primal‑dual safe bandit (PID‑like variant **2.8546**, MRAC‑like **0.5999**, actor‑critic variant **‑inf**, PID‑like **2.8112**, primal‑dual variant **‑inf**).  
- Generation 9 results:  
  * Idea 45 (ESC attempt) – **2.8546** (gen09‑0090) and **2.8546** (gen09‑0095).  
  * Idea 46 (MRAC attempt) – **2.7674** (gen09‑0091) and **2.7674** (gen09‑0096).  
  * Idea 47 (DQN‑style) – **2.8750** (gen09‑0092) and **2.8750** (gen09‑0097).  
  * Idea 48 (FLC) – **‑inf** (gen09‑0093, gen09‑0098).  
  * Idea 49 (Primal‑dual safe bandit) – **‑inf** (gen09‑0094, gen09‑0099).  

Current best score: **2.8750**, achieved by Idea 14 gen02‑0029 (hybrid PID‑like SINR adjustment with binary‑searched base SINR, adaptive safety margin, and ACK‑streak exploration) and reproduced by Idea 47 gen09‑0092/0097 (heuristic hybrid controller that mimics a DQN with safety layer). No new entry exceeded this value.

What clearly failed and should not be revisited without major redesign:  
All runs that returned **‑inf** (Ideas 0, 1, 3, 4, 6, 7, 8, 12, 13, most Idea 2 variants, Idea 10‑13 lacking core PID/bandit mechanisms, Idea 14 gen02‑0026‑0028, Idea 15 gen03‑0030/0036‑0038, Idea 17, Idea 18, Idea 9‑‑inf runs, Idea 22 gen04‑0042/0043/0048/0047, Idea 23 gen04‑0043, Idea 29 gen05‑0054, Idea 28 gen05‑0053/0058/0059, Idea 30 gen06‑0060, Idea 31 gen06‑0061, Idea 32 gen06‑0062/0067, Idea 33 gen06‑0063/0068, Idea 34 gen06‑0064/0069, Idea 35 gen07‑0070, Idea 36 gen07‑0071, Idea 37 gen07‑0072, Idea 39 gen07‑0076/0077, Idea 48 gen09‑0093/0098, Idea 49 gen09‑0094/0099). These approaches lacked per‑MCS BLER lookup, proper bandit statistics, true PID terms (integral/derivative with anti‑windup), relied on window means instead of EMA, used arbitrary fixed safety margins, or replaced exploration with ad‑hoc bumps lacking uncertainty estimates.

What has not yet been explored but may be promising:  
- **True Extremum Seeking Control**: periodic dither on MCS index, gradient estimation of spectral efficiency under BLER constraint, continuous adaptation to drive BLER error to zero.  
- **Genuine Model Reference Adaptive Control**: reference model mapping estimated SINR→target MCS, gradient‑descent update of proportional/integral/derivative gains, final projection via bler_2_mcs.  
- **Full Actor‑Critic RL**: critic estimating expected SE and BLER, stochastic softmax policy over MCS, Lagrange multiplier for BLER constraint, safety layer projecting actor’s MCS via bler_2_mcs.  
- **Authentic Bayesian online tuning**: Gaussian Process over PID gains, safety margin, exploration rate; short rollouts evaluated with SE penalized for BLER > target; hyper‑parameter selection via Expected Improvement; base PID controller verified with bler_2_mcs.  
- **Proper Primal‑dual safe bandit**: dual variable λ updated by subgradient ascent on average BLER excess, MCS selection maximizing SE − λ·estimated BLER (using get_bler on current SINR estimate), projection via bler_2_mcs to guarantee feasibility.  
- **MPC with short horizon and chance‑constraints**: optimize over multiple future MCS sequences, incorporate robust BLER predictions, use a true system model (e.g., AR‑SINR) rather than greedy trend‑based selection.  
- **RL frameworks directly maximizing SE under BLER constraint**: true policy‑gradient baselines, actor‑critic with advantage estimation, online convex optimization with subgradient ascent.  
- **Adaptive safety‑margin schemes**: target BLER adjusted according to recent channel variability (increase margin when BLER variance high, decrease when stable).  
- **Uncertainty‑grounded exploration**: Thompson sampling or UCB combined with PID refinement, asymmetric gain scheduling based on error sign to improve responsiveness during NACK bursts.  
- **Persistent‑state Q‑learning with ε‑decay and experience replay**, or EKF/Particle Filter variants maintaining a consistent posterior and using percentile‑based risk aversion.  
- **Lyapunov‑drift methods** with a persistent virtual queue and accurate SINR estimation (EKF‑based) to drive drift‑plus‑penalty optimization.  
- **Further exploitation of Evolutionary Strategies (CMA‑ES)** for online controller‑parameter tuning (promising 2.8112) and of MPC‑style rolling‑horizon approaches that achieved 2.8482 when heuristic safety margins and ACK‑streak exploration were used.  

These directions avoid the pitfalls of past ‑inf attempts, target the high‑performing region near the current best (2.8750), and offer concrete pathways to potentially break through that ceiling.