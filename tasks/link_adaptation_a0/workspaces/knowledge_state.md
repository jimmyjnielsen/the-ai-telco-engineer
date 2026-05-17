## Updated Knowledge State

### Summary of Explored Approaches
The experiment optimizes MCS selection by balancing SINR estimation with dynamic feedback mechanisms to handle channel volatility.

* **Feedback Control (Quantized & Windowed):**
    * **Quantized Step-Size Feedback:** The most successful paradigm. Using discrete, non-linear MCS drops (e.g., steps of 1, 2, or 4) based on the ratio of current BLER to target BLER is highly effective (metric 2.98).
    * **Multi-Window Control:** Using a short-term window (e.g., size 4) for aggressive quantized drops and a long-term window (e.g., size 20) for conservative increases provides a strong balance of responsiveness and stability (metric 2.88–2.94).
    * **Dual-Threshold Hysteresis:** Implementing a "dead-zone" between a Safety Threshold (to drop MCS) and a Growth Threshold (to increase MCS) effectively prevents oscillations (metric 2.90–2.94).
    * **Volatility-Adjusted Quantized Control:** Scaling the sensitivity of the controller or the magnitude of the drops based on recent MCS/NACK volatility shows moderate success (metric 2.87–2.92).
    * **Trend-Aware Control:** Using the first derivative of windowed BLER to preemptively drop MCS shows moderate success (metric 2.85–2.89).

* **SINR Estimation & Mapping:**
    * **Success-Weighted Bisection:** A robust foundation for estimating "nominal" SINR.
    * **Hybrid DC/AC-Bisection:** Combines Bisection with volatility-based margins (metric 2.76–2.86).
    * **Dynamic SINR Margin:** Scaling the SINR margin based on NACK rates or MCS volatility shows moderate success (metric 2.28).
    * **Failed/Unstable Estimators:** Multi-scale windowing, Dual-Track SINR, Probabilistic/Markov models, and pure Statistical/MLE methods have largely failed (-inf to 0.50).

* **Heuristic & Discrete Approaches:**
    * **Gradient/Bandit/RL:** Treating MCS as a continuous parameter or using RL logic has failed (metric 0.49–0.79).

### Current Best Performance
* **Score:** 2.9893 (gen18-0180)
* **Strategy:** **Quantized Feedback Controller** using a sliding window for BLER estimation and discrete, non-linear step-size drops based on the ratio of current BLER to target BLER.

### Failed/Ineffective Approaches
* **Complex Signal/State Analysis:** Spectral analysis, autocorrelation, and Markov models (consistently result in -inf).
* **Continuous/Gradient-Based Updates:** Treating the discrete MCS index as a continuous parameter for optimization.
* **Non-linear Log-Ratio Scaling:** Attempting to use a continuous log-ratio for MCS scaling (gen18-0185) failed; discrete jumps are superior.
* **Improper Trend Implementation:** Using fixed trend thresholds without considering the direction of change (gen19-0196) can lead to instability (-inf).

### Promising Directions
* **Integrated Multi-Window Hysteresis:** Combining the Multi-Window approach (short-term for drops, long-term for increases) with Dual-Threshold Hysteresis to create a highly stable, non-oscillatory controller.
* **Hybrid Volatility-Trend Control:** Merging the responsiveness of trend-based preemptive drops with the stability of volatility-adjusted quantized steps.
* **Refined Quantized Mapping:** Further tuning the specific mapping of BLER/Target ratios to discrete MCS jumps to maximize recovery speed without overshooting.