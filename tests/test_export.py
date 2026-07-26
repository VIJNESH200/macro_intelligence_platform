from __future__ import annotations
import os
import sys
import unittest
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data.data_engine import DataEngine
from features.feature_engine import FeatureEngine
from analytics.macro_intelligence_engine import MacroIntelligenceEngine
from config import CONFIG, MARKET_SERIES, MACRO_SERIES
from research.pdf import build_pdf_report


class TestExport(unittest.TestCase):
    def setUp(self):
        self.temp_fig = "temp_test_export_fig.png"
        self.out_pdf = "temp_test_export_report.pdf"

    def tearDown(self):
        if os.path.exists(self.temp_fig):
            os.remove(self.temp_fig)
        if os.path.exists(self.out_pdf):
            os.remove(self.out_pdf)

    def test_pdf_export_pipeline(self):
        engine = DataEngine(CONFIG, MARKET_SERIES, MACRO_SERIES, offline=True)
        df = engine.load_all()
        df, spline_data = FeatureEngine.compute_all(df, CONFIG)

        idx = len(df.dropna()) - 1 if len(df.dropna()) > 0 else len(df) - 1
        res = MacroIntelligenceEngine.assign_contribution(df, idx)
        macro_contrib = {
            'all_drivers': res['all_drivers'],
            'macro_score': res['macro_score'],
            'rationale': res['confidence_rationale'],
            'confidence_score': res['confidence_score'],
            'confidence_rationale': res['confidence_rationale'],
            'macro_interpretation': res['macro_interpretation']
        }

        data = {
            'indicator': CONFIG['name'],
            'date': datetime.now().strftime('%B %Y'),
            'source': CONFIG['source'],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'window': f"{CONFIG['window']}-Month Rolling",
            'quadrant': 'Expansion',
            'macro_contrib': macro_contrib,
            'market_data': [],
            'transition_matrix': None,
            'forecast': None,
            'scenarios': []
        }

        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1])
        fig.savefig(self.temp_fig)
        plt.close(fig)

        build_pdf_report(
            data=data,
            analysis={},
            insights={'phase': 'Expansion', 'direction': 'Up', 'health_above_trend': True, 'momentum_above_trend': True, 'market_resilient': True, 'highest_transition': 'N/A', 'highest_transition_prob': 0.0, 'completion_pct': 0.0, 'highest_trans': 'Slowdown', 'highest_trans_prob': 0.0},
            market_insights={},
            narrative={'executive_summary': 'test', 'takeaways': [], 'interpretation': 'test', 'risks': [], 'methodology': 'test'},
            analogues={},
            deltas=[],
            chart_path=self.temp_fig,
            output_path=self.out_pdf,
            data_metadata=engine.get_metadata
        )

        self.assertTrue(os.path.exists(self.out_pdf))
        self.assertGreater(os.path.getsize(self.out_pdf), 0)


if __name__ == '__main__':
    unittest.main()
