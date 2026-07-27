from __future__ import annotations
"""
Rigorous validation and benchmarking of the Forecasting Engine.
================================================================
Compares the Two-Signal Consensus model against baselines
and evaluates empirical calibration and statistical significance.
"""
import os
import sys
import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from config import CONFIG, FORECAST_CONFIG, MACRO_SERIES, MARKET_SERIES, reload_for_market
from data.data_engine import DataEngine
from features.feature_engine import FeatureEngine
from research.report_data import extract_report_data
from analytics.historical_analogues import generate_analogues
from analytics.forecasting_engine import ForecastingEngine
from analytics.transition_matrix import compute_transition_matrix, get_transition_probs_from


def compute_mcnemar_test(c1_correct: pd.Series, c2_correct: pd.Series) -> tuple[float, float]:
    """Compute McNemar's test for paired classification accuracy comparison.
    Returns (chi2_statistic, p_value).
    """
    b = (c1_correct & ~c2_correct).sum()  # model 1 right, model 2 wrong
    c = (~c1_correct & c2_correct).sum()  # model 1 wrong, model 2 right
    if b + c == 0:
        return 0.0, 1.0
    chi2_stat = (abs(b - c) - 1) ** 2 / (b + c)
    p_val = stats.chi2.sf(chi2_stat, df=1)
    return float(chi2_stat), float(p_val)


def compute_diebold_mariano_test(e1: np.ndarray, e2: np.ndarray, h: int = 6) -> tuple[float, float]:
    """Compute Diebold-Mariano test for predictive accuracy comparison of continuous errors.
    Returns (dm_statistic, p_value).
    """
    d = e1**2 - e2**2
    n = len(d)
    mean_d = np.mean(d)
    
    # Auto-covariance lag adjustment (Harvey, Leybourne, Newbold 1997)
    gamma_0 = np.var(d, ddof=0)
    gamma_sum = 0.0
    for k in range(1, h):
        cov_k = np.cov(d[k:], d[:-k])[0, 1] if len(d[k:]) > 0 else 0.0
        gamma_sum += (1 - k / h) * cov_k
        
    var_d = (gamma_0 + 2 * gamma_sum) / n
    if var_d <= 0:
        return 0.0, 1.0
        
    dm_stat = mean_d / np.sqrt(var_d)
    # HLN small-sample correction multiplier
    hln_mult = np.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
    dm_stat_corrected = dm_stat * hln_mult
    p_val = 2 * (1 - stats.norm.cdf(abs(dm_stat_corrected)))
    return float(dm_stat_corrected), float(p_val)


def wilson_ci(k: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    """Compute Wilson score 95% confidence interval for binomial accuracy percentage."""
    if n == 0:
        return 0.0, 0.0
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    p_hat = k / n
    denom = 1 + z**2 / n
    center = (p_hat + z**2 / (2 * n)) / denom
    spread = z * np.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * n)) / n) / denom
    return max(0.0, (center - spread) * 100), min(100.0, (center + spread) * 100)


# Quality gates are per-market: the same model scores very differently on each,
# because the signal ranking inverts (Momentum is India's strongest predictor and
# the US's weakest). A single global bar would either wave through India
# regressions or fail the US permanently. Each bar sits below the current
# committed baseline by roughly one standard error, so it catches regressions
# without tracking noise.
MARKET_GATES = {
    'INDIA': {'min_accuracy': 60.0, 'min_top_quartile_accuracy': 75.0, 'max_distance_mae': 1.20},
    'US':    {'min_accuracy': 50.0, 'min_top_quartile_accuracy': 60.0, 'max_distance_mae': 1.30},
}


