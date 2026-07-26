# Methodology & Technical Architecture

The **Macro Intelligence Platform** traces business cycle regimes and projects 3-to-9 month forward trajectories using a 2D state-space representation and an out-of-sample validated two-signal consensus engine.

---

## 1. The 2D State-Space Framework

Economic leading indicators (such as the OECD Composite Leading Indicator) are mapped into a two-dimensional state space:

1. **$X$-Axis (Economic Health)**:
   $$X = 100 + \frac{I_t - \mu_{36}}{\sigma_{36}}$$
   Measures the normalized level of economic output relative to its 36-month rolling trend. Centered at 100.

2. **$Y$-Axis (Economic Momentum)**:
   $$Y = 100 + \frac{\Delta I_t - \mu_{\Delta, 36}}{\sigma_{\Delta, 36}}$$
   Measures the 1-month rate of change ($\Delta I_t = I_t - I_{t-1}$) normalized over a 36-month rolling window.

### The Four Regimes (Quadrants)

| Quadrant | Level ($X$) | Momentum ($Y$) | Economic Phase |
|---|---|---|---|
| **Expansion** | $\ge 100$ | $\ge 100$ | Above-trend growth accelerating |
| **Slowdown** | $\ge 100$ | $< 100$ | Above-trend growth decelerating |
| **Contraction** | $< 100$ | $< 100$ | Below-trend growth contracting |
| **Recovery** | $< 100$ | $\ge 100$ | Below-trend growth troughing & turning up |

---

## 2. Two-Signal Consensus Engine

Forward projections combine two independent forecasting signals:

$$\mathbf{P}_h = w_{\text{mom}} \cdot \mathbf{S}_{\text{momentum}}(h) + w_{\text{ana}} \cdot \mathbf{S}_{\text{analogue}}(h)$$

Where:
- **Signal 1: CLI Momentum Extrapolation ($w_{\text{mom}} = 0.55$)**: Extrapolates current momentum velocity with exponential mean-reversion decay ($\gamma = 0.85$ per month) back toward trend.
- **Signal 2: Historical Analogue Consensus ($w_{\text{ana}} = 0.45$)**: Finds the $K=5$ most similar historical 2D trajectory segments (weighted by Euclidean distance on $X/Y$ and macro Z-scores) and computes the average path taken historically from those starting points.

*Out-of-sample backtesting (2005–2026) confirmed macro driver regression standalone achieved only 45.2% accuracy (+1.2pp over persistence), while the two-signal consensus achieved **71.6% overall** and **69.4% held-out** out-of-sample quadrant accuracy.*

---

## 3. Forecast Conviction & Calibration

Headline conviction score measures signal agreement and historical similarity:

$$\text{Conviction}_h = \text{Agreement}_h \times (0.5 \cdot S_{\text{dist}} + 0.5 \cdot S_{\text{macro}}) \times e^{-\alpha h}$$

Where $\alpha = 0.15$ per month decay.

- Binned conviction score calibration is statistically validated ($N \ge 10$ per bin) with 95% Wilson score confidence intervals.
- High-conviction signals ($\ge 58\%$) achieve **80.3% realized quadrant accuracy** ($N=127$, 95% Wilson CI: $[72.6\%, 86.2\%]$).

---

## 4. Empirical Statistical Significance

Model performance is verified against the persistence baseline ($X_t, Y_t \to X_{t+6}, Y_{t+6}$):

- **McNemar's Test for Classification Accuracy**: $\chi^2 = 32.76$, $p = 1.04 \times 10^{-8}$ ($p < 0.01$, highly statistically significant).
- **Diebold-Mariano Test for Continuous Error**: $DM = 3.73$, $p = 1.89 \times 10^{-4}$ ($p < 0.01$, highly statistically significant).
