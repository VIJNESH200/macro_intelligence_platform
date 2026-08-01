from __future__ import annotations
"""
CLI Script: Generate Forecast Conviction Calibration Reliability Diagram.
========================================================================
Plots predicted conviction vs. realized accuracy with 95% Wilson confidence bands.
Saves to docs/assets/calibration_reliability_diagram.png.
"""
import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from tests.backtest_benchmarks import wilson_ci
from config import CONFIG, MACRO_SERIES, MARKET_SERIES
from data.data_engine import DataEngine
from features.feature_engine import FeatureEngine
from research.report_data import extract_report_data
from analytics.historical_analogues import generate_analogues
from analytics.forecasting_engine import ForecastingEngine


def generate_calibration_plot(out_path: str = 'docs/assets/calibration_reliability_diagram.png') -> str:
    """Run backtest calibration calculation and plot reliability diagram."""
    print("Generating calibration reliability diagram...")
    engine = DataEngine(CONFIG, MARKET_SERIES, MACRO_SERIES, offline=True)
    df = engine.load_all()
    df, _ = FeatureEngine.compute_all(df, CONFIG)

    start_idx = CONFIG['window'] + 12
    end_idx = len(df) - 7
    results = []

    for idx in range(start_idx, end_idx + 1):
        df_sliced = df.iloc[:idx+1]
        real_6m_quad = df['Quadrant'].iloc[idx + 6]
        plot_elements = {'market_state': {'selected': []}}
        data = extract_report_data(df, CONFIG, plot_elements, idx, MARKET_SERIES)
        analogues = generate_analogues(df_sliced, idx, data, MARKET_SERIES)
        forecast = ForecastingEngine.project(df_sliced, idx, CONFIG, analogues, data.get('macro_contrib'))
        proj_6m_quad = forecast['forecast_6m']['quadrant']
        conviction = forecast['forecast_6m']['conviction']

        results.append({
            'conviction': conviction,
            'correct': proj_6m_quad == real_6m_quad
        })

    res_df = pd.DataFrame(results)
    bins = [10, 45, 55, 65, 100]
    labels = ['Low (10-45%)', 'Moderate (45-55%)', 'Strong (55-65%)', 'High (>65%)']
    res_df['bin'] = pd.cut(res_df['conviction'], bins=bins, labels=labels)

    avg_convs = []
    realized_accs = []
    ci_lows = []
    ci_highs = []

    for lbl in labels:
        b_df = res_df[res_df['bin'] == lbl]
        if not b_df.empty and len(b_df) >= 5:
            n = len(b_df)
            k = b_df['correct'].sum()
            avg_conv = b_df['conviction'].mean()
            acc = (k / n) * 100
            l, h = wilson_ci(k, n)

            avg_convs.append(avg_conv)
            realized_accs.append(acc)
            ci_lows.append(l)
            ci_highs.append(h)

    fig, ax = plt.subplots(figsize=(7, 5), dpi=300)
    ax.plot([30, 85], [30, 85], 'k--', alpha=0.5, label='Perfect Calibration (y=x)')

    ax.errorbar(
        avg_convs, realized_accs,
        yerr=[np.array(realized_accs) - np.array(ci_lows), np.array(ci_highs) - np.array(realized_accs)],
        fmt='o-', color='#1f497d', ecolor='#64748b', elinewidth=1.5, capsize=4,
        linewidth=2, label='Model Realized Accuracy (95% Wilson CI)'
    )

    ax.set_xlabel('Predicted Conviction Score (%)', fontsize=10, fontweight='bold')
    ax.set_ylabel('Realized Quadrant Accuracy (%)', fontsize=10, fontweight='bold')
    ax.set_title('Forecast Conviction Reliability Diagram (6M Horizon)', fontsize=12, fontweight='bold', pad=12)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper left', frameon=True)
    plt.tight_layout()

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)

    print(f"[+] Reliability diagram saved -> {out_path}")
    return out_path


if __name__ == '__main__':
    generate_calibration_plot()
