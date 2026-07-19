import pandas as pd
from .base import BaseProvider
from .fred import FREDProvider

class OECDProvider(BaseProvider):
    """Organization for Economic Co-operation and Development (OECD) provider."""
    
    def __init__(self):
        self.proxy = FREDProvider()
        
    @property
    def name(self) -> str:
        return 'OECD'
        
    @property
    def update_frequency(self) -> str:
        return 'monthly'
        
    def fetch(self, symbol: str, start_date: str = '2000-01-01', end_date: str | None = None) -> pd.Series:
        # For Phase 2, we use FRED as a proxy for OECD data
        return self.proxy.fetch(symbol, start_date, end_date)
