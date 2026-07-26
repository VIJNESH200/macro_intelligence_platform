from __future__ import annotations
"""
Core Data Models & Structured Result Containers.
===============================================
Defines typed dataclasses for data loading payloads (DataBundle)
and forecast outputs (ForecastResult) with JSON serialization.
"""
import json
from dataclasses import dataclass, field, asdict
from typing import Any
import pandas as pd


@dataclass
class DataBundle:
    """Container holding merged data payload alongside provider metadata."""
    df: pd.DataFrame
    data_health: dict[str, dict]
    as_of: str
    config: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            'as_of': self.as_of,
            'data_health': self.data_health,
            'config': self.config,
            'data_rows': len(self.df)
        }


@dataclass
class HorizonForecast:
    """Projection result for a specific forward horizon (e.g. 3m, 6m)."""
    x: float
    y: float
    quadrant: str
    conviction: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ForecastResult:
    """Complete structured forecast result from cycle evaluation."""
    as_of: str
    current_regime: str
    forecasts: dict[str, HorizonForecast]
    signal_contributions: dict[str, dict]
    conviction: float
    model_version: str
    data_health: dict[str, dict]
    projected_path: list[tuple[float, float]]
    confidence_band: dict[str, Any]
    residual_std: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return {
            'as_of': self.as_of,
            'current_regime': self.current_regime,
            'forecasts': {k: v.to_dict() if isinstance(v, HorizonForecast) else v for k, v in self.forecasts.items()},
            'signal_contributions': self.signal_contributions,
            'conviction': self.conviction,
            'model_version': self.model_version,
            'data_health': self.data_health,
            'projected_path': self.projected_path,
            'confidence_band': self.confidence_band,
            'residual_std': self.residual_std
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize ForecastResult to formatted JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def validate_schema(self) -> bool:
        """Validate structural compliance of ForecastResult instance."""
        d = self.to_dict()
        required_keys = {'as_of', 'current_regime', 'forecasts', 'conviction', 'model_version', 'data_health'}
        if not required_keys.issubset(d.keys()):
            return False
        if not isinstance(d['forecasts'], dict) or '6m' not in d['forecasts']:
            return False
        f6m = d['forecasts']['6m']
        if not all(k in f6m for k in ['x', 'y', 'quadrant', 'conviction']):
            return False
        return True
