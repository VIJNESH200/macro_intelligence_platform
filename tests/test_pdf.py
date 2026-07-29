from __future__ import annotations
import os
import sys
import unittest
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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


class TestPDF(unittest.TestCase):
    def setUp(self):
        self.temp_fig = "temp_test_pdf_fig.png"
        self.out_pdf = "temp_test_pdf_report.pdf"

    def tearDown(self):
        if os.path.exists(self.temp_fig):
            os.remove(self.temp_fig)
        if os.path.exists(self.out_pdf):
            os.remove(self.out_pdf)

    def test_full_pdf_generation(self):
        engine = DataEngine(CONFIG, MARKET_SERIES, MACRO_SERIES, offline=True)
        df = engine.load_all()
        df, _ = FeatureEngine.compute_all(df, CONFIG)

        idx = len(df) - 1
        plot_elements = {
            'market_state': {'selected': list(MARKET_SERIES.keys())[:5]}
        }

        data = extract_report_data(df, CONFIG, plot_elements, idx, MARKET_SERIES)
        analysis = compute_statistics(df.iloc[:idx+1], data)
        insights = generate_insights(data, analysis)
        mkt_insights = generate_market_insights(data)
        analogues = generate_analogues(df, idx, data, MARKET_SERIES)

        trans_matrix = compute_transition_matrix(df.iloc[:idx+1])
        forecast_result = ForecastingEngine.project(df, idx, CONFIG, analogues, data.get('macro_contrib'))
        scenarios = ScenarioEngine.generate_scenarios(forecast_result, trans_matrix, analogues, data['quadrant'], CONFIG)

        data['transition_matrix'] = trans_matrix
        data['forecast'] = forecast_result
        data['scenarios'] = scenarios

        narr = generate_narrative(data, analysis, insights, mkt_insights, analogues)
        deltas = calculate_deltas(df, idx, CONFIG, plot_elements, MARKET_SERIES, data, analysis, insights)

        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1])
        fig.savefig(self.temp_fig)
        plt.close(fig)

        metadata = engine.get_metadata
        build_pdf_report(data, analysis, insights, mkt_insights, narr, analogues, deltas, self.temp_fig, self.out_pdf, data_metadata=metadata)

        self.assertTrue(os.path.exists(self.out_pdf))
        self.assertGreater(os.path.getsize(self.out_pdf), 0)


if __name__ == "__main__":
    unittest.main()
