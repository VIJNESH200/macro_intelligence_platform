from __future__ import annotations
"""
Compute Composition — Assembles engine output into API payloads.
================================================================
The analytics engines each take a DataFrame and an index and return a dict.
Composing them in the right order is currently duplicated inside the
matplotlib export handler (`ui/app.py`); this module is the same composition,
expressed once, with no GUI objects involved.

Every function here assumes the caller already holds a `MarketStore.session`,
because the engines read the active market from module globals.
"""
from typing import Sequence

import numpy as np
import pandas as pd

try:
    from ..analytics import cycle_statistics, insights as insights_mod
    from ..analytics import market_insights as market_insights_mod
    from ..analytics import transition_matrix as transition_mod
    from ..analytics import deltas as deltas_mod
    from ..analytics.forecasting_engine import ForecastingEngine
    from ..analytics.historical_analogues import generate_analogues
    from ..analytics.scenario_engine import ScenarioEngine
    from ..research import narrative as narrative_mod
    from ..research.report_data import extract_report_data
    from .store import MarketSnapshot
except ImportError:
    from analytics import cycle_statistics, insights as insights_mod
    from analytics import market_insights as market_insights_mod
    from analytics import transition_matrix as transition_mod
    from analytics import deltas as deltas_mod
    from analytics.forecasting_engine import ForecastingEngine
    from analytics.historical_analogues import generate_analogues
    from analytics.scenario_engine import ScenarioEngine
    from research import narrative as narrative_mod
    from research.report_data import extract_report_data
    from web.store import MarketSnapshot


MIN_AXIS_EXTENT = 3.0
QUADRANT_ORDER = ('Expansion', 'Slowdown', 'Contraction', 'Recovery')


def _plot_elements(selected: Sequence[str]) -> dict:
    """Build the minimal `plot_elements` shape the report extractor expects.

    `extract_report_data` only reads `market_state.selected` from this; the rest
    of the GUI's plot_elements dict is irrelevant off-screen.
    """
    return {'market_state': {'selected': list(selected)}}


def resolve_assets(snapshot: MarketSnapshot, assets: Sequence[str] | None) -> list[str]:
    """Pick which market series to include, defaulting to all of them."""
    if not assets:
        return list(snapshot.market_series)
    available = set(snapshot.market_series)
    return [a for a in assets if a in available]


def axis_bounds(snapshot: MarketSnapshot) -> dict:
    """Compute chart extents the same way `ui/layout.create_main_axes` does.

    Uses the 98th percentile of deviation from centre so a handful of extreme
    months (2020, say) don't inflate the quadrants for every other frame.
    """
    df, config = snapshot.df, snapshot.config
    center = float(config.get('center', 100))
    padding = float(config.get('padding', 0.10))

    dev_x = float((df['X'] - center).abs().quantile(0.98))
    dev_y = float((df['Y'] - center).abs().quantile(0.98))
    max_dist = max(dev_x, dev_y) * (1 + padding)
    max_dist = max(max_dist, MIN_AXIS_EXTENT)

    return {
        'center': center,
        'min': center - max_dist,
        'max': center + max_dist,
        'extent': max_dist,
    }


def _raw_value(snapshot: MarketSnapshot, idx: int) -> float | None:
    """The underlying indicator level at `idx`, before Z-scoring."""
    df = snapshot.df
    if 'CLI_Raw' not in df.columns:
        return None
    value = df['CLI_Raw'].iloc[snapshot.clamp(idx)]
    return float(value) if pd.notna(value) else None


def phase_context(snapshot: MarketSnapshot, idx: int) -> dict:
    """When the current quadrant was entered, how long it has run, what preceded it.

    Same walk-back the desktop sidebar performs in `App.draw_frame`.
    """
    df = snapshot.df
    frame = snapshot.clamp(idx)
    current = df['Quadrant'].iloc[frame]

    entry = frame
    while entry > 0 and df['Quadrant'].iloc[entry - 1] == current:
        entry -= 1

    previous = df['Quadrant'].iloc[entry - 1] if entry > 0 else None

    return {
        'quadrant': current,
        'entered': df.index[entry].strftime('%Y-%m-%d'),
        'entered_label': df.index[entry].strftime('%b %Y'),
        'duration_months': frame - entry + 1,
        'previous_quadrant': previous,
    }


