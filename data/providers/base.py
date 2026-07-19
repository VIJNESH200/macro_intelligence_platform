"""Abstract base class for data providers."""
from abc import ABC, abstractmethod
import pandas as pd


class BaseProvider(ABC):
    """Interface that all data providers must implement."""
    
    def __init__(self):
        self.last_source_used = None

    @abstractmethod
    def fetch(self, symbol: str, start_date: str, end_date: str | None = None) -> pd.Series:
        """Fetch a single data series by symbol.

        Returns a DatetimeIndex-ed Series resampled to month-start.
        """
        ...

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
