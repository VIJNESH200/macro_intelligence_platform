import pandas as pd
from scipy.stats import chi2_contingency

def _compute_chi2_metrics(df: pd.DataFrame):
    if df.empty:
        return 0, 1.0, True
    N = len(df)
    if 'regime' not in df.columns or 'rrg_quadrant' not in df.columns:
        return N, 1.0, True
    
    table = pd.crosstab(df['regime'], df['rrg_quadrant'])
    low_observation_flag = bool(table.values.min() < 10) if table.size > 0 else True
    
    if table.shape[0] < 2 or table.shape[1] < 2:
        p_value = 1.0
    else:
        _, p_value, _, _ = chi2_contingency(table)
    
    return N, float(p_value), low_observation_flag

def validate_descriptive_signal(panel: pd.DataFrame) -> dict:
    if panel.empty:
        return {"N": 0, "p_value": 1.0, "passed_gate": False, "low_observation_flag": True, "sectors": {}}
        
    N_pooled, p_value_pooled, low_obs_pooled = _compute_chi2_metrics(panel)
    passed_gate = bool(p_value_pooled < 0.05)
    
    result = {
        "N": N_pooled,
        "p_value": p_value_pooled,
        "passed_gate": passed_gate,
        "low_observation_flag": low_obs_pooled,
        "sectors": {}
    }
    
    if 'sector' in panel.columns:
        sectors = panel['sector'].unique()
        num_tests = len(sectors)
        
        for sector in sectors:
            sector_df = panel[panel['sector'] == sector]
            s_N, s_p_value, s_low_obs = _compute_chi2_metrics(sector_df)
            
            # Manual Bonferroni correction
            adj_p_value = min(1.0, s_p_value * num_tests)
            
            result["sectors"][sector] = {
                "N": s_N,
                "p_value": s_p_value,
                "adjusted_p_value": adj_p_value,
                "low_observation_flag": s_low_obs
            }
            
    return result

def test_predictive_signal(panel, split_year, passed_gate):
    raise NotImplementedError("Milestone 3")
