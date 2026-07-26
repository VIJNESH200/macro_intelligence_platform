from __future__ import annotations
import unittest
import os
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from features.feature_engine import FeatureEngine
from analytics.forecasting_engine import ForecastingEngine
from config import CONFIG


class TestPureMathEngine(unittest.TestCase):
    """Unit tests for stateless pure mathematical calculations and logic."""

    def test_compute_health_and_momentum_zscores(self):
        """Test Z-score calculation for health (X) and momentum (Y)."""
        series = pd.Series([100.0, 102.0, 101.0, 103.0, 104.0, 102.0, 105.0] * 6)
        x = FeatureEngine.compute_health(series, window=36, center=100)
        y = FeatureEngine.compute_momentum(series, window=36, center=100)

        self.assertEqual(len(x), len(series))
        self.assertEqual(len(y), len(series))
        # First 35 values should be NaN due to min_periods=36
        self.assertTrue(x.iloc[:35].isna().all())
        self.assertFalse(pd.isna(x.iloc[-1]))
        self.assertFalse(pd.isna(y.iloc[-1]))

    def test_rolling_std_zero_division_guard(self):
        """Test that constant series with 0 rolling std does not cause division by zero or Inf."""
        constant_series = pd.Series([100.0] * 40)
        x = FeatureEngine.compute_health(constant_series, window=36, center=100)
        
        # When std is 0, (series - mean) / std should return NaN (guarded by replace(0, np.nan))
        # center + NaN = NaN
        last_val = x.iloc[-1]
        self.assertTrue(pd.isna(last_val))
        self.assertFalse(np.isinf(last_val))

    def test_quadrant_boundary_classification(self):
        """Test strict boundary classification into 4 quadrants."""
        center = 100.0
        
        # Expansion: X >= 100, Y >= 100
        self.assertEqual(ForecastingEngine._get_quadrant(101.5, 102.0, center), 'Expansion')
        self.assertEqual(ForecastingEngine._get_quadrant(100.0, 100.0, center), 'Expansion')
        
        # Slowdown: X >= 100, Y < 100
        self.assertEqual(ForecastingEngine._get_quadrant(101.5, 98.5, center), 'Slowdown')
        
        # Contraction: X < 100, Y < 100
        self.assertEqual(ForecastingEngine._get_quadrant(98.0, 97.5, center), 'Contraction')
        
        # Recovery: X < 100, Y >= 100
        self.assertEqual(ForecastingEngine._get_quadrant(98.0, 101.2, center), 'Recovery')

    def test_spline_interpolation_shape(self):
        """Test cubic spline interpolation generation for smooth trajectory trails."""
        dates = pd.date_range(start='2020-01-01', periods=10, freq='MS')
        df = pd.DataFrame({
            'X': [100, 101, 102, 101, 100, 99, 98, 99, 100, 101],
            'Y': [100, 102, 101, 99, 98, 97, 99, 101, 102, 103]
        }, index=dates)

        spline_df = FeatureEngine.compute_spline(df, CONFIG)
        
        self.assertIn('X', spline_df.columns)
        self.assertIn('Y', spline_df.columns)
        self.assertGreater(len(spline_df), len(df))
        # Total points = (len - 1) * points_per_segment + 1 = 9 * 10 + 1 = 91
        self.assertEqual(len(spline_df), 91)

    def test_conviction_score_calibration(self):
        """Test conviction score calibration scaling with signal agreement."""
        center = 100.0
        horizon = 6

        # Unanimous agreement: all 3 signals project Expansion
        c_unanimous = ForecastingEngine._compute_conviction(
            (102, 102), (103, 101), (101, 104), center, None, None, horizon
        )

        # Majority agreement: 2 project Expansion, 1 projects Slowdown
        c_majority = ForecastingEngine._compute_conviction(
            (102, 102), (103, 101), (101, 98), center, None, None, horizon
        )

        # Split signals: 1 Expansion, 1 Slowdown, 1 Contraction
        c_split = ForecastingEngine._compute_conviction(
            (102, 102), (101, 98), (98, 97), center, None, None, horizon
        )

        self.assertGreater(c_unanimous, c_majority)
        self.assertGreater(c_majority, c_split)
        self.assertTrue(15.0 <= c_split <= 95.0)


    def test_macro_driver_signal_with_real_evaluations_dict(self):
        """Verify _macro_driver_signal produces a non-flat path using walk-forward fitted model."""
        dates = pd.date_range(start='2010-01-01', periods=60, freq='MS')
        data = {
            'X': np.linspace(98.0, 102.0, 60),
            'Y': np.linspace(99.0, 103.0, 60),
            'ICI_Z': np.sin(np.linspace(0, 5, 60)),
            'CPI_Z': np.cos(np.linspace(0, 5, 60)),
            'Yield Spread_Z': np.linspace(-1, 1, 60),
            'Real Policy Rate_Z': np.linspace(1, -1, 60)
        }
        df = pd.DataFrame(data, index=dates)
        idx = 50
        center = 100.0
        max_h = 6

        res = ForecastingEngine._macro_driver_signal(df, idx, center, None, max_h)
        path = res['path']

        self.assertEqual(len(path), max_h)
        x_now, y_now = df['X'].iloc[idx], df['Y'].iloc[idx]
        self.assertNotEqual(path[-1], (x_now, y_now))


if __name__ == '__main__':
    unittest.main()
