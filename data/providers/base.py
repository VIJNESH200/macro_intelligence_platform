from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Optional, Literal
import pandas as pd


SourceType = Literal["live", "cache", "bundled_fallback"]


@dataclass
class ProviderMeta:
    """Metadata tracking data provenance, freshness, and integrity."""
    source: SourceType
    fetched_at: str      # ISO 8601 timestamp string
    series_id: str       # Symbol/ticker ID
    as_of: str | None    # Date string of most recent data point (e.g. 'Jun 2026')
    schema_ok: bool      # Structural validation boolean
    details: str = ""    # Optional extra context string

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ProviderResult:
    """Wrapper holding series payload alongside standardized metadata."""
    series: pd.Series
    meta: ProviderMeta


def create_provider_result(
    series: pd.Series,
    source: SourceType,
    series_id: str,
    details: str = ""
) -> ProviderResult:
    """Helper to construct a standardized ProviderResult with metadata."""
    from datetime import datetime, timezone
    fetched_at = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    valid = series.dropna()
    as_of = valid.index[-1].strftime('%Y-%m-%d') if not valid.empty else None
    schema_ok = (
        not series.empty
        and not valid.empty
        and isinstance(series.index, pd.DatetimeIndex)
    )
    meta = ProviderMeta(
        source=source,
        fetched_at=fetched_at,
        series_id=series_id,
        as_of=as_of,
        schema_ok=schema_ok,
        details=details
    )
    return ProviderResult(series=series, meta=meta)


class BaseProvider(ABC):
    """Interface that all data providers must implement."""

    def __init__(self):
        self.last_source_used = None

    @abstractmethod
    def fetch(self, symbol: str, start_date: str = '2000-01-01', end_date: Optional[str] = None, return_meta: bool = False) -> pd.Series | ProviderResult:
        """Fetch a single data series by symbol."""
        ...

    def fetch_with_meta(self, symbol: str, start_date: str = '2000-01-01', end_date: Optional[str] = None) -> ProviderResult:
        """Fetch a series and return a standardized ProviderResult with metadata."""
        res = self.fetch(symbol, start_date, end_date, return_meta=True)
        if isinstance(res, ProviderResult):
            return res
        return create_provider_result(res, "live", symbol)

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""
        ...

    @property
    @abstractmethod
    def update_frequency(self) -> str:
        """Expected update frequency: 'daily', 'monthly', 'quarterly'."""
        ...
