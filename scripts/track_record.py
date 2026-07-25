from __future__ import annotations
"""
Historical Track Record Generator — Macro Intelligence Platform
================================================================
Generates a rolling out-of-sample track record comparing historical 
3M, 6M, and 9M business cycle forecasts against actual realized outcomes.
Saves the public track record ledger to docs/track_record.csv.
"""
import os
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import CONFIG, MARKET_SERIES, MACRO_SERIES
from data.data_engine import DataEngine
from features.feature_engine import FeatureEngine
from analytics.historical_analogues import generate_analogues
from analytics.macro_intelligence_engine import MacroIntelligenceEngine
from analytics.forecasting_engine import ForecastingEngine


def generate_track_record():
    print("==================================================================")
    print("   GENERATING HISTORICAL OUT-OF-SAMPLE FORECAST TRACK RECORD")
    print("==================================================================")

    engine = DataEngine(CONFIG, MARKET_SERIES, MACRO_SERIES, offline=True)
    df = engine.load_all()
    df, _ = FeatureEngine.compute_all(df, CONFIG)

    start_idx = CONFIG['window'] + 12
    end_idx = len(df) - 10

    records = []

    for idx in range(start_idx, end_idx):
        historical_df = df.iloc[:idx + 1].copy()
        current_date = df.index[idx].strftime('%Y-%m-%d')
        current_quad = df['Quadrant'].iloc[idx]

        # Extract analogues & macro drivers strictly on historical cutoff
        data_subset = {
            'X': df['X'].iloc[idx],
            'Y': df['Y'].iloc[idx],
            'quadrant': current_quad
        }
        analogues = generate_analogues(historical_df, idx, data_subset, MARKET_SERIES)
        macro_res = MacroIntelligenceEngine.assign_contribution(historical_df, idx)

        forecast_result = ForecastingEngine.project(historical_df, idx, CONFIG, analogues, macro_res)

        f3m = forecast_result['forecast_3m']
        f6m = forecast_result['forecast_6m']
        f9m = forecast_result['forecast_9m']

        # Realized outcomes
        real_3m_date = df.index[idx + 3].strftime('%Y-%m-%d')
        real_3m_quad = df['Quadrant'].iloc[idx + 3]
        real_6m_date = df.index[idx + 6].strftime('%Y-%m-%d')
        real_6m_quad = df['Quadrant'].iloc[idx + 6]
        real_9m_date = df.index[idx + 9].strftime('%Y-%m-%d')
        real_9m_quad = df['Quadrant'].iloc[idx + 9]

        records.append({
            'Date': current_date,
            'Current_Quadrant': current_quad,
            '3M_Forecast_Quad': f3m['quadrant'],
            '3M_Conviction': f3m['conviction'],
            '3M_Real_Date': real_3m_date,
            '3M_Real_Quad': real_3m_quad,
            '3M_Hit': f3m['quadrant'] == real_3m_quad,
            '6M_Forecast_Quad': f6m['quadrant'],
            '6M_Conviction': f6m['conviction'],
            '6M_Real_Date': real_6m_date,
            '6M_Real_Quad': real_6m_quad,
            '6M_Hit': f6m['quadrant'] == real_6m_quad,
            '9M_Forecast_Quad': f9m['quadrant'],
            '9M_Conviction': f9m['conviction'],
            '9M_Real_Date': real_9m_date,
            '9M_Real_Quad': real_9m_quad,
            '9M_Hit': f9m['quadrant'] == real_9m_quad,
        })

    track_df = pd.DataFrame(records)

    docs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'docs'))
    if not os.path.exists(docs_dir):
        os.makedirs(docs_dir)

    out_csv = os.path.join(docs_dir, 'track_record.csv')
    track_df.to_csv(out_csv, index=False)

    acc_3m = track_df['3M_Hit'].mean() * 100
    acc_6m = track_df['6M_Hit'].mean() * 100
    acc_9m = track_df['9M_Hit'].mean() * 100

    print(f"\n[+] Track Record Generated ({len(track_df)} Monthly Evaluation Steps)")
    print(f"    - 3-Month Quadrant Accuracy: {acc_3m:.1f}%")
    print(f"    - 6-Month Quadrant Accuracy: {acc_6m:.1f}%")
    print(f"    - 9-Month Quadrant Accuracy: {acc_9m:.1f}%")
    print(f"    - Saved track record ledger to: {out_csv}")
    print("==================================================================")


if __name__ == '__main__':
    generate_track_record()
