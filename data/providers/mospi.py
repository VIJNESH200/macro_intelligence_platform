import pandas as pd
import os
from .base import BaseProvider
from .fred import FREDProvider

class MOSPIProvider(BaseProvider):
    """Ministry of Statistics and Programme Implementation (MOSPI) provider."""
    
    def __init__(self):
        super().__init__()
        self.proxy = FREDProvider()
        
    @property
    def name(self) -> str:
        return 'MOSPI'
        
    @property
    def update_frequency(self) -> str:
        return 'monthly'
        
    def fetch(self, symbol: str, start_date: str = '2000-01-01', end_date: str | None = None) -> pd.Series:
        csv_path = os.path.join('data', 'local_data', f'{symbol}.csv')
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
                if not df.empty and df.columns.size > 0:
                    series = df.iloc[:, 0].resample('MS').first().ffill()
                    self.last_source_used = 'CSV (MOSPI)'
                    return series
            except Exception as e:
                print(f"Failed to read {csv_path}: {e}. Falling back to proxy.")
                
        self.last_source_used = 'FRED Proxy'
        return self.proxy.fetch(symbol, start_date, end_date)
