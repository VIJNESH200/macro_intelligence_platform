from __future__ import annotations
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import CONFIG, MACRO_SERIES, MARKET_SERIES, reload_for_market
from data.data_engine import DataEngine
from features.feature_engine import FeatureEngine
from analytics.macro_intelligence_engine import MacroIntelligenceEngine


class TestIndicators(unittest.TestCase):
    def test_indicator_pipeline(self):
        # Pinned to INDIA explicitly: this test asserts on India-only fields
        # like 'ICI', and the active market is mutable global state that the
        # market-toggle feature can flip to 'US'. reload_for_market() (rather
        # than building an independent config dict) matches how main.py
        # actually switches markets: FeatureEngine.compute_macro_features
        # reads MACRO_SERIES from the config module directly, so the global
        # state must be synchronized for the computed driver features (e.g.
        # ICI_Z) to appear, even though DataEngine itself takes its
        # market_series/macro_series as explicit arguments.
        reload_for_market('INDIA')

        engine = DataEngine(CONFIG, MARKET_SERIES, MACRO_SERIES, offline=True)
        df = engine.load_all()
        self.assertGreater(len(df), 0)

        df, spline_data = FeatureEngine.compute_all(df, CONFIG)
        self.assertIn('X', df.columns)
        self.assertIn('Y', df.columns)

        idx = len(df) - 1
        evals = MacroIntelligenceEngine.evaluate_indicators(df, idx)
        self.assertIsInstance(evals, dict)
        self.assertIn('ICI', evals)

        contrib = MacroIntelligenceEngine.assign_contribution(df, idx)
        self.assertIn('macro_score', contrib)
        self.assertIsInstance(contrib['macro_score'], float)

        shifts = MacroIntelligenceEngine.detect_regime_shifts(df, idx)
        self.assertIsInstance(shifts, list)


if __name__ == "__main__":
    unittest.main()
