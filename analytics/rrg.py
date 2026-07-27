import pandas as pd
import numpy as np

def classify_rrg_quadrant(rs_ratio: float, rs_momentum: float) -> str:
    """
    Classify the RRG quadrant based on RS-Ratio and RS-Momentum.
    
    Quadrants:
    - Leading: RS-Ratio >= 100 and RS-Momentum >= 100
    - Weakening: RS-Ratio >= 100 and RS-Momentum < 100
    - Lagging: RS-Ratio < 100 and RS-Momentum < 100
    - Improving: RS-Ratio < 100 and RS-Momentum >= 100
    """
    if pd.isna(rs_ratio) or pd.isna(rs_momentum):
        return 'Unknown'
        
    if rs_ratio >= 100:
        if rs_momentum >= 100:
            return 'Leading'
        else:
            return 'Weakening'
    else:
        if rs_momentum >= 100:
            return 'Improving'
        else:
            return 'Lagging'


def build_aligned_panel(df: pd.DataFrame) -> pd.DataFrame:
    """
    Resample a weekly pandas DataFrame to month-end.
    
    Args:
        df (pd.DataFrame): DataFrame with a DatetimeIndex representing weekly data.
        
    Returns:
        pd.DataFrame: DataFrame resampled to month-end.
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("DataFrame index must be a DatetimeIndex")
        
    # Pandas 2.2+ uses 'ME' for month-end, older versions use 'M'
    try:
        return df.resample('ME').last()
    except ValueError:
        return df.resample('M').last()
