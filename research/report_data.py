"""
Report Data — Extracts structured data from the DataFrame for report consumption.
==================================================================================
Exact port of report_data.py.
"""
import datetime
import pandas as pd
import numpy as np


def extract_report_data(df, config: dict, plot_elements: dict,
                        current_frame: int, market_series_config: dict) -> dict:
    """Extract a flat data dictionary from the DataFrame at a given frame index.

    Returns a dict with date, indicator metadata, health/momentum values,
    quadrant, distance, direction, and multi-horizon market data.
    """
    idx = int(current_frame)
    if idx >= len(df):
        idx = len(df) - 1

    curr_row = df.iloc[idx]

    # Safely get center
    c = config.get('center', 100)

    # Safely get X and Y
    curr_x = curr_row.get('X', c)
    curr_y = curr_row.get('Y', c)

    # Recompute distance & direction cleanly
    dist = np.sqrt((curr_x - c)**2 + (curr_y - c)**2)

    prev_i = max(0, idx - 1)
    prev_x = df.iloc[prev_i].get('X', c)
    prev_y = df.iloc[prev_i].get('Y', c)
    dx = curr_x - prev_x
    dy = curr_y - prev_y
    if dx == 0 and dy == 0:
        dir_sym = "Neutral"
    else:
        angle = np.degrees(np.arctan2(dy, dx))
        if angle < 0:
            angle += 360
        if 22.5 <= angle < 67.5:
            dir_sym = "Northeast"
        elif 67.5 <= angle < 112.5:
            dir_sym = "North"
        elif 112.5 <= angle < 157.5:
            dir_sym = "Northwest"
        elif 157.5 <= angle < 202.5:
            dir_sym = "West"
        elif 202.5 <= angle < 247.5:
            dir_sym = "Southwest"
        elif 247.5 <= angle < 292.5:
            dir_sym = "South"
        elif 292.5 <= angle < 337.5:
            dir_sym = "Southeast"
        else:
            dir_sym = "East"

    try:
        from ..analytics.macro_intelligence_engine import MacroIntelligenceEngine
        from ..analytics.research_engine import ResearchEngine
    except ImportError:
        from analytics.macro_intelligence_engine import MacroIntelligenceEngine
        from analytics.research_engine import ResearchEngine
    
    # 4. Phase 2 Macro Drivers
    macro_eval = MacroIntelligenceEngine.evaluate_indicators(df, idx)
    macro_contrib = MacroIntelligenceEngine.assign_contribution(df, idx)
    macro_shifts = MacroIntelligenceEngine.detect_regime_shifts(df, idx)
    research_narrative = ResearchEngine.generate_insights(df, idx)

    data = {
        'date': curr_row.name.strftime('%b %Y'),
        'indicator': config.get('name', 'N/A'),
        'source': config.get('source', 'N/A'),
        'window': f"{config.get('window', 'N/A')} Months",
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'center': c,
        'health_val': curr_x,
        'momentum_val': curr_y,
        'quadrant': curr_row.get('Quadrant', 'Unknown'),
        'distance': dist,
        'direction': dir_sym,
        'macro_contrib': macro_contrib,
        'macro_shifts': macro_shifts,
        'research_narrative': research_narrative,
        'market_data': [],
        'market_horizon': 'N/A'
    }

    # 4. Market Context (Multi-Horizon)
    if 'market_state' in plot_elements:
        m_state = plot_elements['market_state']
        horizons = [1, 3, 6, 12]
        data['market_horizon'] = 'Multi'

        for name, series_info in market_series_config.items():
            if name in m_state.get('selected', []):
                try:
                    cur_val = df[name].iloc[idx]
                except (KeyError, IndexError):
                    cur_val = np.nan

                if pd.isna(cur_val):
                    asset_dict = {
                        'name': name,
                        'current_val_str': "N/A",
                        'returns_str': {f"{h}M": "N/A" for h in horizons},
                        'returns_raw': {f"{h}M": np.nan for h in horizons},
                        'type': series_info.get('type')
                    }
                else:
                    fmt_str = series_info.get('format', '{:.2f}')
                    val_str = fmt_str.format(cur_val)

                    ret_str = {}
                    ret_raw = {}

                    for h in horizons:
                        prev_i_h = max(0, idx - h)
                        try:
                            prev_val = df[name].iloc[prev_i_h]
                        except (KeyError, IndexError):
                            prev_val = np.nan

                        if pd.isna(prev_val) or prev_val == 0:
                            ret_str[f"{h}M"] = "N/A"
                            ret_raw[f"{h}M"] = np.nan
                        elif series_info.get('type') == 'yfinance':
                            pct_chg = (cur_val - prev_val) / prev_val * 100
                            sign = '+' if pct_chg > 0 else ''
                            ret_str[f"{h}M"] = f"{sign}{pct_chg:.1f}%"
                            ret_raw[f"{h}M"] = pct_chg
                        else:
                            bp_chg = (cur_val - prev_val) * 100
                            sign = '+' if bp_chg > 0 else ''
                            ret_str[f"{h}M"] = f"{sign}{bp_chg:.0f} bp"
                            ret_raw[f"{h}M"] = bp_chg

                    asset_dict = {
                        'name': name,
                        'current_val_str': val_str,
                        'returns_str': ret_str,
                        'returns_raw': ret_raw,
                        'type': series_info.get('type')
                    }
                data['market_data'].append(asset_dict)

    return data
