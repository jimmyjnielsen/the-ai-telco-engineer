## Current knowledge state

### Summary of Explored Approaches
The optimization has converged on a **Multi-Scale Dual-Loop Control** architecture. The most successful strategies use a fast-reacting inner loop for SINR estimation and a slow-reacting outer loop for BLER regulation, typically adjusting a "safety margin" (dB offset) rather than the MCS index directly.

* **Multi-Scale Trend-Based PI Control (High Performance, 2.90–2.96):** The most robust approach. It uses a PI-style controller where the safety margin is adjusted based on error signals derived from the difference between short-term and long-term BLER windows (residuals).
* **Hybrid Adaptive Window PI (High Performance, 2.93–2.95):** An evolution of the trend-based approach that dynamically adjusts EWMA $\alpha$ parameters based on NACK volatility. High volatility triggers longer windows (smaller $\alpha$) for stability; low volatility triggers shorter windows (larger $\alpha$) for responsiveness.
* **Threshold-Triggered Recovery (High Performance, 2.90–2.94):** Uses a standard PI controller for normal operation but switches to a "Safe Mode" (large fixed margin + conservative SINR estimation) when short-term BLER exceeds a critical threshold (e.g., 20%).
* **Non-linear Error-Residual PI (High Performance, 2.90–2.92):** Replaces linear PI adjustments with non-linear mappings (e.g., exponential) to apply aggressive margin increases when BLER approaches the limit.
* **Momentum & Acceleration-Aware PI (Moderate Performance, 2.44–2.88):** Incorporates first and second derivatives of the BLER residual. Higher-order terms have struggled to outperform standard PI or non-linear PI.
* **Predictive/Volatility-Aware Margins (Moderate Performance, 2.77–2.85):** Scaling margins using SINR standard deviation or volatility.
* **Optimized SINR Estimation (Moderate Performance, 2.50–2.92):** Using weighted binary searches or EWMA-weighted SINR estimates provides a cleaner input for the PI controller.
* **Probabilistic/Bayesian Approaches (Failure, <1.0):** Attempts to maintain a belief distribution (Gaussian, Grid-based, or MLE) of the SINR to calculate a confidence-interval-based margin ($\mu - k\sigma$) have failed significantly due to the extreme noise in Bernoulli (ACK/NACK) trials.

### Current Best Result
* **Score:** 2.9593 (gen15-0155)
* **Method:** **Multi-Scale Trend-Based PI Control**: Uses a PI-inspired controller where the safety margin is adjusted based on the error signal derived from the difference between a short-term and long-term BLER window.

### Failed Approaches & Lessons Learned
* **Probabilistic/Bayesian/MLE Inference:** Maintaining formal posterior distributions, grid-based MLE, or using SGD/Gradient Ascent to optimize SINR likelihood is highly unstable. The noise in ACK/NACK feedback leads to catastrophic errors or convergence to -inf.
* **Direct Volatility-Based Gain Scaling:** Scaling PI gains directly by SINR standard deviation is unreliable.
* **Frequency-Domain/Margin Smoothing:** Applying low-pass filters directly to the margin or using log-space smoothing has resulted in convergence failure.

### Promising Directions
* **Refined Non-linear Mapping:** Further tuning the exponential/sigmoid response curves in the Non-linear Error-Residual PI to find the optimal "aggression" threshold.
* **Advanced EWMA Tuning:** Optimizing the $\alpha$ parameters for the short-term and long-term EWMA windows to maximize the signal-to-noise ratio of the BLER residual.
* **Integrated SINR-Margin Estimation:** Exploring if the SINR estimation and the margin adjustment can be more tightly coupled, perhaps by treating the margin as a dynamic parameter within the SINR search itself.