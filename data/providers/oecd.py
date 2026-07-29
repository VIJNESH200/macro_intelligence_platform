import pandas as pd
from .base import BaseProvider, ProviderResult, create_provider_result
from .fred import FREDProvider

class OECDProvider(BaseProvider):
    """Organization for Economic Co-operation and Development (OECD) provider."""
    
    def __init__(self):
        super().__init__()
        self.proxy = FREDProvider()
        
    @property
    def name(self) -> str:
        return 'OECD'
        
    @property
    def update_frequency(self) -> str:
        return 'monthly'
        
    def fetch(self, symbol: str, start_date: str = '2000-01-01', end_date: str | None = None, return_meta: bool = False) -> pd.Series | ProviderResult:
        res = self.proxy.fetch(symbol, start_date, end_date, return_meta=True)
        if return_meta:
            return ProviderResult(
                series=res.series,
                source='oecd',
                series_id=res.series_id,
                as_of=res.as_of,
                fetched_at=res.fetched_at,
                schema_ok=res.schema_ok,
                details=f"OECD CLI via FRED proxy ({res.details})"
            )
        return res.series
