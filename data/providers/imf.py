import pandas as pd
import sdmx
from datetime import datetime
from .base import BaseProvider
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
    
    def fetch(self, symbol: str, start_date: str = '2010', end_date: str = None) -> pd.Series:
        """
        Fetch data from api.imf.org using sdmx1 library.
        symbol format is the SDMX key, e.g., 'IND.CPI._T.IX.M' or 'IND.IND.IX.M'.
        Wait, CPI dataflow is 'CPI', IIP (PI) dataflow is 'PI'. We can parse this from the symbol structure or
        we can assume the symbol holds a prefix for the dataflow or we just figure it out.
        If symbol contains CPI, it's CPI dataflow, else PI.
        """
        try:
            client = sdmx.Client('IMF_DATA')
            # Extract dataflow from symbol or just hardcode based on symbol contents.
            # CPI key: IND.CPI._T.IX.M -> contains CPI
            # PI key: IND.IND.IX.M -> does not contain CPI.
            if 'CPI' in symbol:
                dataflow = 'CPI'
            else:
                dataflow = 'PI'
                
            msg = client.data(dataflow, key=symbol, params={'startPeriod': start_date[:4]})
            df = sdmx.to_pandas(msg).reset_index()
            
            # The 'TIME_PERIOD' column is formatted as 'YYYY-MM'
            # Convert to datetime and set as index
            df['TIME_PERIOD'] = pd.to_datetime(df['TIME_PERIOD'], format='%Y-M%m')
            df.set_index('TIME_PERIOD', inplace=True)
            
            # The actual values are in the 'value' column
            series = df['value']
            
            # Resample to month-start and forward fill to standardize
            series = series.resample('MS').first().ffill()
            return series
            
        except Exception as e:
            print(f"IMF fetch failed for {symbol}: {e}")
            return pd.Series(dtype=float)
