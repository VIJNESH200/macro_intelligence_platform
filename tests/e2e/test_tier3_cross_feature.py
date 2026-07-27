import pytest
import pandas as pd
import numpy as np

pytestmark = pytest.mark.skip(reason="Milestone 3 feature un-implemented")

def test_cross_f1_f2_classification_to_alignment():
    """Test 1: F1 x F2. Ensure raw RRG inputs are classified into quadrants and then correctly aligned with month-end macro data."""
    from analytics.rrg import classify_rrg_quadrant
    from features.alignment import build_aligned_panel
    
    dates = pd.date_range(start='2020-01-01', periods=10, freq='W')
    raw_rrg = pd.DataFrame({'rs_ratio': np.random.randn(10), 'rs_momentum': np.random.randn(10)}, index=dates)
    macro_data = pd.DataFrame({'gdp': np.random.randn(3)}, index=pd.date_range(start='2020-01-01', periods=3, freq='ME'))
    
    quadrants = classify_rrg_quadrant(raw_rrg)
    aligned = build_aligned_panel(quadrants, macro_data)
    
    assert isinstance(aligned, pd.DataFrame)
    assert 'quadrant' in aligned.columns
    assert len(aligned) > 0

def test_cross_f1_f3_classification_to_validation():
    """Test 2: F1 x F3. Ensure classified RRG quadrants flow correctly into the descriptive validation gate."""
    from analytics.rrg import classify_rrg_quadrant
    from features.validation import descriptive_validation_gate
    
    raw_rrg = pd.DataFrame({'rs_ratio': [1.1, 0.9], 'rs_momentum': [1.1, 0.9]})
    quadrants = classify_rrg_quadrant(raw_rrg)
    
    result = descriptive_validation_gate(quadrants)
    assert isinstance(result, dict)
    assert 'passed' in result
    assert result['passed'] in [True, False]

def test_cross_f1_f4_classification_to_predictive_signal():
    """Test 3: F1 x F4. Classify RRG quadrants and feed them directly into predictive signal modeling."""
    from analytics.rrg import classify_rrg_quadrant
    from analytics.predictive import run_predictive_signal
    
    raw_rrg = pd.DataFrame({'rs_ratio': [1.1, 0.9], 'rs_momentum': [1.1, 0.9]})
    quadrants = classify_rrg_quadrant(raw_rrg)
    
    forward_returns = pd.Series([0.05, -0.02])
    signal_result = run_predictive_signal(quadrants, forward_returns)
    assert isinstance(signal_result, dict)
    assert 'signal' in signal_result

def test_cross_f1_f5_classification_to_export():
    """Test 4: F1 x F5. Check that the API can export RRG classification metadata."""
    from analytics.rrg import classify_rrg_quadrant
    from exports.api import export_api_result
    
    raw_rrg = pd.DataFrame({'rs_ratio': [1.1], 'rs_momentum': [1.1]})
    quadrants = classify_rrg_quadrant(raw_rrg)
    
    export_result = export_api_result(metadata={"rrg": quadrants})
    assert isinstance(export_result, dict)
    assert export_result.get('status') == 'success'
    assert 'metadata' in export_result

def test_cross_f2_f3_alignment_to_validation_missing_data():
    """Test 5: F2 x F3. Test misaligned dates or missing observations handled correctly."""
    from features.alignment import build_aligned_panel
    from features.validation import descriptive_validation_gate
    
    synthetic_quadrants = pd.DataFrame({'quadrant': ['Leading', 'Lagging']}, index=[pd.Timestamp('2020-01-01'), pd.Timestamp('2020-02-01')])
    macro_data = pd.DataFrame({'macro': [1.5, np.nan]}, index=[pd.Timestamp('2020-01-01'), pd.Timestamp('2020-02-01')])
    
    aligned = build_aligned_panel(synthetic_quadrants, macro_data)
    result = descriptive_validation_gate(aligned)
    
    assert isinstance(result, dict)
    assert 'passed' in result
    assert result['passed'] is False

def test_cross_f2_f4_alignment_to_predictive_signal_gaps():
    """Test 6: F2 x F4. Aligned panel with missing or NaN values affects held-out window split."""
    from features.alignment import build_aligned_panel
    from analytics.predictive import run_predictive_signal
    
    synthetic_quadrants = pd.DataFrame({'quadrant': ['Leading']*5}, index=pd.date_range('2020-01-01', periods=5, freq='ME'))
    macro_data = pd.DataFrame({'macro': [1, 2, np.nan, 4, 5]}, index=pd.date_range('2020-01-01', periods=5, freq='ME'))
    
    aligned = build_aligned_panel(synthetic_quadrants, macro_data)
    returns = pd.Series([1, -1, 1, -1, 1], index=pd.date_range('2020-01-01', periods=5, freq='ME'))
    signal_result = run_predictive_signal(aligned, returns)
    
    assert isinstance(signal_result, dict)
    assert 'metrics' in signal_result

def test_cross_f2_f5_alignment_to_export_serialization():
    """Test 7: F2 x F5. Export the aligned panel directly via the API to verify formatting."""
    from features.alignment import build_aligned_panel
    from exports.api import export_api_result
    
    synthetic_quadrants = pd.DataFrame({'quadrant': ['Leading']}, index=[pd.Timestamp('2020-01-01')])
    macro_data = pd.DataFrame({'macro': [1.0]}, index=[pd.Timestamp('2020-01-01')])
    
    aligned = build_aligned_panel(synthetic_quadrants, macro_data)
    export_result = export_api_result(data=aligned)
    
    assert isinstance(export_result, dict)
    assert 'data' in export_result

def test_cross_f3_f4_validation_gate_trigger():
    """Test 8: F3 x F4. Test interaction between decision gate and predictive signal."""
    from features.validation import descriptive_validation_gate
    from analytics.predictive import run_predictive_signal
    
    strong_data = pd.DataFrame({'quadrant': ['Leading']*50 + ['Lagging']*50, 'macro': [1]*50 + [-1]*50})
    
    res_strong = descriptive_validation_gate(strong_data)
    gate_passed = res_strong.get('passed', False)
    
    returns = pd.Series(np.random.randn(100))
    sig_strong = run_predictive_signal(strong_data, returns, gate_passed=gate_passed)
    
    assert isinstance(sig_strong, dict)
    assert 'signal' in sig_strong

def test_cross_f3_f5_validation_to_export_early_termination():
    """Test 9: F3 x F5. Failed gate correctly generates an API export indicating early termination."""
    from features.validation import descriptive_validation_gate
    from exports.api import export_api_result
    
    random_data = pd.DataFrame({'quadrant': ['Leading', 'Lagging'], 'macro': [1, -1]})
    res_fail = descriptive_validation_gate(random_data)
    
    export_result = export_api_result(validation_result=res_fail, early_termination=True)
    
    assert isinstance(export_result, dict)
    assert export_result.get('status') == 'terminated'

def test_cross_f4_f5_predictive_signal_to_export():
    """Test 10: F4 x F5. Full predictive signal results serialized into SectorRotationResult API export."""
    from analytics.predictive import run_predictive_signal
    from exports.api import export_api_result
    
    aligned_data = pd.DataFrame({'quadrant': ['Leading']*10, 'macro': [1]*10})
    returns = pd.Series([0.1]*10)
    
    signal_result = run_predictive_signal(aligned_data, returns)
    export_result = export_api_result(signal_result=signal_result)
    
    assert isinstance(export_result, dict)
    assert 'signal_result' in export_result