def cycle_payload(snapshot: MarketSnapshot) -> dict:
    """The full time series a client needs to render and scrub the cycle chart."""
    df = snapshot.df
    config = snapshot.config
    ticker = config.get('ticker')

    raw = df[ticker] if ticker in df.columns else df.get('CLI_Raw', pd.Series(dtype=float))

    frames = [
        {
            'i': i,
            'date': timestamp.strftime('%Y-%m-%d'),
            'label': timestamp.strftime('%b %Y'),
            'x': float(x),
            'y': float(y),
            'velocity': float(v) if pd.notna(v) else None,
            'quadrant': quadrant,
            'raw': float(r) if pd.notna(r) else None,
        }
        for i, (timestamp, x, y, v, quadrant, r) in enumerate(zip(
            df.index, df['X'], df['Y'],
            df['Velocity'] if 'Velocity' in df.columns else [np.nan] * len(df),
            df['Quadrant'],
            raw if len(raw) == len(df) else [np.nan] * len(df),
        ))
    ]

    spline = [
        {'t': float(t), 'x': float(x), 'y': float(y)}
        for t, x, y in zip(snapshot.spline['t'], snapshot.spline['X'], snapshot.spline['Y'])
    ]

    return {
        'market': snapshot.market,
        'label': snapshot.label,
        'as_of': snapshot.as_of,
        'config': {
            'name': config.get('name'),
            'ticker': ticker,
            'source': config.get('source'),
            'frequency': config.get('frequency'),
            'window': config.get('window'),
            'center': config.get('center'),
            'tail_length': config.get('tail_length'),
        },
        'bounds': axis_bounds(snapshot),
        'frames': frames,
        'spline': spline,
        'points_per_segment': config.get('points_per_segment', 10),
        'data_health': snapshot.data_health,
        'warnings': list(snapshot.warnings),
        'market_series': {
            name: {'type': info.get('type'), 'symbol': info.get('symbol')}
            for name, info in snapshot.market_series.items()
        },
        'domestic_indices': list(snapshot.domestic_indices),
        'global_indices': list(snapshot.global_indices),
    }


def analysis_bundle(snapshot: MarketSnapshot, idx: int,
                    assets: Sequence[str] | None = None) -> dict:
    """Run the full engine chain for one frame, memoized per (market, frame, assets).

    Mirrors the composition in `ui/app.py`'s PDF export path so the web view and
    the PDF report never diverge. The result is cached because the frame and
    forecast endpoints are two views of this one computation and the client asks
    for both on every scrub.
    """
    try:
        from .store import STORE
    except ImportError:
        from web.store import STORE

    frame = snapshot.clamp(idx)
    selected = resolve_assets(snapshot, assets)
    key = (snapshot.market, snapshot.loaded_at, frame, tuple(selected))

    return STORE.cached_bundle(key, lambda: _compute_bundle(snapshot, frame, selected))


