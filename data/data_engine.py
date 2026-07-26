from __future__ import annotations
"""
Data Engine — Orchestrates data loading across all providers.
=============================================================
Replaces the monolithic load_data() function with a modular,
cached, provider-based pipeline. Produces the exact same
DataFrame output as the original.
"""
from typing import Any
import pandas as pd
import numpy as np
from .providers.fred import FREDProvider
from .providers.yfinance_provider import YFinanceProvider
from .providers.imf import IMFProvider
from .providers.rbi import RBIProvider
from .providers.oecd import OECDProvider
from .providers.yield_provider import YieldProvider
from .providers.credit_provider import CreditProvider
from .cache import CacheManager


class DataEngine:
    """Central data orchestrator for the Macro Intelligence Platform.

    Usage:
        engine = DataEngine(config, market_series, macro_series)
        df = engine.load_all()
    """

    @staticmethod
    def classify_freshness(release_date: pd.Timestamp | None, frequency: str) -> tuple[str, str]:
        """Classify data freshness relative to current system date.
        
        Returns:
            tuple (status_label, color_indicator)
            e.g. ('Fresh', '🟢') or ('Stale', '🔴')
        """
        if release_date is None or pd.isna(release_date):
            return 'Unknown', '[UNKNOWN]'
            
        delta_days = (pd.Timestamp.now() - release_date).days
        
        if frequency.lower() == 'daily':
            if delta_days <= 3:
                return 'Fresh', '[OK]'
            elif delta_days <= 10:
                return 'Delayed', '[DELAYED]'
            else:
                return 'Stale', '[STALE]'
        elif frequency.lower() == 'manual':
            # Manual inputs are updated whenever the user provides them
            return 'Manual Input', '[MANUAL]'
        else: # Monthly data
            if delta_days <= 45:
                return 'Fresh', '[OK]'
            elif delta_days <= 90:
                return 'Delayed', '[DELAYED]'
            else:
                return 'Stale', '[STALE]'

    def __init__(self, config: dict, market_series: dict,
                 macro_series: dict = None, cache_dir: str | None = None,
                 offline: bool = False):
        import os
        self.config = config
        self.market_series = market_series
        self.macro_series = macro_series or {}

        self.providers = {
            'fred': FREDProvider(),
            'yfinance': YFinanceProvider(),
            'imf': IMFProvider(),
            'rbi': RBIProvider(),
            'oecd': OECDProvider(),
            'yield': YieldProvider(),
            'credit': CreditProvider()
        }
        self.fred = self.providers['fred']
        self.yfinance = self.providers['yfinance']
        self.cache = CacheManager(cache_dir)
        self.data_metadata = {}
        self.load_warnings = []  # Track partial failures

    def load_indicator(self) -> pd.DataFrame:
        """Load the primary macro indicator series."""
        ticker = self.config['ticker']
        source = self.config['source'].lower()
        cache_key = f"indicator_{ticker}"

        print(f"Fetching {self.config['name']} ({ticker}) from {source}...")

        import os
        local_path = os.path.join(os.path.dirname(__file__), 'local_data', f"{ticker}.csv")

        if self.offline and os.path.exists(local_path):
            print("  (using offline bundled indicator data)")
            local_df = pd.read_csv(local_path, index_col=0, parse_dates=True)
            rel_date = local_df.dropna().index[-1] if not local_df.dropna().empty else None
            self.data_metadata[self.config['name']] = {
                'value': round(local_df.iloc[-1, 0], 2) if not local_df.empty else 'N/A',
                'release_date': rel_date.strftime('%b %Y') if rel_date else 'N/A',
                'source': f"{self.config['source']} (Offline Bundled)",
                'last_updated': 'N/A',
                'cache_status': 'Offline [OK]'
            }
            return local_df

        if self.cache.is_fresh(cache_key):
            cached = self.cache.get(cache_key)
            if cached is not None:
                print("  (using cached data)")
                rel_date = cached.dropna().index[-1] if not cached.dropna().empty else None
                status, indicator = self.classify_freshness(rel_date, self.config['frequency'])
                self.data_metadata[self.config['name']] = {
                    'value': round(cached.iloc[-1, 0], 2) if not cached.empty else 'N/A',
                    'release_date': rel_date.strftime('%b %Y') if rel_date else 'N/A',
                    'source': f"{self.config['source']} (Cached)",
                    'last_updated': 'N/A',
                    'cache_status': f"{indicator} {status}"
                }
                return cached

        # Fetch from provider
        provider = self.providers.get(source, self.providers['fred'])
        series = provider.fetch(ticker)

        if series.empty:
            # Fall back to stale cache
            if self.cache.has_any(cache_key):
                print("  [!] Network failed, using stale cache")
                cached = self.cache.get(cache_key)
                if cached is not None:
                    return cached
            # Fall back to bundled local fallback CSV
            import os
            local_path = os.path.join(os.path.dirname(__file__), 'local_data', f"{ticker}.csv")
            if os.path.exists(local_path):
                print("  [!] Network and cache failed, using bundled local fallback data")
                try:
                    local_df = pd.read_csv(local_path, index_col=0, parse_dates=True)
                    return local_df
                except Exception:
                    pass
            raise ValueError(f"No data returned for ticker {ticker} and no cache available.")

        df = series.to_frame(name=ticker)
        df = df.resample('MS').first().ffill()
        self.cache.put(cache_key, df)
        
        rel_date = series.dropna().index[-1] if not series.dropna().empty else None
        status, indicator = self.classify_freshness(rel_date, self.config['frequency'])
        self.data_metadata[self.config['name']] = {
            'value': round(series.dropna().iloc[-1], 2) if not series.dropna().empty else 'N/A',
            'release_date': rel_date.strftime('%b %Y') if rel_date else 'N/A',
            'source': provider.last_source_used or provider.name,
            'last_updated': 'Live',
            'cache_status': f"{indicator} {status}"
        }
        return df

    def load_macro_series(self, df: pd.DataFrame) -> pd.DataFrame:
        """Load all macro driver series and merge into the indicator DataFrame."""
        if not self.macro_series:
            return df
            
        print("Fetching Macro Driver series...")
        cache_key = "macro_series_all"

        import os
        local_macro_path = os.path.join(os.path.dirname(__file__), 'local_data', 'macro_series_fallback.csv')

        if self.offline and os.path.exists(local_macro_path):
            print("  (using offline bundled macro data)")
            local_df = pd.read_csv(local_macro_path, index_col=0, parse_dates=True)
            return df.join(local_df, how='outer')

        if self.cache.is_fresh(cache_key):
            cached = self.cache.get(cache_key)
            if cached is not None:
                print("  (using cached macro data)")
                # Outer join the cached macro data to ensure newer dates are kept
                df = df.join(cached, how='outer')
                
                for col in cached.columns:
                    # Transform for metadata display if needed
                    info = self.macro_series.get(col)
                    if info and info.transformation == 'yoy':
                        display_series = cached[col].dropna().pct_change(12) * 100
                    elif info and info.transformation == 'real_rate' and 'CPI' in df.columns:
                        cpi_yoy = df['CPI'].dropna().pct_change(12) * 100
                        repo_rate = cached[col].dropna()
                        combined_index = repo_rate.index.union(cpi_yoy.index)
                        display_series = (repo_rate.reindex(combined_index).ffill() - cpi_yoy.reindex(combined_index).ffill()).dropna()
                    else:
                        display_series = cached[col]
                        
                    rel_date = cached[col].dropna().index[-1] if not cached[col].dropna().empty else None
                    status, indicator = self.classify_freshness(rel_date, 'monthly')
                    self.data_metadata[col] = {
                        'value': round(display_series.dropna().iloc[-1], 2) if not display_series.dropna().empty else 'N/A',
                        'release_date': rel_date.strftime('%b %Y') if rel_date else 'N/A',
                        'source': f"{info.source} (Cached)" if info else "Unknown (Cached)",
                        'last_updated': 'N/A',
                        'cache_status': f"{indicator} {status}"
                    }
                return df

        for name, info in self.macro_series.items():
            sym = info.ticker
            source = info.source.lower()
            provider = self.providers.get(source, self.providers['fred'])
            
            res = provider.fetch_with_meta(sym)
            series = res.series
            if not series.empty:
                df = df.join(series.rename(name), how='outer')
                
                # Transform for metadata display if needed
                if info.transformation == 'yoy':
                    display_series = series.dropna().pct_change(12) * 100
                elif info.transformation == 'real_rate' and 'CPI' in df.columns:
                    cpi_yoy = df['CPI'].dropna().pct_change(12) * 100
                    repo_rate = series.dropna()
                    combined_index = repo_rate.index.union(cpi_yoy.index)
                    display_series = (repo_rate.reindex(combined_index).ffill() - cpi_yoy.reindex(combined_index).ffill()).dropna()
                else:
                    display_series = series
                    
                rel_date = display_series.index[-1] if not display_series.empty else None
                status, indicator = self.classify_freshness(rel_date, 'monthly')
                self.data_metadata[name] = {
                    'value': round(display_series.dropna().iloc[-1], 2) if not display_series.dropna().empty else 'N/A',
                    'release_date': rel_date.strftime('%b %Y') if rel_date else 'N/A',
                    'source': res.meta.source,
                    'last_updated': res.meta.fetched_at,
                    'cache_status': f"{indicator} {status}",
                    'schema_ok': res.meta.schema_ok
                }
            else:
                df[name] = np.nan
                self.data_metadata[name] = {
                    'value': 'N/A',
                    'release_date': 'N/A',
                    'source': 'Unavailable',
                    'last_updated': 'N/A',
                    'cache_status': 'Failed'
                }

        # Cache the macro columns
        macro_cols = list(self.macro_series.keys())
        existing_cols = [c for c in macro_cols if c in df.columns and not df[c].isna().all()]
        if not existing_cols:
            import os
            local_macro_path = os.path.join(os.path.dirname(__file__), 'local_data', 'macro_series_fallback.csv')
            if os.path.exists(local_macro_path):
                try:
                    local_df = pd.read_csv(local_macro_path, index_col=0, parse_dates=True)
                    df = df.join(local_df, how='outer')
                    existing_cols = [c for c in macro_cols if c in df.columns]
                except Exception:
                    pass

        if existing_cols:
            self.cache.put(cache_key, df[existing_cols])

        return df

    def load_market_series(self, df: pd.DataFrame) -> pd.DataFrame:
        """Load all market context series and merge into the indicator DataFrame."""
        print("Fetching Market Context series...")
        cache_key = "market_series_all"
        self.load_warnings = []

        import os
        local_market_path = os.path.join(os.path.dirname(__file__), 'local_data', 'market_series_fallback.csv')

        if self.offline and os.path.exists(local_market_path):
            print("  (using offline bundled market data)")
            local_df = pd.read_csv(local_market_path, index_col=0, parse_dates=True)
            for col in local_df.columns:
                df[col] = local_df[col]
            return df

        if self.cache.is_fresh(cache_key):
            cached = self.cache.get(cache_key)
            if cached is not None:
                print("  (using cached market data)")
                for col in cached.columns:
                    df[col] = cached[col]
                return df

        # ---- FRED market series ----
        fred_series = {k: v['symbol'] for k, v in self.market_series.items()
                       if v['type'] == 'fred'}
        for name, sym in fred_series.items():
            res = self.fred.fetch_with_meta(sym)
            series = res.series
            if not series.empty:
                df[name] = series
                rel_date = series.dropna().index[-1] if not series.dropna().empty else None
                status, indicator = self.classify_freshness(rel_date, 'monthly')
                self.data_metadata[name] = {
                    'value': round(series.dropna().iloc[-1], 2) if not series.dropna().empty else 'N/A',
                    'release_date': rel_date.strftime('%b %Y') if rel_date else 'N/A',
                    'source': res.meta.source,
                    'last_updated': res.meta.fetched_at,
                    'cache_status': f"{indicator} {status}",
                    'schema_ok': res.meta.schema_ok
                }
            else:
                df[name] = np.nan
                self.load_warnings.append(f"{name} ({sym}) unavailable")

        # ---- yfinance market series (bulk fetch) ----
        yf_series = {k: v['symbol'] for k, v in self.market_series.items()
                     if v['type'] == 'yfinance'}
        if yf_series:
            tickers = list(yf_series.values())
            res_dict = self.yfinance.fetch_bulk(tickers, return_meta=True)
            close_df = pd.DataFrame({sym: res_dict[sym].series for sym in tickers if not res_dict[sym].series.empty})

            if not close_df.empty:
                for name, sym in yf_series.items():
                    if sym in close_df.columns:
                        # Check if data is actually present (not all NaN)
                        if not close_df[sym].isna().all():
                            df[name] = close_df[sym]
                        else:
                            df[name] = np.nan
                            self.load_warnings.append(f"{name} ({sym}) no data available")
                    else:
                        df[name] = np.nan
                        self.data_metadata[name] = {
                            'value': 'N/A',
                            'release_date': 'N/A',
                            'source': 'bundled_fallback',
                            'last_updated': 'N/A',
                            'cache_status': 'Failed',
                            'schema_ok': False
                        }
            else:
                for name in yf_series.keys():
                    df[name] = np.nan
                    self.data_metadata[name] = {
                        'value': 'N/A',
                        'release_date': 'N/A',
                        'source': 'bundled_fallback',
                        'last_updated': 'N/A',
                        'cache_status': 'Failed',
                        'schema_ok': False
                    }
