import pytest
import pandas as pd
import numpy as np

from integrations.rrg.rrg import calculate_rrg_metrics
from analytics.rrg import classify_rrg_quadrant, build_aligned_panel

def test_calculate_rrg_metrics():
    dates = pd.date_range(start='2020-01-01', periods=30, freq='D')
    asset = pd.Series(np.linspace(100, 150, 30), index=dates)
    benchmark = pd.Series(np.linspace(100, 120, 30), index=dates)
    
    df = calculate_rrg_metrics(asset, benchmark, window=5)
    
    assert isinstance(df, pd.DataFrame)
    assert 'rs_ratio' in df.columns
    assert 'rs_momentum' in df.columns
    
    # Valid values should exist
    assert not df['rs_ratio'].dropna().empty
    assert not df['rs_momentum'].dropna().empty

def test_classify_rrg_quadrant():
    assert classify_rrg_quadrant(105, 105) == 'Leading'
    assert classify_rrg_quadrant(105, 95) == 'Weakening'
    assert classify_rrg_quadrant(95, 95) == 'Lagging'
    assert classify_rrg_quadrant(95, 105) == 'Improving'
    
    # Boundary cases
    assert classify_rrg_quadrant(100, 100) == 'Leading'
    
    # NaN cases
    assert classify_rrg_quadrant(np.nan, 105) == 'Unknown'

def test_build_aligned_panel():
    # Use weekly data (Friday)
    dates = pd.date_range(start='2023-01-01', end='2023-03-31', freq='W-FRI')
    df = pd.DataFrame({'value': range(len(dates))}, index=dates)
    
    monthly_df = build_aligned_panel(df)
    
    # Output should have 3 month-end dates
    assert len(monthly_df) == 3
    assert monthly_df.index.month.tolist() == [1, 2, 3]

def test_build_aligned_panel_invalid_index():
    df = pd.DataFrame({'value': [1, 2, 3]})
    with pytest.raises(ValueError):
        build_aligned_panel(df)
