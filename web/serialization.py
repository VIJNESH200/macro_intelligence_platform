from __future__ import annotations
"""
JSON Serialization Helpers.
===========================
The compute layer speaks numpy/pandas. JSON does not: `NaN` and `Infinity`
are not valid JSON literals, and `np.float64` is not a `float` as far as the
stdlib encoder is concerned.

`to_jsonable` normalizes any payload coming out of the analytics engines into
something `json.dumps` accepts, mapping every non-finite float to `None` so the
frontend sees a single, unambiguous "no value" sentinel.
"""
import math
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from typing import Any

import numpy as np
import pandas as pd


def _finite_or_none(value: float) -> float | None:
    """Map NaN and +/-Infinity to None; pass finite floats through."""
    return value if math.isfinite(value) else None


def to_jsonable(value: Any) -> Any:
    """Recursively convert numpy/pandas/dataclass payloads into JSON-safe values."""
    if value is None or isinstance(value, (str, bool)):
        return value

    if isinstance(value, float):
        return _finite_or_none(value)

    if isinstance(value, int):
        return value

    if isinstance(value, (np.bool_,)):
        return bool(value)

    if isinstance(value, np.integer):
        return int(value)

    if isinstance(value, np.floating):
        return _finite_or_none(float(value))

    if isinstance(value, (np.ndarray,)):
        return [to_jsonable(v) for v in value.tolist()]

    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.isoformat()

    if isinstance(value, pd.Series):
        return {str(k): to_jsonable(v) for k, v in value.items()}

    if isinstance(value, pd.DataFrame):
        return [to_jsonable(row) for row in value.to_dict(orient='records')]

    if value is pd.NaT:
        return None

    if is_dataclass(value) and not isinstance(value, type):
        return to_jsonable(asdict(value))

    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(v) for v in value]

    if hasattr(value, 'to_dict'):
        return to_jsonable(value.to_dict())

    return str(value)
