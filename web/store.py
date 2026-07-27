from __future__ import annotations
"""
Market Store — Cached, serialized access to per-market computed state.
======================================================================
The compute layer keeps the active market in module-level globals
(`config.CONFIG`, `config.MARKET_SERIES`, `config.MACRO_SERIES`), which
`reload_for_market()` mutates in place. Several engines read those globals at
call time rather than taking them as arguments — `FeatureEngine.compute_macro_features`,
`MacroIntelligenceEngine`, and `analytics.market_insights` all do.

That is fine for a single-user desktop app driving one figure. It is not safe
for a server handling interleaved requests for different markets. So every
computation runs inside `session(market)`, which holds a reentrant lock while
the globals point at the requested market.

Loading a market is expensive (network fetches for every series), so each
market's DataFrame is computed once and cached. Cache entries are immutable
snapshots: callers get a private copy of the config dicts and must not mutate
the frame.
"""
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from contextlib import contextmanager
from typing import Callable, Iterator

import pandas as pd

try:
    from ..config import (CONFIG, MARKET_SERIES, MACRO_SERIES, VERSION,
                          get_current_market, reload_for_market)
    from ..config.markets import MARKET_PROFILES
    from ..data.data_engine import DataEngine
    from ..features.feature_engine import FeatureEngine
except ImportError:
    from config import (CONFIG, MARKET_SERIES, MACRO_SERIES, VERSION,
                        get_current_market, reload_for_market)
    from config.markets import MARKET_PROFILES
    from data.data_engine import DataEngine
    from features.feature_engine import FeatureEngine


KNOWN_MARKETS: tuple[str, ...] = tuple(MARKET_PROFILES.keys())

# Roughly one market's worth of frames. Scrubbing revisits frames constantly,
# and the engine chain behind a frame is expensive, so keeping the recent window
# resident is what makes dragging the scrubber feel immediate.
BUNDLE_CACHE_SIZE = 320


class UnknownMarketError(ValueError):
    """Raised when a caller asks for a market that has no profile."""


@dataclass(frozen=True)
class MarketSnapshot:
    """Fully computed, immutable state for one market."""
    market: str
    label: str
    df: pd.DataFrame
    spline: pd.DataFrame
    config: dict
    market_series: dict
    macro_series: dict
    data_health: dict
    warnings: tuple[str, ...]
    as_of: str
    loaded_at: float
    domestic_indices: tuple[str, ...] = field(default=())
    global_indices: tuple[str, ...] = field(default=())

    @property
    def frame_count(self) -> int:
        return len(self.df)

    @property
    def last_index(self) -> int:
        return max(0, len(self.df) - 1)

    def clamp(self, idx: int | None) -> int:
        """Clamp a caller-supplied frame index into the valid range."""
        if idx is None:
            return self.last_index
        return max(0, min(int(idx), self.last_index))


def normalize_market(market: str | None) -> str:
    """Validate and canonicalize a market identifier."""
    if market is None:
        return get_current_market()
    candidate = market.strip().upper()
    if candidate not in MARKET_PROFILES:
        raise UnknownMarketError(
            f"Unknown market {market!r}. Choose from {list(MARKET_PROFILES)}"
        )
    return candidate


class MarketStore:
    """Loads, caches, and hands out per-market computed state under a lock."""

    def __init__(self, offline: bool = False):
        self._offline = offline
        self._lock = threading.RLock()
        self._snapshots: dict[str, MarketSnapshot] = {}
        self._bundles: OrderedDict[tuple, dict] = OrderedDict()

    # ------------------------------------------------------------------
    # Per-frame memoization
    # ------------------------------------------------------------------
    def cached_bundle(self, key: tuple, factory: Callable[[], dict]) -> dict:
        """Return a memoized engine result for `key`, computing it on a miss.

        `/api/frame` and `/api/forecast` are two views of one expensive
        computation, and the client requests both for every scrub position.
        Without this the engine chain runs twice per frame and a drag queues
        dozens of duplicate runs behind the lock.
        """
        with self._lock:
            hit = self._bundles.get(key)
            if hit is not None:
                self._bundles.move_to_end(key)
                return hit

            value = factory()
            self._bundles[key] = value
            while len(self._bundles) > BUNDLE_CACHE_SIZE:
                self._bundles.popitem(last=False)
            return value

    # ------------------------------------------------------------------
    # Global-state management
    # ------------------------------------------------------------------
    def _activate(self, market: str) -> None:
        """Point the compute layer's module globals at `market`.

        Caller must hold the lock.
        """
        if get_current_market() != market:
            reload_for_market(market)

    @contextmanager
    def session(self, market: str | None = None) -> Iterator[MarketSnapshot]:
        """Hold the lock with the globals pinned to `market`, yielding its snapshot.

        Every call into the analytics engines must happen inside this block,
        because they read `config.MACRO_SERIES` and friends at call time.
        """
        resolved = normalize_market(market)
        with self._lock:
            self._activate(resolved)
            yield self._load_locked(resolved)

    # ------------------------------------------------------------------
    # Loading & caching
    # ------------------------------------------------------------------
    def _load_locked(self, market: str) -> MarketSnapshot:
        """Return the cached snapshot for `market`, computing it if absent.

        Caller must hold the lock and have already activated `market`.
        """
        cached = self._snapshots.get(market)
        if cached is not None:
            return cached

        profile = MARKET_PROFILES[market]
        engine = DataEngine(CONFIG, MARKET_SERIES, MACRO_SERIES, offline=self._offline)
        df = engine.load_all()
        df, spline = FeatureEngine.compute_all(df, CONFIG)

        non_empty = df.dropna(how='all')
        last_date = non_empty.index[-1] if len(non_empty) else pd.Timestamp.now()

        snapshot = MarketSnapshot(
            market=market,
            label=profile['label'],
            df=df,
            spline=spline,
            config=dict(CONFIG),
            market_series=dict(MARKET_SERIES),
            macro_series=dict(MACRO_SERIES),
            data_health=dict(engine.get_metadata),
            warnings=tuple(engine.load_warnings),
            as_of=last_date.strftime('%Y-%m-%d'),
            loaded_at=time.time(),
            domestic_indices=tuple(profile.get('domestic_indices', ())),
            global_indices=tuple(profile.get('global_indices', ())),
        )
        self._snapshots[market] = snapshot
        return snapshot

    def invalidate(self, market: str | None = None) -> list[str]:
        """Drop cached snapshots so the next request refetches. Returns dropped markets."""
        with self._lock:
            if market is None:
                dropped = list(self._snapshots)
                self._snapshots.clear()
                self._bundles.clear()
                return dropped

            resolved = normalize_market(market)
            self._snapshots.pop(resolved, None)
            # Frame results are derived from the snapshot, so they expire with it.
            for key in [k for k in self._bundles if k[0] == resolved]:
                del self._bundles[key]
            return [resolved]

    def loaded_markets(self) -> list[str]:
        """Markets currently held in cache."""
        with self._lock:
            return list(self._snapshots)


STORE = MarketStore()