def _compute_bundle(snapshot: MarketSnapshot, idx: int, selected: list[str]) -> dict:
    """The uncached engine chain. Callers should use `analysis_bundle`."""
    df = snapshot.df
    config = snapshot.config
    frame = idx

    df_sliced = df.iloc[:frame + 1]
    elements = _plot_elements(selected)

    data = extract_report_data(df, config, elements, frame, snapshot.market_series)
    analysis = cycle_statistics.compute_statistics(df_sliced, data)
    flags = insights_mod.generate_insights(data, analysis)
    market_ins = market_insights_mod.generate_market_insights(data)
    analogues = generate_analogues(df, frame, data, snapshot.market_series)

    transitions = transition_mod.compute_transition_matrix(df_sliced)
    forecast = ForecastingEngine.project(df, frame, config, analogues, data.get('macro_contrib'))
    scenarios = ScenarioEngine.generate_scenarios(
        forecast, transitions, analogues, data['quadrant'], config
    )

    data['transition_matrix'] = transitions
    data['forecast'] = forecast
    data['scenarios'] = scenarios

    deltas = deltas_mod.calculate_deltas(
        df, frame, config, elements, snapshot.market_series, data, analysis, flags
    )
    narrative = narrative_mod.generate_narrative(data, analysis, flags, market_ins, analogues)

    return {
        'index': frame,
        'data': data,
        'analysis': analysis,
        'insights': flags,
        'market_insights': market_ins,
        'analogues': analogues,
        'transitions': transitions,
        'forecast': forecast,
        'scenarios': scenarios,
        'deltas': deltas,
        'narrative': narrative,
        'selected_assets': selected,
    }


def frame_payload(snapshot: MarketSnapshot, idx: int,
                  assets: Sequence[str] | None = None) -> dict:
    """Per-frame view model: everything the sidebars and panels display."""
    bundle = analysis_bundle(snapshot, idx, assets)
    data = bundle['data']

    return {
        'market': snapshot.market,
        'index': bundle['index'],
        'date': data.get('date'),
        'quadrant': data.get('quadrant'),
        'health': data.get('health_val'),
        'momentum': data.get('momentum_val'),
        'center': data.get('center'),
        'distance': data.get('distance'),
        'direction': data.get('direction'),
        'indicator': data.get('indicator'),
        'source': data.get('source'),
        'window': data.get('window'),
        'raw_value': _raw_value(snapshot, bundle['index']),
        'phase': phase_context(snapshot, bundle['index']),
        'macro_contrib': data.get('macro_contrib'),
        'macro_shifts': data.get('macro_shifts'),
        'research_narrative': data.get('research_narrative'),
        'market_data': data.get('market_data'),
        'analysis': bundle['analysis'],
        'insights': bundle['insights'],
        'market_insights': bundle['market_insights'],
        'analogues': bundle['analogues'],
        'narrative': bundle['narrative'],
        'deltas': bundle['deltas'],
        'selected_assets': bundle['selected_assets'],
    }


def forecast_payload(snapshot: MarketSnapshot, idx: int,
                     assets: Sequence[str] | None = None) -> dict:
    """Forward projection, confidence bands, scenarios, and transition matrix."""
    bundle = analysis_bundle(snapshot, idx, assets)
    forecast = bundle['forecast']
    config = snapshot.config
    horizons = config.get('horizons', [3, 6, 9])

    horizon_forecasts = {
        f'{h}m': forecast[f'forecast_{h}m']
        for h in horizons
        if f'forecast_{h}m' in forecast
    }
    headline = horizon_forecasts.get('6m') or next(iter(horizon_forecasts.values()), None)

    return {
        'market': snapshot.market,
        'index': bundle['index'],
        'as_of': snapshot.as_of,
        'current_regime': bundle['data'].get('quadrant'),
        'forecasts': horizon_forecasts,
        'conviction': headline.get('conviction') if headline else None,
        'projected_path': forecast.get('projected_path', []),
        'confidence_band': forecast.get('confidence_band', {}),
        'residual_std': forecast.get('residual_std', {}),
        'signal_contributions': forecast.get('method_contributions', {}),
        'scenarios': bundle['scenarios'],
        'transitions': bundle['transitions'],
        'analogues': bundle['analogues'],
        'model_version': config.get('version'),
    }


def series_payload(snapshot: MarketSnapshot, names: Sequence[str]) -> dict:
    """Raw column values keyed by name, for sparklines and secondary charts."""
    df = snapshot.df
    dates = [ts.strftime('%Y-%m-%d') for ts in df.index]

    series = {
        name: [float(v) if pd.notna(v) else None for v in df[name]]
        for name in names
        if name in df.columns
    }
    missing = [name for name in names if name not in df.columns]

    return {'market': snapshot.market, 'dates': dates, 'series': series, 'missing': missing}
