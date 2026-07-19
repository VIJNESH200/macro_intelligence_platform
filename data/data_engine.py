"""
Data Engine — Orchestrates data loading across all providers.
=============================================================
Replaces the monolithic load_data() function with a modular,
cached, provider-based pipeline. Produces the exact same
DataFrame output as the original.
"""
import pandas as pd
import numpy as np
from .providers.fred import FREDProvider
from .providers.yfinance_provider import YFinanceProvider
from .providers.mospi import MOSPIProvider
from .providers.rbi import RBIProvider
from .providers.oecd import OECDProvider
from .providers.s_and_p import SAndPProvider
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
            return 'Unknown', '⚪'
            
        delta_days = (pd.Timestamp.now() - release_date).days
        
        if frequency.lower() == 'daily':
            if delta_days <= 3:
                return 'Fresh', '🟢'
            elif delta_days <= 10:
                return 'Delayed', '🟡'
            else:
                return 'Stale', '🔴'
        else: # Monthly data
            if delta_days <= 45:
                return 'Fresh', '🟢'
            elif delta_days <= 90:
                return 'Delayed', '🟡'
            else:
                return 'Stale', '🔴'

    def __init__(self, config: dict, market_series: dict,
                 macro_series: dict = None, cache_dir: str | None = None):
        self.config = config
        self.market_series = market_series
        self.macro_series = macro_series or {}
        
        self.providers = {
            'fred': FREDProvider(),
            'yfinance': YFinanceProvider(),
            'mospi': MOSPIProvider(),
            'rbi': RBIProvider(),
            'oecd': OECDProvider(),
            's_and_p': SAndPProvider(),
            'yield': YieldProvider(),
            'credit': CreditProvider()
        }
        self.fred = self.providers['fred']
        self.yfinance = self.providers['yfinance']
        self.cache = CacheManager(cache_dir)
        self.data_metadata = {}

    def load_indicator(self) -> pd.DataFrame:
        """Load the primary macro indicator series."""
        ticker = self.config['ticker']
        source = self.config['source'].lower()
        cache_key = f"indicator_{ticker}"

        print(f"Fetching {self.config['name']} ({ticker}) from {source}...")

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

        if self.cache.is_fresh(cache_key):
            cached = self.cache.get(cache_key)
            if cached is not None:
                print("  (using cached macro data)")
                for col in cached.columns:
                    df[col] = cached[col]
                    
                    # Transform for metadata display if needed
                    info = self.macro_series.get(col)
                    if info and info.transformation == 'yoy':
                        display_series = cached[col].dropna().pct_change(12) * 100
                    elif info and info.transformation == 'real_rate' and 'CPI' in df.columns:
                        cpi_yoy = df['CPI'].dropna().pct_change(12) * 100
                        repo_rate = cached[col].dropna()
                        cpi_yoy_aligned = cpi_yoy.reindex(repo_rate.index).ffill()
                        display_series = repo_rate - cpi_yoy_aligned
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
            
            series = provider.fetch(sym)
            if not series.empty:
                df[name] = series
                
                # Transform for metadata display if needed
                if info.transformation == 'yoy':
                    display_series = series.dropna().pct_change(12) * 100
                elif info.transformation == 'real_rate' and 'CPI' in df.columns:
                    cpi_yoy = df['CPI'].dropna().pct_change(12) * 100
                    repo_rate = series.dropna()
                    cpi_yoy_aligned = cpi_yoy.reindex(repo_rate.index).ffill()
                    display_series = repo_rate - cpi_yoy_aligned
                else:
                    display_series = series
                    
                rel_date = series.dropna().index[-1] if not series.dropna().empty else None
                status, indicator = self.classify_freshness(rel_date, 'monthly')
                self.data_metadata[name] = {
                    'value': round(display_series.dropna().iloc[-1], 2) if not display_series.dropna().empty else 'N/A',
                    'release_date': rel_date.strftime('%b %Y') if rel_date else 'N/A',
                    'source': provider.last_source_used or provider.name,
                    'last_updated': 'Live',
                    'cache_status': f"{indicator} {status}"
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
        existing_cols = [c for c in macro_cols if c in df.columns]
        if existing_cols:
            self.cache.put(cache_key, df[existing_cols])

        return df

    def load_market_series(self, df: pd.DataFrame) -> pd.DataFrame:
        """Load all market context series and merge into the indicator DataFrame."""
        print("Fetching Market Context series...")
        cache_key = "market_series_all"

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
            series = self.fred.fetch(sym)
            if not series.empty:
                df[name] = series
            else:
                df[name] = np.nan

        # ---- yfinance market series (bulk fetch) ----
        yf_series = {k: v['symbol'] for k, v in self.market_series.items()
                     if v['type'] == 'yfinance'}
        if yf_series:
            tickers = list(yf_series.values())
            close_df = self.yfinance.fetch_bulk(tickers)

            if not close_df.empty:
                for name, sym in yf_series.items():
                    if sym in close_df.columns:
                        df[name] = close_df[sym]
                    else:
                        df[name] = np.nan
            else:
                for name in yf_series.keys():
                    df[name] = np.nan

        # Cache the market columns
        market_cols = list(self.market_series.keys())
        existing_cols = [c for c in market_cols if c in df.columns]
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
