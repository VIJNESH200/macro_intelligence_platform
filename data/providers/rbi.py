from __future__ import annotations
import pandas as pd
import os
from .base import BaseProvider, ProviderResult, create_provider_result
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
        
    def fetch(self, symbol: str, start_date: str = '2000-01-01', end_date: str | None = None, return_meta: bool = False) -> pd.Series | ProviderResult:
        source_type = "live"
        fred_proxy_map = {
            'INDIRLSTT01STM': 'INDIR3TIB01STM',
            'INDBKCRD': 'MANMM101INM189S'
        }
        
        fred_symbol = fred_proxy_map.get(symbol, symbol)
        series = pd.Series(dtype=float)
        try:
            series = self.proxy.fetch(fred_symbol, start_date, end_date)
        except Exception as e:
            print(f"Warning: RBI FRED proxy fetch failed for {symbol}: {e}")

        if symbol == 'IRSTCB01INM156N' and not series.empty:
            try:
                import requests
                from bs4 import BeautifulSoup
                import re
                from datetime import datetime
                headers = {'User-Agent': 'Mozilla/5.0'}
                res = requests.get('https://www.rbi.org.in/', headers=headers, timeout=10)
                soup = BeautifulSoup(res.text, 'html.parser')
                b = soup.find(string=re.compile('Policy Repo Rate'))
                if b:
                    text_val = b.parent.parent.text
                    match = re.search(r'([0-9\.]+)\%', text_val)
                    if match:
                        val = float(match.group(1))
                        series.loc[datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)] = val
                        series = series.resample('MS').ffill()
                        self.last_source_used = 'FRED + RBI Live'
            except Exception as e:
                print(f"Warning: Failed to fetch latest RBI Repo Rate: {e}")
                self.last_source_used = f'FRED Proxy ({fred_symbol})'
        elif not series.empty:
            self.last_source_used = f'FRED Proxy ({fred_symbol})'

        # Fallback to local CSV if live fetch was empty
        if series.empty:
            csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "local_data", f"{symbol}_fallback.csv")
            if os.path.exists(csv_path):
                try:
                    df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
                    if not df.empty and df.columns.size > 0:
                        series = df.iloc[:, 0].resample('MS').first().ffill()
                        self.last_source_used = 'CSV (RBI Fallback)'
                        source_type = "bundled_fallback"
                except Exception as e:
                    print(f"Failed to read {csv_path}: {e}")
                    source_type = "bundled_fallback"
            else:
                source_type = "bundled_fallback"

        if return_meta:
            return create_provider_result(series, source_type, symbol, details=self.last_source_used or self.name)
        return series
