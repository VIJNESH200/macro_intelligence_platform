"""Stub providers for future macro indicators (PMI, CPI, Yield Curve, Credit)."""
from .base import BaseProvider
import pandas as pd


class PMIProvider(BaseProvider):
    """Purchasing Managers' Index provider — stub for v2.1+."""

    @property
    def name(self) -> str:
        return 'PMI'

    @property
    def update_frequency(self) -> str:
        return 'monthly'

    def fetch(self, symbol: str, start_date: str = '2000-01-01',
              end_date: str | None = None) -> pd.Series:
        raise NotImplementedError("PMI provider not yet implemented. Planned for v2.1.")


class CPIProvider(BaseProvider):
    """Consumer Price Index provider — stub for v2.1+."""

    @property
    def name(self) -> str:
        return 'CPI'

    @property
    def update_frequency(self) -> str:
        return 'monthly'

    def fetch(self, symbol: str, start_date: str = '2000-01-01',
              end_date: str | None = None) -> pd.Series:
        raise NotImplementedError("CPI provider not yet implemented. Planned for v2.1.")


class YieldCurveProvider(BaseProvider):
    """Yield curve spread provider — stub for v2.1+."""

    @property
    def name(self) -> str:
        return 'YieldCurve'

    @property
    def update_frequency(self) -> str:
        return 'daily'

    def fetch(self, symbol: str, start_date: str = '2000-01-01',
              end_date: str | None = None) -> pd.Series:
        raise NotImplementedError("Yield curve provider not yet implemented. Planned for v2.1.")


class CreditProvider(BaseProvider):
    """Credit growth provider — stub for v2.1+."""

    @property
    def name(self) -> str:
        return 'Credit'

    @property
    def update_frequency(self) -> str:
        return 'monthly'

    def fetch(self, symbol: str, start_date: str = '2000-01-01',
              end_date: str | None = None) -> pd.Series:
        raise NotImplementedError("Credit provider not yet implemented. Planned for v2.1.")
