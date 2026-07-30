from __future__ import annotations
"""
Public Python API for Macro Intelligence Platform.
=================================================
Exposes a clean, notebook-friendly, non-GUI API:

    from macro_intelligence_platform.api import load_macro_data, compute_features, forecast_cycle

    bundle = load_macro_data(offline=True)     # -> DataBundle
    bundle = compute_features(bundle)           # -> DataBundle with X, Y, Quadrant
    forecast = forecast_cycle(bundle)           # -> ForecastResult
"""
from typing import Optional
import pandas as pd

try:
    from .config import CONFIG, MARKET_SERIES, MACRO_SERIES, VERSION
    from .config.markets import get_market_config
    from .data.data_engine import DataEngine
    from .features.feature_engine import FeatureEngine
    from .analytics.forecasting_engine import ForecastingEngine
    from .analytics.historical_analogues import generate_analogues
    from .analytics.macro_intelligence_engine import MacroIntelligenceEngine
    from .research.report_data import extract_report_data
    from .models import DataBundle, ForecastResult, HorizonForecast
except ImportError:
    from config import CONFIG, MARKET_SERIES, MACRO_SERIES, VERSION
    from config.markets import get_market_config
    from data.data_engine import DataEngine
    from features.feature_engine import FeatureEngine
    from analytics.forecasting_engine import ForecastingEngine
    from analytics.historical_analogues import generate_analogues
    from analytics.macro_intelligence_engine import MacroIntelligenceEngine
    from research.report_data import extract_report_data
    from models import DataBundle, ForecastResult, HorizonForecast


def load_macro_data(config: dict | None = None,
                    market_series: dict | None = None,
                    macro_series: dict | None = None,
                    offline: bool = False,
                    market: str | None = None) -> DataBundle:
    """Load macroeconomic and market series into a :class:`DataBundle`.

    Pass ``market="INDIA"`` or ``market="US"`` to select a built-in market
    profile without changing the application-wide market preference. Custom
    ``config``, ``market_series``, and ``macro_series`` remain available for
    advanced callers, but cannot be combined with ``market``.
    """
    if market is not None:
        if any(value is not None for value in (config, market_series, macro_series)):
            raise ValueError("market cannot be combined with custom configuration arguments")
        market_name = market.upper()
        profile = get_market_config(market_name)
        cfg = {**profile['primary_indicator'], 'version': VERSION, '_market': market_name}
        mkt = profile['market_series']
        mac = profile['macro_series']
    else:
        cfg = config or CONFIG
        mkt = market_series or MARKET_SERIES
        mac = macro_series or MACRO_SERIES

    engine = DataEngine(cfg, mkt, mac, offline=offline)
    return engine.load_all_bundle()


def compute_features(bundle: DataBundle, config: dict | None = None) -> DataBundle:
    """Compute X (Health), Y (Momentum), Velocity, Quadrants, and spline data."""
    cfg = config or bundle.config or CONFIG
    df_feat, _ = FeatureEngine.compute_all(bundle.df, cfg)
    return DataBundle(
        df=df_feat,
        data_health=bundle.data_health,
        as_of=bundle.as_of,
        config=cfg
    )


def forecast_cycle(bundle: DataBundle,
                   idx: Optional[int] = None,
                   config: dict | None = None) -> ForecastResult:
    """Compute cycle projections forward and return a structured ForecastResult."""
    cfg = config or bundle.config or CONFIG
    df = bundle.df

    if 'X' not in df.columns or 'Y' not in df.columns:
        bundle = compute_features(bundle, cfg)
        df = bundle.df

    if idx is None:
        idx = int(len(df) - 1)
    else:
        idx = int(idx)

    plot_elements = {'market_state': {'selected': []}}
    market_name = cfg.get('_market')
    market_config = (get_market_config(market_name)['market_series']
                     if market_name else MARKET_SERIES)
    report_data = extract_report_data(df, cfg, plot_elements, idx, market_config)
    analogues = generate_analogues(df, idx, report_data, market_config)
    macro_contrib = report_data.get('macro_contrib')

    raw_forecast = ForecastingEngine.project(df, idx, cfg, analogues, macro_contrib)

    current_regime = df['Quadrant'].iloc[idx]
    as_of = df.index[idx].strftime('%Y-%m-%d')

    forecasts_dict = {}
    for h in cfg.get('horizons', [3, 6, 9]):
        key = f'forecast_{h}m'
        if key in raw_forecast:
            f = raw_forecast[key]
            forecasts_dict[f'{h}m'] = HorizonForecast(
                x=f['x'],
                y=f['y'],
                quadrant=f['quadrant'],
                conviction=f['conviction']
            )

    headline_conviction = forecasts_dict.get('6m', list(forecasts_dict.values())[0]).conviction if forecasts_dict else 50.0

    return ForecastResult(
        as_of=as_of,
        current_regime=current_regime,
        forecasts=forecasts_dict,
        signal_contributions=raw_forecast.get('method_contributions', {}),
        conviction=headline_conviction,
        model_version=VERSION,
        data_health=bundle.data_health,
        projected_path=raw_forecast.get('projected_path', []),
        confidence_band=raw_forecast.get('confidence_band', {}),
        residual_std=raw_forecast.get('residual_std', {})
    )
