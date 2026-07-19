"""
Historical Analogues — Euclidean distance-based analogue matching.
==================================================================
Port of report_analogues.py with bug fix:
get_quadrant() now accepts center parameter for future flexibility.
"""
import numpy as np
import pandas as pd


def get_quadrant(x: float, y: float, center: float = 100) -> str:
    """Assign quadrant based on X (health) and Y (momentum) relative to center.

    BUG FIX: The original used hardcoded 100 for X and 0 for Y thresholds.
    Now uses the same center-relative logic as the main FeatureEngine.
    """
    if x >= center and y >= center:
        return "Expansion"
    if x >= center and y < center:
        return "Slowdown"
    if x < center and y < center:
        return "Contraction"
    return "Recovery"


def generate_analogues(df, current_idx: int, data: dict,
                       market_series_config: dict,
                       center: float = 100) -> dict:
    """Find the top-3 most statistically similar historical macro environments.

    Uses Euclidean distance across normalized health (X) and momentum (Y) vectors.
    """
    x_curr = df['X'].iloc[current_idx]
    y_curr = df['Y'].iloc[current_idx]
    quad_curr = get_quadrant(x_curr, y_curr, center)

    historical_phases = []
    current_phase_start = current_idx

    # Find start of current phase
    for i in range(current_idx, -1, -1):
        if get_quadrant(df['X'].iloc[i], df['Y'].iloc[i], center) != quad_curr:
            break
        current_phase_start = i

    start_i = 0
    while start_i < current_phase_start:
        q = get_quadrant(df['X'].iloc[start_i], df['Y'].iloc[start_i], center)
        if q == quad_curr:
            # Find end of this phase
            end_i = start_i
            while (end_i < current_phase_start and
                   get_quadrant(df['X'].iloc[end_i], df['Y'].iloc[end_i], center) == quad_curr):
                end_i += 1
            end_i -= 1

            # Find point of maximum similarity
            min_dist = float('inf')
            best_idx = start_i

            for j in range(start_i, end_i + 1):
                xy_dist = np.sqrt((df['X'].iloc[j] - x_curr)**2 + (df['Y'].iloc[j] - y_curr)**2)
                
                macro_dist = 0.0
                valid_macro = 0
                macro_cols = [c for c in df.columns if str(c).endswith('_Z')]
                for mc in macro_cols:
                    val_curr = df[mc].iloc[current_idx]
                    val_hist = df[mc].iloc[j]
                    if not pd.isna(val_curr) and not pd.isna(val_hist):
                        macro_dist += (val_curr - val_hist)**2
                        valid_macro += 1
                
                if valid_macro > 0:
                    macro_dist = np.sqrt(macro_dist / valid_macro)
                    try:
                        from ..config import FORECAST_CONFIG
                        w_xy = FORECAST_CONFIG['analogue_similarity_weights']['xy']
                        w_macro = FORECAST_CONFIG['analogue_similarity_weights']['macro']
                    except ImportError:
                        try:
                            from config import FORECAST_CONFIG
                            w_xy = FORECAST_CONFIG['analogue_similarity_weights']['xy']
                            w_macro = FORECAST_CONFIG['analogue_similarity_weights']['macro']
                        except ImportError:
                            w_xy, w_macro = 0.6, 0.4
                    dist = w_xy * xy_dist + w_macro * macro_dist
                else:
                    dist = xy_dist

                if dist < min_dist:
                    min_dist = dist
                    best_idx = j

            next_phase = "N/A"
            if end_i + 1 <= current_idx:
                next_phase = get_quadrant(
                    df['X'].iloc[end_i + 1], df['Y'].iloc[end_i + 1], center
                )

            historical_phases.append({
                'best_idx': best_idx,
                'min_dist': min_dist,
                'duration': end_i - start_i + 1,
                'next_phase': next_phase,
                'date': df.iloc[best_idx].name
            })
            start_i = end_i + 1
        else:
            start_i += 1

    historical_phases.sort(key=lambda x: x['min_dist'])
    top_3 = historical_phases[:3]

    results = []

    benchmark_name = None
    for name in market_series_config.keys():
        if 'Nifty' in name or 'Sensex' in name or 'S&P' in name:
            benchmark_name = name
            break

    if not benchmark_name and market_series_config:
        benchmark_name = list(market_series_config.keys())[0]

    for p in top_3:
        # Heuristic mapping for similarity score: 0 distance = 100%
        sim = max(0, min(100, 100 - (p['min_dist'] * 15)))

        fwd_ret = "N/A"
        fwd_ret_val = np.nan
        if benchmark_name:
            future_idx = p['best_idx'] + 6
            if future_idx < len(df):
                try:
                    val_now = df[benchmark_name].iloc[p['best_idx']]
                    val_fut = df[benchmark_name].iloc[future_idx]
                    if not pd.isna(val_now) and not pd.isna(val_fut) and val_now != 0:
                        ret = (val_fut - val_now) / val_now * 100
                        fwd_ret_val = ret
                        sign = '+' if ret > 0 else ''
                        fwd_ret = f"{sign}{ret:.1f}%"
                except (IndexError, KeyError):
                    pass

        results.append({
            'date_str': p['date'].strftime('%b %Y'),
            'similarity_score': sim,
            'similarity_str': f"{sim:.0f}%",
            'duration': f"{p['duration']} months",
            'next_phase': p['next_phase'],
            'benchmark_name': benchmark_name if benchmark_name else 'Benchmark',
            'fwd_ret': fwd_ret,
            'fwd_ret_val': fwd_ret_val
        })

    if not results:
        return {'matches': [], 'averages': None}

    avg_sim = sum(r['similarity_score'] for r in results) / len(results)
    avg_dur = sum(int(r['duration'].split(' ')[0]) for r in results) / len(results)

    valid_fwd = [r['fwd_ret_val'] for r in results if not pd.isna(r['fwd_ret_val'])]
    avg_fwd = sum(valid_fwd) / len(valid_fwd) if valid_fwd else np.nan
    avg_fwd_str = f"{'+' if avg_fwd > 0 else ''}{avg_fwd:.1f}%" if not pd.isna(avg_fwd) else "N/A"

    next_phases = [r['next_phase'] for r in results if r['next_phase'] != "N/A"]
    most_common = max(set(next_phases), key=next_phases.count) if next_phases else "N/A"

    averages = {
        'avg_sim_str': f"{avg_sim:.0f}%",
        'avg_dur_str': f"{avg_dur:.0f} months",
        'most_common_next': most_common,
        'avg_fwd_str': avg_fwd_str,
        'avg_fwd_val': avg_fwd
    }

    return {'matches': results, 'averages': averages}
