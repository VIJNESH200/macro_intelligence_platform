"""
Backtesting and Validation of the Forecasting Engine.
======================================================
Performs a rolling historical backtest of the 3-month and 6-month forecasts,
comparing them against a simple persistence baseline.
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


def run_backtest():
    print("Initializing Data Engine for Backtest...")
    engine = DataEngine(CONFIG, MARKET_SERIES, MACRO_SERIES)
    df = engine.load_all()
    df, _ = FeatureEngine.compute_all(df, CONFIG)
    
    # We need to run backtest over a subset of history
    # Start after we have enough historical data for rolling windows (e.g. 36 months)
    start_idx = CONFIG['window'] + 12
    end_idx = len(df) - 7  # Reserve 6 months for realization check
    
    results = []
    
    print(f"Running rolling forecast backtest from index {start_idx} to {end_idx} ({end_idx - start_idx + 1} steps)...")
    
    for idx in range(start_idx, end_idx + 1):
        df_sliced = df.iloc[:idx+1]
        
        # Minimal mocked elements
        plot_elements = {'market_state': {'selected': []}}
        data = extract_report_data(df, CONFIG, plot_elements, idx, MARKET_SERIES)
        analogues = generate_analogues(df_sliced, idx, data, MARKET_SERIES)
        
        # Generate Forecast
        forecast = ForecastingEngine.project(df, idx, CONFIG, analogues, data.get('macro_contrib'))
        
        # Realized values
        real_3m_x = df['X'].iloc[idx + 3]
        real_3m_y = df['Y'].iloc[idx + 3]
        real_3m_quad = df['Quadrant'].iloc[idx + 3]
        
        real_6m_x = df['X'].iloc[idx + 6]
        real_6m_y = df['Y'].iloc[idx + 6]
        real_6m_quad = df['Quadrant'].iloc[idx + 6]
        
        # Forecast values
        proj_3m_x = forecast['forecast_3m']['x']
        proj_3m_y = forecast['forecast_3m']['y']
        proj_3m_quad = forecast['forecast_3m']['quadrant']
        
        proj_6m_x = forecast['forecast_6m']['x']
        proj_6m_y = forecast['forecast_6m']['y']
        proj_6m_quad = forecast['forecast_6m']['quadrant']
        
        results.append({
            'date': df.index[idx],
            # Current values (for persistence baseline)
            'curr_x': df['X'].iloc[idx],
            'curr_y': df['Y'].iloc[idx],
            'curr_quad': df['Quadrant'].iloc[idx],
            # 3M Realized vs Forecast
            'real_3m_x': real_3m_x, 'real_3m_y': real_3m_y, 'real_3m_quad': real_3m_quad,
            'proj_3m_x': proj_3m_x, 'proj_3m_y': proj_3m_y, 'proj_3m_quad': proj_3m_quad,
            # 6M Realized vs Forecast
            'real_6m_x': real_6m_x, 'real_6m_y': real_6m_y, 'real_6m_quad': real_6m_quad,
            'proj_6m_x': proj_6m_x, 'proj_6m_y': proj_6m_y, 'proj_6m_quad': proj_6m_quad,
        })
        
    res_df = pd.DataFrame(results)
    
    # Calculate performance metrics
    print("\n==================================================")
    print("          FORECAST ENGINE BACKTEST RESULTS")
    print("==================================================")
    
    for h in [3, 6]:
        print(f"\n--- {h}-Month Horizon ---")
        
        # 1. Model Errors
        err_x_model = np.abs(res_df[f'proj_{h}m_x'] - res_df[f'real_{h}m_x'])
        err_y_model = np.abs(res_df[f'proj_{h}m_y'] - res_df[f'real_{h}m_y'])
        mae_x_model = err_x_model.mean()
        mae_y_model = err_y_model.mean()
        
        # 2. Baseline Errors (Persistence: future = current)
        err_x_base = np.abs(res_df['curr_x'] - res_df[f'real_{h}m_x'])
        err_y_base = np.abs(res_df['curr_y'] - res_df[f'real_{h}m_y'])
        mae_x_base = err_x_base.mean()
        mae_y_base = err_y_base.mean()
        
        # 3. Model vs Baseline Improvement
        imp_x = (mae_x_base - mae_x_model) / mae_x_base * 100
        imp_y = (mae_y_base - mae_y_model) / mae_y_base * 100
        
        # 4. Quadrant Accuracy
        acc_model = (res_df[f'proj_{h}m_quad'] == res_df[f'real_{h}m_quad']).mean() * 100
        acc_base = (res_df['curr_quad'] == res_df[f'real_{h}m_quad']).mean() * 100
        
        print(f"Health (X) MAE: Model = {mae_x_model:.3f} | Persistence = {mae_x_base:.3f} | Improvement = {imp_x:+.1f}%")
        print(f"Momentum (Y) MAE: Model = {mae_y_model:.3f} | Persistence = {mae_y_base:.3f} | Improvement = {imp_y:+.1f}%")
        print(f"Quadrant Accuracy: Model = {acc_model:.1f}% | Persistence = {acc_base:.1f}% | Improvement = {acc_model - acc_base:+.1f}%")


if __name__ == "__main__":
    run_backtest()
