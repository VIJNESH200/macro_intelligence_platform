import pandas as pd
import os
from .base import BaseProvider
from .fred import FREDProvider

class RBIProvider(BaseProvider):
    """Reserve Bank of India (RBI) provider."""
    
    def __init__(self):
        super().__init__()
        self.proxy = FREDProvider()
        
    @property
    def name(self) -> str:
        return 'RBI'
        
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
                    self.last_source_used = 'CSV (RBI)'
                    return series
            except Exception as e:
                print(f"Failed to read {csv_path}: {e}. Falling back to proxy.")
                
        # Mapping RBI tickers to available FRED proxies for automatic web fetching
        fred_proxy_map = {
            'INDIRLSTT01STM': 'INDIR3TIB01STM', # 3-Month Interbank Rate as proxy for 91D T-Bill
            'INDBKCRD': 'MANMM101INM189S'       # M1 Money Supply as proxy for Credit Growth
        }
        
        fred_symbol = fred_proxy_map.get(symbol, symbol)
        self.last_source_used = f'FRED Proxy ({fred_symbol})'
        return self.proxy.fetch(fred_symbol, start_date, end_date)
