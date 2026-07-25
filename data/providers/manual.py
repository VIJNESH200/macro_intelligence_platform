from __future__ import annotations
import os
import pandas as pd
from .base import BaseProvider

class ManualProvider(BaseProvider):
    def __init__(self):
        super().__init__()
        # Store in ~/.macro_intelligence_platform/data
        self.data_dir = os.path.join(os.path.expanduser('~'), '.macro_intelligence_platform', 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        self.manual_file = os.path.join(self.data_dir, 'manual_inputs.csv')

    @property
    def name(self) -> str:
        return 'Manual'
    
    @property
    def update_frequency(self) -> str:
        return 'manual'
    
    def fetch(self, symbol: str, start_date: str = '2000-01-01', end_date: str = None) -> pd.Series:
        """
        Reads data from manual_inputs.csv if it exists.
        The CSV should have columns: Date, <Symbol>
        e.g., Date, INDPMI
        """
        if not os.path.exists(self.manual_file):
            print(f"Manual input file not found at {self.manual_file}. Please create it to supply {symbol} data.")
            return pd.Series(dtype=float)
            
        try:
            df = pd.read_csv(self.manual_file, parse_dates=['Date'], index_col='Date')
            if symbol in df.columns:
                series = df[symbol].dropna()
                # Resample to MS
                series = series.resample('MS').first().ffill()
                return series
            else:
                print(f"Symbol {symbol} not found in {self.manual_file}.")
                return pd.Series(dtype=float)
        except Exception as e:
            print(f"Failed to read manual input file: {e}")
            return pd.Series(dtype=float)
