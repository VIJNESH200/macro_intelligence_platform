from __future__ import annotations
import pandas as pd
import sdmx
from datetime import datetime
from .base import BaseProvider, ProviderResult, create_provider_result
import warnings

class IMFProvider(BaseProvider):
    def __init__(self):
        super().__init__()
        # Suppress sdmx1 UserWarnings about missing structure args for data retrieval
        warnings.filterwarnings('ignore', module='sdmx')

    @property
    def name(self) -> str:
        return 'IMF'
    
    @property
    def update_frequency(self) -> str:
        return 'monthly'
    
    def fetch(self, symbol: str, start_date: str = '2010', end_date: str = None, return_meta: bool = False) -> pd.Series | ProviderResult:
        """Fetch macroeconomic series from api.imf.org using SDMX."""
        source_type = "live"
        try:
            client = sdmx.Client('IMF_DATA')
            if 'CPI' in symbol:
                dataflow = 'CPI'
            else:
                dataflow = 'PI'
                
            params = {'startPeriod': start_date[:4]}
            if end_date:
                params['endPeriod'] = end_date[:4]
                
            msg = client.data(dataflow, key=symbol, params=params)
            df = sdmx.to_pandas(msg).reset_index()
            
            df['TIME_PERIOD'] = pd.to_datetime(df['TIME_PERIOD'], format='%Y-M%m')
            df.set_index('TIME_PERIOD', inplace=True)
            series = df['value']
            series = series.resample('MS').first().ffill()
            if end_date:
                series = series[series.index <= pd.Timestamp(end_date)]
            self.last_source_used = 'IMF SDMX API'
            
        except Exception as e:
            print(f"IMF fetch failed for {symbol}: {e}")
            series = pd.Series(dtype=float)
            source_type = "bundled_fallback"

        if return_meta:
            return create_provider_result(series, source_type, symbol, details=self.name)
        return series
