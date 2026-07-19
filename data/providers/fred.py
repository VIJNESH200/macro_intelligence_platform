"""FRED data provider — wraps pandas-datareader for FRED API access."""
import pandas as pd
import pandas_datareader.data as web
from datetime import datetime
from .base import BaseProvider


class FREDProvider(BaseProvider):
    """Fetches macroeconomic series from the Federal Reserve (FRED)."""

    @property
    def name(self) -> str:
        return 'FRED'

    @property
    def update_frequency(self) -> str:
        return 'monthly'

    def fetch(self, symbol: str, start_date: str = '2000-01-01',
              end_date: str | None = None) -> pd.Series:
        """Fetch a FRED series, resampled to month-start and forward-filled."""
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        try:
            df = web.DataReader(symbol, 'fred', start_date, end_date)
            series = df[symbol].resample('MS').first().ffill()
            self.last_source_used = 'FRED API'
            return series
        except Exception as e:
            print(f"  [!] FRED fetch failed for {symbol}: {e}")
            return pd.Series(dtype=float)
