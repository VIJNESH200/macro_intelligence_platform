from __future__ import annotations
import pandas as pd
from .base import BaseProvider
from .rbi import RBIProvider

class CreditProvider(BaseProvider):
    """Credit Provider that calculates YoY growth for Scheduled Commercial Bank Credit."""
    
    def __init__(self):
        super().__init__()
        self.rbi = RBIProvider()
        self.raw_credit = None
        self._source = None
        
    @property
    def name(self) -> str:
        return 'Credit Growth'
        
    @property
    def update_frequency(self) -> str:
        return 'monthly'
        
    def fetch(self, symbol: str, start_date: str = '2000-01-01', end_date: str | None = None) -> pd.Series:
        # Fetch raw credit outstanding (e.g. INDBKCRD)
        self.raw_credit = self.rbi.fetch(symbol, start_date, end_date)
        self._source = self.rbi.last_source_used
        self.last_source_used = self._source
        
        if not self.raw_credit.empty:
            # Returns raw credit outstanding series; FeatureEngine performs YoY transformation
            return self.raw_credit
            
        self.last_source_used = "Unavailable"
        return pd.Series(dtype=float)
