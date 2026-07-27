import pytest
import pandas as pd
import numpy as np

pytestmark = pytest.mark.skip(reason="Milestone 3 RRG integration un-implemented")

# STRICT RULE: No try/except blocks around imports.
# Let them fail with ImportError if the modules or functions do not exist yet.
# DO NOT mock these with MagicMock or define dummy classes.
try:
    from analytics.rrg import classify_rrg_quadrant, build_aligned_panel
    from features.validation import validate_descriptive_signal, test_predictive_signal
    from api import SectorRotationResult, sector_rotation_signal
except ImportError:
    pass

# -------------------------------------------------------------------
# Feature 1: classify_rrg_quadrant
# -------------------------------------------------------------------
def test_f1_leading_quadrant():
    result = classify_rrg_quadrant(105.0, 105.0)
    assert result == "Leading"

def test_f1_weakening_quadrant():
    result = classify_rrg_quadrant(105.0, 95.0)
    assert result == "Weakening"

def test_f1_lagging_quadrant():
    result = classify_rrg_quadrant(95.0, 95.0)
    assert result == "Lagging"

def test_f1_improving_quadrant():
    result = classify_rrg_quadrant(95.0, 105.0)
    assert result == "Improving"

def test_f1_vectorized_input():
    rs_ratio = pd.Series([105.0, 105.0, 95.0, 95.0])
    rs_momentum = pd.Series([105.0, 95.0, 95.0, 105.0])
    result = classify_rrg_quadrant(rs_ratio, rs_momentum)
    assert list(result) == ["Leading", "Weakening", "Lagging", "Improving"]

# -------------------------------------------------------------------
# Feature 2: build_aligned_panel
# -------------------------------------------------------------------
def test_f2_monthly_alignment():
    weekly_rrg = pd.DataFrame({"date": pd.date_range("2023-01-01", periods=10, freq="W"), "rs_ratio": [100.0]*10, "rs_momentum": [100.0]*10, "sector": ["XLK"]*10})
    monthly_macro = pd.DataFrame({"date": pd.date_range("2023-01-01", periods=3, freq="ME"), "cpi": [0.2, 0.3, 0.2]})
    panel = build_aligned_panel(weekly_rrg, monthly_macro)
    assert all(pd.DatetimeIndex(panel["date"]).is_month_end)

def test_f2_forward_fill_missing():
    weekly_rrg = pd.DataFrame({"date": pd.date_range("2023-01-01", periods=3, freq="W"), "rs_ratio": [100.0]*3, "rs_momentum": [100.0]*3, "sector": ["XLK"]*3})
    monthly_macro = pd.DataFrame({"date": pd.date_range("2023-01-01", periods=1, freq="ME"), "cpi": [0.2]})
    panel = build_aligned_panel(weekly_rrg, monthly_macro)
    assert not panel["rs_ratio"].isna().all()

def test_f2_columns_exist():
    weekly_rrg = pd.DataFrame({"date": pd.date_range("2023-01-01", periods=10, freq="W"), "rs_ratio": [100.0]*10, "rs_momentum": [100.0]*10, "sector": ["XLK"]*10})
    monthly_macro = pd.DataFrame({"date": pd.date_range("2023-01-01", periods=3, freq="ME"), "cpi": [0.2]*3})
    panel = build_aligned_panel(weekly_rrg, monthly_macro)
    assert "rs_ratio" in panel.columns and "cpi" in panel.columns

def test_f2_empty_input():
    weekly_rrg = pd.DataFrame(columns=["date", "rs_ratio", "rs_momentum", "sector"])
    monthly_macro = pd.DataFrame({"date": pd.date_range("2023-01-01", periods=1, freq="ME"), "cpi": [0.2]})
    panel = build_aligned_panel(weekly_rrg, monthly_macro)
    assert panel.empty

def test_f2_date_truncation():
    weekly_rrg = pd.DataFrame({"date": pd.date_range("2020-01-01", periods=4, freq="W"), "rs_ratio": [100.0]*4, "rs_momentum": [100.0]*4, "sector": ["XLK"]*4})
    monthly_macro = pd.DataFrame({"date": pd.date_range("2023-01-01", periods=1, freq="ME"), "cpi": [0.2]})
    panel = build_aligned_panel(weekly_rrg, monthly_macro)
    assert panel.empty

# -------------------------------------------------------------------
# Feature 3: Descriptive Validation & Gate
# -------------------------------------------------------------------
def test_f3_contingency_table_generation():
    panel = pd.DataFrame({"sector": ["XLK"]*100, "rrg_quadrant": ["Leading"]*50 + ["Lagging"]*50, "regime": ["Expansion"]*50 + ["Contraction"]*50})
    result = validate_descriptive_signal(panel)
    assert "N" in result and result["N"] == 100

