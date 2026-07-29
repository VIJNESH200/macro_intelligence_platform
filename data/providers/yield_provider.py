from __future__ import annotations
import pandas as pd
from .base import BaseProvider, ProviderResult, create_provider_result
from .rbi import RBIProvider

class YieldProvider(BaseProvider):
    """Yield Provider that calculates Yield Spread (10Y - 91D) using RBI/FRED data."""
    
    def __init__(self):
        super().__init__()
        self.rbi = RBIProvider()
        self.raw_10y = None
        self.raw_91d = None
        self._source_10y = None
        self._source_91d = None
        
    @property
    def name(self) -> str:
        return 'Yield Spread'
        
    @property
    def update_frequency(self) -> str:
        return 'monthly'
        
    def fetch(self, symbol: str, start_date: str = '2000-01-01', end_date: str | None = None, return_meta: bool = False) -> pd.Series | ProviderResult:
        source_type = "live"
        if symbol and symbol not in ['YIELD_SPREAD', 'Yield Spread', '']:
            series = self.rbi.fetch(symbol, start_date, end_date)
            self.last_source_used = self.rbi.last_source_used
            if return_meta:
                return create_provider_result(series, "live" if not series.empty else "bundled_fallback", symbol, details=self.last_source_used)
            return series

        self.raw_10y = self.rbi.fetch('INDIRLTLT01STM', start_date, end_date)
        self._source_10y = self.rbi.last_source_used
        
        self.raw_91d = self.rbi.fetch('INDIRLSTT01STM', start_date, end_date)
        self._source_91d = self.rbi.last_source_used
        
        if not self.raw_10y.empty and not self.raw_91d.empty:
            spread = self.raw_10y - self.raw_91d
            self.last_source_used = f"10Y: {self._source_10y} | 91D: {self._source_91d}"
            series = spread.dropna()
        else:
            self.last_source_used = "Unavailable"
            series = pd.Series(dtype=float)
            source_type = "bundled_fallback"

        if return_meta:
            return create_provider_result(series, source_type, symbol, details=self.last_source_used)
        return series
