"""Local CSV cache with staleness checks and graceful fallback."""
import os
import hashlib
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path


class CacheManager:
    """Manages local CSV caching for fetched data series.

    - Cache files are stored in ~/.macro_intelligence_platform/cache/
    - Freshness threshold: 24 hours (configurable)
    - Falls back to stale cache if network fetch fails
    """

    def __init__(self, cache_dir: str | None = None, max_age_hours: int = 24):
        if cache_dir is None:
            cache_dir = os.path.join(
                os.path.expanduser('~'),
                '.macro_intelligence_platform', 'cache'
            )
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_age_hours = max_age_hours

    def _cache_path(self, key: str) -> Path:
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{safe_key}.csv"

    def is_fresh(self, key: str) -> bool:
        """Check if cached data exists and is within the freshness window."""
        path = self._cache_path(key)
        if not path.exists():
            return False
        age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
        return age < timedelta(hours=self.max_age_hours)

    def get(self, key: str) -> pd.DataFrame | None:
        """Retrieve cached DataFrame, or None if not available."""
        path = self._cache_path(key)
        if path.exists():
            try:
                return pd.read_csv(path, index_col=0, parse_dates=True)
            except Exception:
                return None
        return None

    def put(self, key: str, data: pd.DataFrame | pd.Series) -> None:
        """Store data to cache."""
        path = self._cache_path(key)
        if isinstance(data, pd.Series):
            data = data.to_frame()
        data.to_csv(path)

    def has_any(self, key: str) -> bool:
        """Check if any cache exists (regardless of staleness)."""
        return self._cache_path(key).exists()
