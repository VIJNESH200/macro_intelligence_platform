"""
Rigorous validation and benchmarking of the Forecasting Engine.
================================================================
Compares the Three-Signal Consensus model against five baselines
and evaluates the empirical calibration of Forecast Conviction.
"""
import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from config import CONFIG, MACRO_SERIES, MARKET_SERIES
from data.data_engine import DataEngine
from features.feature_engine import FeatureEngine
from research.report_data import extract_report_data
from analytics.historical_analogues import generate_analogues
from analytics.forecasting_engine import ForecastingEngine
from analytics.transition_matrix import compute_transition_matrix, get_transition_probs_from


def run_benchmarks():
    print("Loading historical data...")
    engine = DataEngine(CONFIG, MARKET_SERIES, MACRO_SERIES)
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
        # 1. Three-Signal Consensus (Full Model)
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
    print("                6-MONTH HORIZON MODEL BENCHMARKS")
    print("==================================================================")
    
    models = {
        'Persistence': ('curr_quad', 'curr_x', 'curr_y'),
        'CLI Momentum Only': ('momentum_quad', 'momentum_x', 'momentum_y'),
        'Analogues Only': ('analogues_quad', 'analogues_x', 'analogues_y'),
        'Macro Drivers Only': ('macro_quad', 'macro_x', 'macro_y'),
        'Transition Matrix Only': ('tm_quad', None, None),
        'Three-Signal Consensus': ('consensus_quad', 'consensus_x', 'consensus_y'),
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
    # Calculate Forecast Conviction Calibration Curve
    # ----------------------------------------------------
    print("\n==================================================================")
    print("             FORECAST CONVICTION CALIBRATION ANALYSIS")
    print("==================================================================")
    
    # Define Conviction bins for 6-month horizon (since max conviction is ~65% due to decay)
    bins = [10, 45, 52, 58, 66]
    bin_labels = ['Low (10-45%)', 'Moderate (45-52%)', 'Strong (52-58%)', 'High (58-65%)']
    
    res_df['conviction_bin'] = pd.cut(res_df['conviction'], bins=bins, labels=bin_labels)
    
    calibration_data = []
    for label in bin_labels:
        bin_df = res_df[res_df['conviction_bin'] == label]
        if not bin_df.empty:
            avg_conv = bin_df['conviction'].mean()
            realized_acc = (bin_df['consensus_quad'] == bin_df['real_6m_quad']).mean() * 100
            sample_count = len(bin_df)
            calibration_data.append({
                'Conviction Bin': label,
                'Sample Size': sample_count,
                'Average Conviction Score': f"{avg_conv:.1f}%",
                'Realized Quadrant Accuracy': f"{realized_acc:.1f}%",
                'Calibration Error': f"{abs(avg_conv - realized_acc):.1f}%"
            })
            
    cal_df = pd.DataFrame(calibration_data)
    print(cal_df.to_string(index=False))
    print("==================================================================")


if __name__ == "__main__":
    run_benchmarks()
