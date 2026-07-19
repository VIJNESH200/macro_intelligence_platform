import os
import sys
import pandas as pd
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from config import CONFIG, MACRO_SERIES, MARKET_SERIES
from data.data_engine import DataEngine
from features.feature_engine import FeatureEngine
from research.report_data import extract_report_data
from analytics.cycle_statistics import compute_statistics
from analytics.insights import generate_insights
from analytics.market_insights import generate_market_insights
from research.narrative import generate_narrative
from analytics.historical_analogues import generate_analogues
from analytics.deltas import calculate_deltas
from analytics.transition_matrix import compute_transition_matrix
from analytics.forecasting_engine import ForecastingEngine
from analytics.scenario_engine import ScenarioEngine
from research.pdf import build_pdf_report
import matplotlib.pyplot as plt

def test_pdf():
    print("Testing PDF Generation...")
    
    # 1. Load Data
    engine = DataEngine(CONFIG, MARKET_SERIES, MACRO_SERIES)
    df = engine.load_all()
    df, _ = FeatureEngine.compute_all(df, CONFIG)
    
    idx = len(df) - 1
    
    # Fake plot_elements
    plot_elements = {
        'market_state': {'selected': list(MARKET_SERIES.keys())[:5]}
    }
    
    data = extract_report_data(df, CONFIG, plot_elements, idx, MARKET_SERIES)
    analysis = compute_statistics(df.iloc[:idx+1], data)
    insights = generate_insights(data, analysis)
    mkt_insights = generate_market_insights(data)
    analogues = generate_analogues(df, idx, data, MARKET_SERIES)
    
    # Phase 3
    trans_matrix = compute_transition_matrix(df.iloc[:idx+1])
    forecast_result = ForecastingEngine.project(df, idx, CONFIG, analogues, data.get('macro_contrib'))
    scenarios = ScenarioEngine.generate_scenarios(forecast_result, trans_matrix, analogues, data['quadrant'], CONFIG)
    
    data['transition_matrix'] = trans_matrix
    data['forecast'] = forecast_result
    data['scenarios'] = scenarios
    
    narr = generate_narrative(data, analysis, insights, mkt_insights, analogues)
    
    # Fake current_data dict for deltas
    deltas = calculate_deltas(df, idx, CONFIG, plot_elements, MARKET_SERIES, data, analysis, insights)
    
    # Fake fig
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    temp_fig = "temp_fig.png"
    fig.savefig(temp_fig)
    
    out_pdf = "test_report.pdf"
    build_pdf_report(data, analysis, insights, mkt_insights, narr, analogues, deltas, temp_fig, out_pdf)
    
    print("PDF successfully built at", out_pdf)
    
if __name__ == "__main__":
    test_pdf()
