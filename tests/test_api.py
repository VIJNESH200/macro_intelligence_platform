from __future__ import annotations
"""
Unit & Schema Validation Tests for Top-Level Python API & Models.
================================================================
"""
import unittest
import pandas as pd
from api import load_macro_data, compute_features, forecast_cycle
from macro_intel import load_macro_data as alias_load, compute_features as alias_compute, forecast_cycle as alias_forecast
from models import DataBundle, ForecastResult, HorizonForecast
from config.markets import get_market_config


class TestAPIAndModels(unittest.TestCase):
    """Test DataBundle, ForecastResult dataclasses, and api.py pipeline."""

    def test_data_bundle_schema(self):
        """Verify DataBundle attributes and dictionary representation."""
        dates = pd.date_range('2020-01-01', periods=12, freq='MS')
        df = pd.DataFrame({'INDLOLITOAASTSAM': range(12)}, index=dates)
        health = {'ICI': {'source': 'live', 'as_of': '2026-06-30'}}

        bundle = DataBundle(df=df, data_health=health, as_of='2026-06-30', config={'name': 'test'})
        self.assertEqual(bundle.as_of, '2026-06-30')
        self.assertIn('data_rows', bundle.to_dict())
        self.assertEqual(bundle.to_dict()['data_rows'], 12)

    def test_forecast_result_schema_and_json(self):
        """Verify ForecastResult schema validation and JSON serialization."""
        f6m = HorizonForecast(x=101.5, y=100.8, quadrant='Expansion', conviction=72.5)
        res = ForecastResult(
            as_of='2026-06-30',
            current_regime='Expansion',
            forecasts={'6m': f6m},
            signal_contributions={'momentum': {'x': 101.0, 'y': 100.5}},
            conviction=72.5,
            model_version='2.5.0',
            data_health={'ICI': {'source': 'live'}},
            projected_path=[(100.0, 100.0), (101.5, 100.8)],
            confidence_band={'inner': []},
            residual_std={'x': 0.5, 'y': 0.5}
        )

        self.assertTrue(res.validate_schema())
        json_str = res.to_json()
        self.assertIn('"current_regime": "Expansion"', json_str)
        self.assertIn('"conviction": 72.5', json_str)

    def test_end_to_end_api_pipeline(self):
        """Verify load_macro_data -> compute_features -> forecast_cycle execution in offline mode."""
        # Pass INDIA's config explicitly rather than relying on the process-global
        # CONFIG (whose active market is mutable state the market-toggle feature
        # can flip to 'US'), since this test asserts on the India CLI ticker.
        india = get_market_config('INDIA')
        config = {**india['primary_indicator'], 'version': '2.5'}
        bundle = load_macro_data(config=config, market_series=india['market_series'],
                                  macro_series=india['macro_series'], offline=True)
        self.assertIsInstance(bundle, DataBundle)
        self.assertIn('INDLOLITOAASTSAM', bundle.df.columns)
        self.assertIsNotNone(bundle.as_of)

        feat_bundle = compute_features(bundle)
        self.assertIn('X', feat_bundle.df.columns)
        self.assertIn('Y', feat_bundle.df.columns)
        self.assertIn('Quadrant', feat_bundle.df.columns)

        forecast = forecast_cycle(feat_bundle)
        self.assertIsInstance(forecast, ForecastResult)
        self.assertTrue(forecast.validate_schema())
        self.assertIn('6m', forecast.forecasts)
        self.assertIn(forecast.forecasts['6m'].quadrant, ['Expansion', 'Slowdown', 'Contraction', 'Recovery'])


if __name__ == '__main__':
    unittest.main()
