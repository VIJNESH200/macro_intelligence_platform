import os
import sys
import unittest
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from features.feature_engine import FeatureEngine
from analytics.macro_intelligence_engine import MacroIntelligenceEngine


class TestRealPolicyRate(unittest.TestCase):

    def setUp(self):
        # Create a clean synthetic 120-month (10 year) monthly dataset
        dates = pd.date_range(start='2014-01-01', periods=120, freq='MS')
        self.df = pd.DataFrame(index=dates)
        
        # Primary CLI ticker for India
        self.df['INDLOLITOAASTSAM'] = 100.0 + np.sin(np.linspace(0, 8*np.pi, 120)) * 2.0
        
        # CPI Index (growing at ~5% annual rate with slight cyclic fluctuation)
        self.df['CPI'] = 100.0 * (1.05 ** (np.arange(120) / 12.0)) + np.sin(np.linspace(0, 6*np.pi, 120)) * 1.5
        
        # Repo Rate (constant 6.5%)
        self.df['Real Policy Rate'] = 6.50
        
        # Yields
        self.df['Yield 10Y'] = 7.10
        self.df['Yield Short'] = 6.00
        
        self.config = {
            'name': 'India CLI (OECD)',
            'ticker': 'INDLOLITOAASTSAM',
            'window': 36,
            'center': 100,
            'points_per_segment': 10
        }

    def test_real_policy_rate_formula(self):
        """Verify Real Policy Rate = Repo Rate - CPI YoY."""
        df_feat, _ = FeatureEngine.compute_all(self.df.copy(), self.config)
        
        # At the last row of df_feat, compare computed Real Policy Rate_Base against expected
        last_date = df_feat.index[-1]
        orig_idx = self.df.index.get_loc(last_date)
        
        cpi_curr = self.df['CPI'].iloc[orig_idx]
        cpi_prev = self.df['CPI'].iloc[orig_idx - 12]
        expected_cpi_yoy = (cpi_curr - cpi_prev) / cpi_prev * 100
        expected_real_rate = 6.50 - expected_cpi_yoy
        
        actual_real_rate = df_feat['Real Policy Rate_Base'].iloc[-1]
        self.assertAlmostEqual(actual_real_rate, expected_real_rate, places=4)

    def test_missing_cpi_degrades_safely(self):
        """Verify missing CPI does not crash FeatureEngine and sets Real Policy Rate to NaN."""
        df_no_cpi = self.df.drop(columns=['CPI']).copy()
        
        df_feat, _ = FeatureEngine.compute_all(df_no_cpi, self.config)
        
        self.assertIn('Real Policy Rate_Base', df_feat.columns)
        self.assertTrue(df_feat['Real Policy Rate_Base'].isna().all())

    def test_yoy_preserves_calendar_month_alignment(self):
        """Verify YoY calculation uses 12-month calendar shift regardless of missing values."""
        df_gapped = self.df.copy()
        # Insert a NaN at index 50
        df_gapped.loc[df_gapped.index[50], 'CPI'] = np.nan
        
        df_feat, _ = FeatureEngine.compute_all(df_gapped, self.config)
        
        # At index 60 (which is valid), YoY should still compare against index 48 (12 months prior), not index 47
        cpi_60 = df_gapped['CPI'].iloc[60]
        cpi_48 = df_gapped['CPI'].iloc[48]
        expected_yoy_60 = (cpi_60 - cpi_48) / cpi_48 * 100
        
        target_date = self.df.index[60]
        actual_cpi_base_60 = df_feat.loc[target_date, 'CPI_Base']
        self.assertAlmostEqual(actual_cpi_base_60, expected_yoy_60, places=4)

    def test_unknown_state_evaluation_schema_is_complete(self):
        """Verify evaluate_indicators returns complete key schema even when indicator is in Unknown state."""
        df_feat, _ = FeatureEngine.compute_all(self.df.copy(), self.config)
        
        # Manually set a Z-score column to NaN to force Unknown state
        df_feat['CPI_Z'] = np.nan
        
        last_idx = len(df_feat) - 1
        evals = MacroIntelligenceEngine.evaluate_indicators(df_feat, idx=last_idx)
        
        cpi_eval = evals['CPI']
        self.assertEqual(cpi_eval['state'], 'Unknown')
        
        # Verify all standard keys exist to prevent KeyError downstream
        expected_keys = {'score', 'state', 'level', 'trend', 'raw_value', 'yoy_value', 'percentile', 'symbol', 'momentum'}
        self.assertTrue(expected_keys.issubset(cpi_eval.keys()), f"Missing keys: {expected_keys - cpi_eval.keys()}")

    def test_nan_momentum_produces_flat_trend(self):
        """Verify NaN momentum evaluates to 'Flat' trend rather than 'Weakening'."""
        df_feat, _ = FeatureEngine.compute_all(self.df.copy(), self.config)
        df_feat['CPI_MoM'] = np.nan
        
        last_idx = len(df_feat) - 1
        evals = MacroIntelligenceEngine.evaluate_indicators(df_feat, idx=last_idx)
        self.assertEqual(evals['CPI']['trend'], 'Flat')


if __name__ == '__main__':
    unittest.main()