def run_benchmarks(market: str = 'INDIA'):
    """
    Freeze-Then-Evaluate Discipline Rule:
    ======================================
    If model hyperparameters, weights, or architecture are modified based on backtest tuning,
    the resulting benchmark run is an in-sample optimization, not a clean evaluation.
    Evaluate final frozen configurations once on held-out periods or out-of-sample datasets.
    """
    # The active market is mutable global state that the market toggle can flip,
    # and the choice persists to ~/.macro_intelligence_platform/market_preference.txt.
    # Pin it explicitly so the run never inherits whichever market the app was last
    # opened in, and so each market is scored against its own gates.
    reload_for_market(market)
    gates = MARKET_GATES[market]

    print(f"Loading historical data for {market}...")
    # Use offline mode for deterministic, fast CI & test runs
    engine = DataEngine(CONFIG, MARKET_SERIES, MACRO_SERIES, offline=True)
    df = engine.load_all()
    df, _ = FeatureEngine.compute_all(df, CONFIG)
    
    # Validation range: exclude lookback window (36m) + 12m buffer, reserve 6m for realizations
    start_idx = CONFIG['window'] + 12
    end_idx = len(df) - 7
    
    results = []
    
    print(f"Running rolling out-of-sample backtest from {df.index[start_idx].strftime('%b %Y')} to {df.index[end_idx].strftime('%b %Y')} ({end_idx - start_idx + 1} steps)...")
    
    for idx in range(start_idx, end_idx + 1):
        df_sliced = df.iloc[:idx+1]
        
        # Current observation state
        curr_quad = df['Quadrant'].iloc[idx]
        curr_x = df['X'].iloc[idx]
        curr_y = df['Y'].iloc[idx]
        
        # Realized 6M state
        real_6m_quad = df['Quadrant'].iloc[idx + 6]
        real_6m_x = df['X'].iloc[idx + 6]
        real_6m_y = df['Y'].iloc[idx + 6]
        
        # Mock elements for report data
        plot_elements = {'market_state': {'selected': []}}
        data = extract_report_data(df, CONFIG, plot_elements, idx, MARKET_SERIES)
        
        # Analogue lookup strictly limited to df_sliced (past data)
        analogues = generate_analogues(df_sliced, idx, data, MARKET_SERIES)
        
        # ----------------------------------------------------
        # 1. Two-Signal Consensus (Full Model)
        # ----------------------------------------------------
        forecast = ForecastingEngine.project(df_sliced, idx, CONFIG, analogues, data.get('macro_contrib'))
        proj_6m_quad = forecast['forecast_6m']['quadrant']
        proj_6m_x = forecast['forecast_6m']['x']
        proj_6m_y = forecast['forecast_6m']['y']
        conviction = forecast['forecast_6m']['conviction']
        
        # ----------------------------------------------------
        # 2. CLI Momentum Only (Signal 1)
        # ----------------------------------------------------
        mom_proj = ForecastingEngine._momentum_signal(df_sliced, idx, CONFIG['center'], 0.85, 6)
        mom_6m_x, mom_6m_y = mom_proj['path'][5]
        mom_6m_quad = ForecastingEngine._get_quadrant(mom_6m_x, mom_6m_y, CONFIG['center'])
        
        # ----------------------------------------------------
        # 3. Analogues Only (Signal 2)
        # ----------------------------------------------------
        ana_proj = ForecastingEngine._analogue_signal(df_sliced, idx, analogues, 6)
        ana_6m_x, ana_6m_y = ana_proj['path'][5]
        ana_6m_quad = ForecastingEngine._get_quadrant(ana_6m_x, ana_6m_y, CONFIG['center'])
        
        # ----------------------------------------------------
        # 4. Macro Drivers Only (Signal 3)
        # ----------------------------------------------------
        macro_proj = ForecastingEngine._macro_driver_signal(df_sliced, idx, CONFIG['center'], data.get('macro_contrib'), 6)
        macro_6m_x, macro_6m_y = macro_proj['path'][5]
        macro_6m_quad = ForecastingEngine._get_quadrant(macro_6m_x, macro_6m_y, CONFIG['center'])
        
        # ----------------------------------------------------
        # 5. Transition Matrix Only (Markov Baseline)
        # ----------------------------------------------------
        trans_matrix = compute_transition_matrix(df_sliced)
        probs = get_transition_probs_from(trans_matrix['matrix'], curr_quad)
        
        # Remove 'From \ To' or label columns, find the highest probability transition
        labels = trans_matrix['labels']
        max_p = -1.0
        tm_6m_quad = curr_quad  # fallback
        for label in labels:
            p = probs.get(label, 0.0)
            if p > max_p:
                max_p = p
                tm_6m_quad = label
                
        results.append({
            'date': df.index[idx],
            'conviction': conviction,
            'real_6m_quad': real_6m_quad,
            'real_6m_x': real_6m_x,
            'real_6m_y': real_6m_y,
            # Current values (for Persistence)
            'curr_quad': curr_quad,
            'curr_x': curr_x,
            'curr_y': curr_y,
            # Models
            'consensus_quad': proj_6m_quad, 'consensus_x': proj_6m_x, 'consensus_y': proj_6m_y,
            'momentum_quad': mom_6m_quad, 'momentum_x': mom_6m_x, 'momentum_y': mom_6m_y,
            'analogues_quad': ana_6m_quad, 'analogues_x': ana_6m_x, 'analogues_y': ana_6m_y,
            'macro_quad': macro_6m_quad, 'macro_x': macro_6m_x, 'macro_y': macro_6m_y,
            'tm_quad': tm_6m_quad
        })
        
    res_df = pd.DataFrame(results)
    
    # ----------------------------------------------------
    # Calculate Benchmarking Performance Metrics (6M Horizon)
    # ----------------------------------------------------
    print("\n==================================================================")
    print(f"          6-MONTH HORIZON MODEL BENCHMARKS — {market}")
    print("==================================================================")
    
    w = FORECAST_CONFIG['weights']
    consensus_label = (f"Blended Consensus ({w['momentum']:.0%} Mom / "
                       f"{w['analogues']:.0%} Ana / {w['macro_drivers']:.0%} Macro)")

    models = {
        'Persistence': ('curr_quad', 'curr_x', 'curr_y'),
        'CLI Momentum Only': ('momentum_quad', 'momentum_x', 'momentum_y'),
        'Analogues Only': ('analogues_quad', 'analogues_x', 'analogues_y'),
        'Macro Drivers Only': ('macro_quad', 'macro_x', 'macro_y'),
        'Transition Matrix Only': ('tm_quad', None, None),
        consensus_label: ('consensus_quad', 'consensus_x', 'consensus_y'),
    }
    
    summary_data = []
    
    for name, (quad_col, x_col, y_col) in models.items():
        # Quadrant Accuracy
        acc = (res_df[quad_col] == res_df['real_6m_quad']).mean() * 100
        
        # Coordinate MAE if applicable
        if x_col and y_col:
            mae_x = np.abs(res_df[x_col] - res_df['real_6m_x']).mean()
            mae_y = np.abs(res_df[y_col] - res_df['real_6m_y']).mean()
            dist_mae = np.sqrt((res_df[x_col] - res_df['real_6m_x'])**2 + (res_df[y_col] - res_df['real_6m_y'])**2).mean()
            mae_x_str = f"{mae_x:.3f}"
            mae_y_str = f"{mae_y:.3f}"
            dist_str = f"{dist_mae:.3f}"
        else:
            mae_x_str = "N/A"
            mae_y_str = "N/A"
            dist_str = "N/A"
            
        summary_data.append({
            'Model': name,
            'Quadrant Accuracy': f"{acc:.1f}%",
            'Health (X) MAE': mae_x_str,
            'Momentum (Y) MAE': mae_y_str,
            'Distance MAE': dist_str,
            'acc_raw': acc
        })
        
    summary_df = pd.DataFrame(summary_data)
    print(summary_df.to_string(index=False))

    # ----------------------------------------------------
    # Statistical Significance Testing (Consensus vs Persistence)
    # ----------------------------------------------------
    print("\n------------------------------------------------------------------")
    print("        STATISTICAL SIGNIFICANCE TESTS (Consensus vs Persistence)")
    print("------------------------------------------------------------------")
    cons_correct = (res_df['consensus_quad'] == res_df['real_6m_quad'])
    pers_correct = (res_df['curr_quad'] == res_df['real_6m_quad'])
    
    mc_stat, mc_pval = compute_mcnemar_test(cons_correct, pers_correct)
    print(f" McNemar's Test (Classification Accuracy): chi^2 = {mc_stat:.2f}, p-value = {mc_pval:.4e}")
    if mc_pval < 0.01:
        print("  -> Difference in quadrant classification accuracy is HIGHLY STATISTICALLY SIGNIFICANT (p < 0.01)")
    elif mc_pval < 0.05:
        print("  -> Difference in quadrant classification accuracy is STATISTICALLY SIGNIFICANT (p < 0.05)")
    else:
        print("  -> Difference in classification accuracy is not statistically significant at 5% level.")

    cons_err = np.sqrt((res_df['consensus_x'] - res_df['real_6m_x'])**2 + (res_df['consensus_y'] - res_df['real_6m_y'])**2)
    pers_err = np.sqrt((res_df['curr_x'] - res_df['real_6m_x'])**2 + (res_df['curr_y'] - res_df['real_6m_y'])**2)
    dm_stat, dm_pval = compute_diebold_mariano_test(pers_err.values, cons_err.values, h=6)
    print(f" Diebold-Mariano Test (Continuous Distance MAE): DM = {dm_stat:.2f}, p-value = {dm_pval:.4e}")
    if dm_pval < 0.01:
        print("  -> Outperformance in continuous Distance MAE is HIGHLY STATISTICALLY SIGNIFICANT (p < 0.01)")
    elif dm_pval < 0.05:
        print("  -> Outperformance in continuous Distance MAE is STATISTICALLY SIGNIFICANT (p < 0.05)")
    else:
        print("  -> Continuous error outperformance is not statistically significant at 5% level.")

    # Held-Out Evaluation Window Breakdown (Jan 2019 - Jan 2026)
    heldout_df = res_df[res_df['date'] >= '2019-01-01']
    if not heldout_df.empty:
        print("\n------------------------------------------------------------------")
        print("    HELD-OUT EVALUATION WINDOW BENCHMARK (Jan 2019 - Jan 2026)")
        print("------------------------------------------------------------------")
        heldout_summary = []
        for name, (quad_col, x_col, y_col) in models.items():
            acc_h = (heldout_df[quad_col] == heldout_df['real_6m_quad']).mean() * 100
            heldout_summary.append({'Model': name, 'Held-Out Quadrant Accuracy': f"{acc_h:.1f}%"})
        print(pd.DataFrame(heldout_summary).to_string(index=False))

    # ----------------------------------------------------
    # Calculate Forecast Conviction Calibration Curve
    # ----------------------------------------------------
    print("\n==================================================================")
    print("             FORECAST CONVICTION CALIBRATION ANALYSIS")
    print("==================================================================")
    
    # Bin by quartile of the realized conviction distribution rather than fixed cut
    # points. Fixed edges were tuned to India's distribution and left the US 'Strong'
    # bin holding 2 samples, which makes its accuracy meaningless; quartiles keep every
    # bin populated on any market and let the calibration check compare like with like.
    binned = pd.qcut(res_df['conviction'], 4, duplicates='drop')
    res_df['conviction_bin'] = binned
    bin_labels = list(binned.cat.categories)

    calibration_data = []
    for label in bin_labels:
        bin_df = res_df[res_df['conviction_bin'] == label]
        if not bin_df.empty:
            avg_conv = bin_df['conviction'].mean()
            k_correct = (bin_df['consensus_quad'] == bin_df['real_6m_quad']).sum()
            sample_count = len(bin_df)
            realized_acc = (k_correct / sample_count) * 100
            ci_low, ci_high = wilson_ci(k_correct, sample_count)
            calibration_data.append({
                'Conviction Bin': f"{label.left:.1f}-{label.right:.1f}%",
                'Sample Size': sample_count,
                'Average Conviction Score': f"{avg_conv:.1f}%",
                'Realized Quadrant Accuracy': f"{realized_acc:.1f}%",
                '95% Wilson CI': f"[{ci_low:.1f}%, {ci_high:.1f}%]",
                'Calibration Error': f"{abs(avg_conv - realized_acc):.1f}%"
            })
            
    cal_df = pd.DataFrame(calibration_data)
    print(cal_df.to_string(index=False))
    print("==================================================================")

    # ----------------------------------------------------
    # CI Quality Gate Assertions
    # ----------------------------------------------------
    consensus_acc = (res_df['consensus_quad'] == res_df['real_6m_quad']).mean() * 100
    persistence_acc = (res_df['curr_quad'] == res_df['real_6m_quad']).mean() * 100
    dist_mae = np.sqrt((res_df['consensus_x'] - res_df['real_6m_x'])**2 + (res_df['consensus_y'] - res_df['real_6m_y'])**2).mean()

    # Conviction calibration quality gate checks (evaluated on statistically representative bins with N >= 10)
    valid_cal_rows = [row for row in calibration_data if row['Sample Size'] >= 10]
    assert len(valid_cal_rows) >= 2, f"CI REGRESSION: Fewer than 2 statistically valid conviction bins (N >= 10)"

    valid_cal_errors = [float(row['Calibration Error'].replace('%', '')) for row in valid_cal_rows]
    mean_cal_err = float(np.mean(valid_cal_errors))
    assert mean_cal_err <= 30.0, f"CI REGRESSION [{market}]: Mean conviction calibration error on valid bins ({mean_cal_err:.1f}%) exceeds 30.0% threshold"

    # Conviction must be monotone in outcome: the model's most confident quartile
    # has to beat its least confident one, or the score carries no information.
    top_bin = res_df[res_df['conviction_bin'] == bin_labels[-1]]
    bottom_bin = res_df[res_df['conviction_bin'] == bin_labels[0]]
    assert not top_bin.empty, f"CI REGRESSION [{market}]: Top conviction quartile is empty"
    top_acc = (top_bin['consensus_quad'] == top_bin['real_6m_quad']).mean() * 100
    bottom_acc = (bottom_bin['consensus_quad'] == bottom_bin['real_6m_quad']).mean() * 100
    assert top_acc >= gates['min_top_quartile_accuracy'], f"CI REGRESSION [{market}]: Top-quartile conviction accuracy ({top_acc:.1f}%) drops below {gates['min_top_quartile_accuracy']:.1f}% threshold"
    assert top_acc > bottom_acc, f"CI REGRESSION [{market}]: Conviction is not discriminative — top quartile {top_acc:.1f}% vs bottom quartile {bottom_acc:.1f}%"

    assert consensus_acc >= gates['min_accuracy'], f"CI REGRESSION [{market}]: 6M Consensus Quadrant Accuracy drops below {gates['min_accuracy']:.1f}% threshold ({consensus_acc:.1f}%)"
    assert consensus_acc > persistence_acc, f"CI REGRESSION [{market}]: Consensus model fails to outperform Persistence baseline ({consensus_acc:.1f}% vs {persistence_acc:.1f}%)"
    assert dist_mae <= gates['max_distance_mae'], f"CI REGRESSION [{market}]: Distance MAE exceeds {gates['max_distance_mae']:.2f} threshold ({dist_mae:.3f})"
    print(f"\n[+] CI Benchmark Quality Gate [{market}]: PASSED "
          f"(accuracy {consensus_acc:.1f}%, MAE {dist_mae:.3f}, top-quartile conviction {top_acc:.1f}%)")


if __name__ == "__main__":
    # Both markets are gated. The model is materially weaker on US, but it is shipped
    # there, so it needs regression cover too -- against its own baseline, not India's.
    for _market in ('INDIA', 'US'):
        run_benchmarks(_market)
