import pytest
import pandas as pd
import numpy as np

pytestmark = pytest.mark.skip(reason="Milestone 3 feature un-implemented")

try:
    from core_api import sector_rotation_signal, SectorRotationResult
    from exports import export_to_notebook, export_to_json
except ImportError:
    pass

def generate_synthetic_data(noise_level=0.1, missing_pct=0.0, predictive_valid=True):
    # Generating mock data over 100 days
    dates = pd.date_range(start="2020-01-01", periods=100, freq='B')
    
    # Macro Data
    macro_data = {
        'date': dates,
        'macro_X': np.random.randn(100),
        'macro_Y': np.random.randn(100)
    }
    macro_df = pd.DataFrame(macro_data).set_index('date')
    
    # Sector Data (e.g. Technology)
    # If not noise, we make JdK values dependent on macro
    if noise_level < 0.5:
        rs_ratio = macro_df['macro_X'] * 2 + np.random.randn(100) * noise_level
        rs_momentum = macro_df['macro_Y'] * 2 + np.random.randn(100) * noise_level
    else:
        rs_ratio = np.random.randn(100)
        rs_momentum = np.random.randn(100)
        
    if predictive_valid:
        # forward return dependent on current RS ratio
        forward_returns = rs_ratio * 0.05 + np.random.randn(100) * 0.01
    else:
        forward_returns = np.random.randn(100) * 0.05
        
    sector_data = {
        'date': dates,
        'JdK_RS_Ratio': rs_ratio,
        'JdK_RS_Momentum': rs_momentum,
        'forward_return': forward_returns
    }
    sector_df = pd.DataFrame(sector_data).set_index('date')
    
    # Inject missing values
    if missing_pct > 0:
        mask = np.random.rand(*sector_df.shape) < missing_pct
        sector_df[mask] = np.nan
        
    return macro_df, sector_df

def test_full_pipeline_success(tmp_path):
    """Scenario 1: Full pipeline from raw data to API result (Features: F1, F2, F3, F4, F5)"""
    macro_df, sector_df = generate_synthetic_data(noise_level=0.1, missing_pct=0.0, predictive_valid=True)
    
    result = sector_rotation_signal(macro_df, sector_df)
    
    assert isinstance(result, SectorRotationResult)
    assert result.descriptive_passed is True
    assert result.predictive_passed is True
    assert result.chi_square_p_value <= 0.05
    assert result.dm_test_p_value <= 0.05

    json_path = tmp_path / "test_output.json"
    export_to_json(result, json_path)
    assert json_path.exists()
    
    nb_path = tmp_path / "test_output.ipynb"
    export_to_notebook(result, nb_path)
    assert nb_path.exists()

def test_early_termination_descriptive_gate():
    """Scenario 2: Early termination at descriptive validation gate (Features: F1, F2, F3)"""
    macro_df, sector_df = generate_synthetic_data(noise_level=1.0, missing_pct=0.0, predictive_valid=False)
    
    result = sector_rotation_signal(macro_df, sector_df)
    
    assert isinstance(result, SectorRotationResult)
    assert result.descriptive_passed is False
    assert result.predictive_passed is None
    assert result.chi_square_p_value > 0.05

def test_missing_observations_contingency():
    """Scenario 3: Missing observations flagged in contingency (Features: F2, F3)"""
    macro_df, sector_df = generate_synthetic_data(noise_level=0.1, missing_pct=0.1, predictive_valid=True)
    
    orig_len = len(sector_df)
    
    result = sector_rotation_signal(macro_df, sector_df)
    
    assert isinstance(result, SectorRotationResult)
    # Result should still proceed, but aligned panel should drop NaNs
    assert result.aligned_panel is not None
    assert len(result.aligned_panel) < orig_len
    # Expect the pipeline to handle this gracefully and output a signal
    assert result.descriptive_passed is not None

def test_failing_predictive_signal():
    """Scenario 4: Synthetic failing predictive signal (Features: F4)"""
    macro_df, sector_df = generate_synthetic_data(noise_level=0.1, missing_pct=0.0, predictive_valid=False)
    
    result = sector_rotation_signal(macro_df, sector_df)
    
    assert isinstance(result, SectorRotationResult)
    assert result.descriptive_passed is True
    assert result.predictive_passed is False
    assert result.dm_test_p_value > 0.05

def test_successful_signal_with_notebook(tmp_path):
    """Scenario 5: Successful predictive signal with notebook (Features: F4, F5)"""
    macro_df, sector_df = generate_synthetic_data(noise_level=0.1, missing_pct=0.0, predictive_valid=True)
    
    result = sector_rotation_signal(macro_df, sector_df)
    
    assert isinstance(result, SectorRotationResult)
    assert result.descriptive_passed is True
    assert result.predictive_passed is True
    
    json_path = tmp_path / "test_output.json"
    export_to_json(result, json_path)
    assert json_path.exists()
    
    nb_path = tmp_path / "test_output.ipynb"
    export_to_notebook(result, nb_path)
    assert nb_path.exists()
