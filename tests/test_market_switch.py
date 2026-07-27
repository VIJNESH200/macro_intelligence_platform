from __future__ import annotations
"""
Regression tests for the India/US market-toggle feature.
==========================================================
Covers three bugs found while investigating a real "Market switch failed"
crash when switching from US to India:

1. The market/macro-series cache was keyed identically regardless of which
   market was active, so a fresh US cache could get served back for an
   India request with entirely different column names.
2. ICIProvider (India's live DPIIT fetch) was defined but never registered
   in DataEngine.providers, so India's ICI series silently routed through
   FRED (which 404s on the fake 'INDICI' ticker) instead of ever running.
3. The market-panel text widgets were only ever built once, for whichever
   market the app started in; switching markets left them keyed by the
   old market's series names.
"""
import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

import matplotlib
matplotlib.use('Agg')

import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import CONFIG, MARKET_SERIES, MACRO_SERIES, reload_for_market, get_current_market
from config.markets import get_market_config
from data.data_engine import DataEngine
from data.providers.ici import ICIProvider
from data.providers.base import create_provider_result
from ui.sidebars import build_market_texts


def _fake_series(value: float, periods: int = 6) -> pd.Series:
    idx = pd.date_range('2020-01-01', periods=periods, freq='MS')
    return pd.Series([value] * periods, index=idx)


class TestMarketProfiles(unittest.TestCase):
    """The two market profiles must actually be distinct, and switching
    between them (via reload_for_market) must fully replace the active
    series sets rather than merge or leak state between markets."""

    def tearDown(self):
        reload_for_market('INDIA')  # restore the actual default for later tests/imports

    def test_india_and_us_have_distinct_series(self):
        india = get_market_config('INDIA')
        us = get_market_config('US')

        self.assertIn('Sensex', india['market_series'])
        self.assertNotIn('Sensex', us['market_series'])
        self.assertIn('Dow Jones', us['market_series'])
        self.assertNotIn('Dow Jones', india['market_series'])
        self.assertIn('ICI', india['macro_series'])
        self.assertNotIn('ICI', us['macro_series'])

    def test_reload_for_market_swaps_global_state_both_directions(self):
        reload_for_market('INDIA')
        self.assertEqual(get_current_market(), 'INDIA')
        self.assertIn('Sensex', MARKET_SERIES)
        self.assertIn('ICI', MACRO_SERIES)
        self.assertEqual(CONFIG['ticker'], 'INDLOLITOAASTSAM')

        reload_for_market('US')
        self.assertEqual(get_current_market(), 'US')
        self.assertIn('Dow Jones', MARKET_SERIES)
        self.assertNotIn('Sensex', MARKET_SERIES)
        self.assertNotIn('ICI', MACRO_SERIES)
        self.assertEqual(CONFIG['ticker'], 'USALOLITOAASTSAM')

    def test_ici_provider_is_registered(self):
        # Regression test: ICIProvider was defined but never wired into
        # DataEngine.providers, so India's ICI series silently routed
        # through FRED (which 404s on the fake 'INDICI' ticker) instead of
        # ever calling the real DPIIT fetch path.
        engine = DataEngine(CONFIG, MARKET_SERIES, MACRO_SERIES)
        self.assertIn('ici', engine.providers)
        self.assertIsInstance(engine.providers['ici'], ICIProvider)


class TestMarketSeriesCacheIsolation(unittest.TestCase):
    """Regression test: switching markets must not serve back the other
    market's cached columns. Network calls are mocked so this stays fast
    and deterministic; only DataEngine's own cache-key logic is exercised."""

    def setUp(self):
        self.cache_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.cache_dir, ignore_errors=True)
        reload_for_market('INDIA')

    def _load_market_df(self, market: str) -> pd.DataFrame:
        profile = get_market_config(market)
        config = {**profile['primary_indicator'], 'version': '2.5'}
        engine = DataEngine(config, profile['market_series'], profile['macro_series'],
                             cache_dir=self.cache_dir, offline=False)
        df = pd.DataFrame(index=pd.date_range('2020-01-01', periods=6, freq='MS'))

        fred_result = create_provider_result(_fake_series(1.0), 'live', 'x')
        yf_symbols = [v['symbol'] for v in profile['market_series'].values() if v['type'] == 'yfinance']
        yf_results = {sym: create_provider_result(_fake_series(100.0), 'live', sym) for sym in yf_symbols}

        with patch.object(engine.fred, 'fetch_with_meta', return_value=fred_result), \
             patch.object(engine.yfinance, 'fetch_bulk', return_value=yf_results):
            return engine.load_market_series(df)

    def test_switching_markets_does_not_reuse_others_cached_columns(self):
        india_df = self._load_market_df('INDIA')
        self.assertIn('Sensex', india_df.columns)

        us_df = self._load_market_df('US')
        # Before the fix, both loads shared the "market_series_all" cache
        # key, so this would come back with India's columns (Sensex present,
        # Dow Jones missing) instead of US's.
        self.assertIn('Dow Jones', us_df.columns)
        self.assertNotIn('Sensex', us_df.columns)


class TestMarketPanelRebuild(unittest.TestCase):
    """Regression test: the market-panel text widgets must be rebuilt to
    match the newly active market_series, not left over from whichever
    market built them first."""

    def setUp(self):
        import matplotlib.pyplot as plt
        self.fig = plt.figure()
        self.ax_market = self.fig.add_axes([0.02, 0.06, 0.14, 0.57])

    def tearDown(self):
        import matplotlib.pyplot as plt
        plt.close(self.fig)

    def test_rebuild_replaces_stale_widget_keys(self):
        india = get_market_config('INDIA')['market_series']
        us = get_market_config('US')['market_series']

        texts = build_market_texts(self.ax_market, india)
        self.assertEqual(set(texts.keys()), set(india.keys()))

        # Simulate App.rebuild_market_panel(): remove the old artists, then
        # build fresh ones for the new market's series.
        for entry in texts.values():
            entry['name'].remove()
            entry['val'].remove()
            entry['chg'].remove()
            entry['sep'].remove()
        texts = build_market_texts(self.ax_market, us)

        # Before the fix, market_texts kept India's keys (e.g. 'Sensex')
        # after switching to US, so draw_frame's `pe['market_texts'][name]`
        # for a US-only series like 'Dow Jones' would KeyError.
        self.assertEqual(set(texts.keys()), set(us.keys()))
        self.assertNotIn('Sensex', texts)
        self.assertIn('Dow Jones', texts)


if __name__ == '__main__':
    unittest.main()
