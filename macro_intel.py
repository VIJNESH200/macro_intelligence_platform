from __future__ import annotations
"""
Public Package Alias (`macro_intel`).
====================================
Provides the top-level convenience import contract:

    from macro_intel import load_macro_data, compute_features, forecast_cycle
"""
try:
    from .api import load_macro_data, compute_features, forecast_cycle
    from .models import DataBundle, ForecastResult, HorizonForecast
except ImportError:
    from api import load_macro_data, compute_features, forecast_cycle
    from models import DataBundle, ForecastResult, HorizonForecast

__all__ = [
    'load_macro_data',
    'compute_features',
    'forecast_cycle',
    'DataBundle',
    'ForecastResult',
    'HorizonForecast'
]