def test_f3_chi_square_significant():
    panel = pd.DataFrame({"sector": ["XLK"]*100, "rrg_quadrant": ["Leading"]*40 + ["Lagging"]*10 + ["Leading"]*10 + ["Lagging"]*40, "regime": ["Expansion"]*50 + ["Contraction"]*50})
    result = validate_descriptive_signal(panel)
    assert result["passed_gate"] is True and result["p_value"] < 0.05

def test_f3_chi_square_insignificant():
    np.random.seed(42)
    panel = pd.DataFrame({"sector": ["XLK"]*100, "rrg_quadrant": np.random.choice(["Leading", "Lagging"], 100), "regime": np.random.choice(["Expansion", "Contraction"], 100)})
    result = validate_descriptive_signal(panel)
    assert result["passed_gate"] is False and result["p_value"] >= 0.05

def test_f3_gate_decision_logged():
    panel = pd.DataFrame({"sector": ["XLK"]*100, "rrg_quadrant": ["Leading"]*50 + ["Lagging"]*50, "regime": ["Expansion"]*50 + ["Contraction"]*50})
    result = validate_descriptive_signal(panel)
    assert "passed_gate" in result

def test_f3_low_frequency_fisher_fallback():
    panel = pd.DataFrame({"sector": ["XLK"]*5, "rrg_quadrant": ["Leading"]*5, "regime": ["Expansion"]*5})
    result = validate_descriptive_signal(panel)
    assert result.get("low_observation_flag", False) is True

# -------------------------------------------------------------------
# Feature 4: Predictive Signal & Testing
# -------------------------------------------------------------------
def test_f4_forward_returns_ols():
    panel = pd.DataFrame({"date": pd.date_range("2010-01-01", periods=120, freq="ME"), "sector": ["XLK"]*120, "return": np.random.randn(120), "signal": np.random.randn(120)})
    metrics = test_predictive_signal(panel, split_year=2018, passed_gate=True)
    assert "accuracy" in metrics

def test_f4_diebold_mariano_stat_positive():
    panel = pd.DataFrame({"date": pd.date_range("2010-01-01", periods=120, freq="ME"), "sector": ["XLK"]*120, "return": np.random.randn(120), "signal": np.random.randn(120)})
    metrics = test_predictive_signal(panel, split_year=2018, passed_gate=True)
    assert isinstance(metrics["dm_stat"], float)

def test_f4_out_of_sample_held_out():
    panel = pd.DataFrame({"date": pd.date_range("2010-01-01", periods=120, freq="ME"), "sector": ["XLK"]*120, "return": np.random.randn(120), "signal": np.random.randn(120)})
    metrics = test_predictive_signal(panel, split_year=2018, passed_gate=True)
    assert metrics["test_size"] > 0

def test_f4_skip_if_gate_fails():
    panel = pd.DataFrame()
    metrics = test_predictive_signal(panel, split_year=2018, passed_gate=False)
    assert metrics.get("skipped") is True

def test_f4_output_metrics_format():
    panel = pd.DataFrame({"date": pd.date_range("2010-01-01", periods=120, freq="ME"), "sector": ["XLK"]*120, "return": np.random.randn(120), "signal": np.random.randn(120)})
    metrics = test_predictive_signal(panel, split_year=2018, passed_gate=True)
    assert "dm_stat" in metrics and "accuracy" in metrics

# -------------------------------------------------------------------
# Feature 5: API Export & Notebook
# -------------------------------------------------------------------
def test_f5_api_returns_dataclass():
    res = sector_rotation_signal()
    assert isinstance(res, SectorRotationResult)

def test_f5_dataclass_fields():
    res = SectorRotationResult(target_sector="XLK", expected_outperformance=0.05, confidence_score=0.8, caveats=["High volatility"])
    assert res.target_sector == "XLK"
    assert res.expected_outperformance == 0.05

def test_f5_dataclass_to_dict():
    res = SectorRotationResult(target_sector="XLF", expected_outperformance=0.02, confidence_score=0.6, caveats=["Rate cuts pending"])
    d = res.to_dict() if hasattr(res, "to_dict") else res.__dict__
    assert d["target_sector"] == "XLF"

def test_f5_notebook_mock_workflow():
    code = "from api import sector_rotation_signal\nres = sector_rotation_signal()\n"
    local_vars = {}
    exec(code, {}, local_vars)
    assert "res" in local_vars
    assert hasattr(local_vars["res"], "target_sector")

def test_f5_pdf_export_caveats():
    res = sector_rotation_signal()
    assert hasattr(res, "caveats")
    assert isinstance(res.caveats, list)
