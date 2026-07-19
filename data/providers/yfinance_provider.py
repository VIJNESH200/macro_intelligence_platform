"""yfinance data provider — wraps yfinance for market data."""
import pandas as pd
import yfinance as yf
from .base import BaseProvider


class YFinanceProvider(BaseProvider):
    """Fetches market data (equities, FX, commodities) via yfinance."""

    @property
    def name(self) -> str:
        return 'yfinance'

    @property
    def update_frequency(self) -> str:
        return 'daily'

    def fetch(self, symbol: str, start_date: str = '2000-01-01',
              end_date: str | None = None) -> pd.Series:
        """Fetch a single symbol's Close price, resampled to month-start."""
        try:
            data = yf.download(symbol, start=start_date, progress=False)
            if data.empty:
                return pd.Series(dtype=float)
            if isinstance(data.columns, pd.MultiIndex):
                close = data['Close']
                if isinstance(close, pd.DataFrame):
                    close = close.iloc[:, 0]
            else:
                close = data['Close']
            self.last_source_used = 'Yahoo Finance API'
            return close.resample('MS').last().ffill()
        except Exception as e:
            print(f"  ⚠ yfinance fetch failed for {symbol}: {e}")
            return pd.Series(dtype=float)

    def fetch_bulk(self, symbols: list[str],
                   start_date: str = '2000-01-01') -> pd.DataFrame:
        """Fetch multiple symbols in a single API call for efficiency."""
        try:
            data = yf.download(symbols, start=start_date, progress=False)
            if isinstance(data.columns, pd.MultiIndex) and 'Close' in data.columns.levels[0]:
                close_df = data['Close']
            else:
                close_df = data
            self.last_source_used = 'Yahoo Finance API (Bulk)'
            return close_df.resample('MS').last().ffill()
        except Exception as e:
            print(f"  ⚠ yfinance bulk fetch failed: {e}")
            return pd.DataFrame()