=======
                        # Check if data is actually present (not all NaN)
                        if not close_df[sym].isna().all():
                            df[name] = close_df[sym]
                        else:
                            df[name] = np.nan
                            self.load_warnings.append(f"{name} ({sym}) no data available")
                    else:
                        df[name] = np.nan
                        self.load_warnings.append(f"{name} ({sym}) not found")
            else:
                for name in yf_series.keys():
                    df[name] = np.nan
                self.load_warnings.append(f"Market data fetch completely failed (using fallback)")
>>>>>>> 19ef381 (fix: handle partial market data failures gracefully)

        # Cache the market columns
        market_cols = list(self.market_series.keys())
        existing_cols = [c for c in market_cols if c in df.columns and not df[c].isna().all()]
        if not existing_cols:
            import os
            local_market_path = os.path.join(os.path.dirname(__file__), 'local_data', 'market_series_fallback.csv')
            if os.path.exists(local_market_path):
                try:
                    local_df = pd.read_csv(local_market_path, index_col=0, parse_dates=True)
                    for col in local_df.columns:
                        df[col] = local_df[col]
                    existing_cols = [c for c in market_cols if c in df.columns]
                except Exception:
                    pass

        if existing_cols:
            self.cache.put(cache_key, df[existing_cols])

        return df

    @property
    def get_metadata(self) -> dict:
        return self.data_metadata

    def load_all(self) -> pd.DataFrame:
        """Load indicator + macro + market series into a single DataFrame.

        This is the main entry point, producing the exact combined dataset.
        """
        df = self.load_indicator()
        df = self.load_macro_series(df)
        df = self.load_market_series(df)
        return df

    def load_all_bundle(self) -> Any:
        """Load data and return a structured DataBundle payload."""
        try:
            from ..models import DataBundle
        except ImportError:
            from models import DataBundle

        df = self.load_all()
        last_date = df.dropna(how='all').index[-1] if not df.empty else pd.Timestamp.now()
        as_of_str = last_date.strftime('%Y-%m-%d')
        return DataBundle(
            df=df,
            data_health=self.data_metadata,
            as_of=as_of_str,
            config=self.config
        )
