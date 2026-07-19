import pandas as pd
from .base import BaseProvider
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
        
    def fetch(self, symbol: str, start_date: str = '2000-01-01', end_date: str | None = None) -> pd.Series:
        # symbol here is 'SPREAD', we ignore it and fetch the legs
        self.raw_10y = self.rbi.fetch('INDIRLTLT01STM', start_date, end_date)
        self._source_10y = self.rbi.last_source_used
        
        self.raw_91d = self.rbi.fetch('INDIRLSTT01STM', start_date, end_date)
        self._source_91d = self.rbi.last_source_used
        
        # Calculate Spread
        if not self.raw_10y.empty and not self.raw_91d.empty:
            spread = self.raw_10y - self.raw_91d
            self.last_source_used = f"10Y: {self._source_10y} | 91D: {self._source_91d}"
            return spread.dropna()
        
        self.last_source_used = "Unavailable"
        return pd.Series(dtype=float)
