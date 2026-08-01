from __future__ import annotations
"""
FastAPI Service — HTTP surface over the compute layer.
======================================================
Run it:

    uvicorn web.server:app --reload --port 8000

Endpoints are read-only apart from cache invalidation and report generation.
All market-specific work happens inside a `MarketStore.session`, which pins the
compute layer's module globals to the requested market for the duration of the
call. See `web/store.py` for why that matters.
"""
import datetime
import os
import tempfile
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from starlette.background import BackgroundTask
from fastapi.staticfiles import StaticFiles

try:
    from ..config import VERSION
    from ..config.markets import MARKET_PROFILES
    from . import compute
    from .chart import render_cycle_png
    from .serialization import to_jsonable
    from .store import STORE, UnknownMarketError, normalize_market
except ImportError:
    from config import VERSION
    from config.markets import MARKET_PROFILES
    from web import compute
    from web.chart import render_cycle_png
    from web.serialization import to_jsonable
    from web.store import STORE, UnknownMarketError, normalize_market


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIST = os.path.join(BASE_DIR, 'web', 'frontend', 'dist')
EXPORT_DIR = os.path.join(tempfile.gettempdir(), 'macro_platform_exports')

app = FastAPI(
    title='Macro Intelligence Platform API',
    version=VERSION,
    description='Economic regime tracing, forecasting, and market context.',
)

raw_origins = os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000')
allowed_origins = [o.strip() for o in raw_origins.split(',') if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=['GET', 'POST', 'OPTIONS'],
    allow_headers=['*'],
)


def ok(payload: Any) -> JSONResponse:
    """Serialize a payload, scrubbing NaN/Inf that would produce invalid JSON."""
    return JSONResponse(content=to_jsonable(payload))


@app.exception_handler(UnknownMarketError)
async def _unknown_market_handler(_request, exc: UnknownMarketError):
    return JSONResponse(status_code=404, content={'detail': str(exc)})


def _parse_assets(assets: str | None) -> list[str] | None:
    """Split a comma-separated `assets` query parameter."""
    if not assets:
        return None
    return [a.strip() for a in assets.split(',') if a.strip()]


# ----------------------------------------------------------------------
# Metadata
# ----------------------------------------------------------------------
@app.get('/api/health')
def health() -> JSONResponse:
    """Liveness plus which markets are already warm in cache."""
    return ok({
        'status': 'ok',
        'version': VERSION,
        'markets': list(MARKET_PROFILES),
        'loaded': STORE.loaded_markets(),
    })


@app.get('/api/markets')
def markets() -> JSONResponse:
    """Available market profiles and the series each one tracks."""
    return ok([
        {
            'id': market,
            'label': profile['label'],
            'indicator': profile['primary_indicator']['name'],
            'ticker': profile['primary_indicator']['ticker'],
            'market_series': list(profile['market_series']),
            'macro_series': list(profile['macro_series']),
            'domestic_indices': profile.get('domestic_indices', []),
            'global_indices': profile.get('global_indices', []),
        }
        for market, profile in MARKET_PROFILES.items()
    ])


# ----------------------------------------------------------------------
# Cycle data
# ----------------------------------------------------------------------
@app.get('/api/cycle')
def cycle(market: str | None = Query(None)) -> JSONResponse:
    """Full cycle time series: frames, spline path, axis bounds, data health."""
    with STORE.session(market) as snapshot:
        return ok(compute.cycle_payload(snapshot))


@app.get('/api/frame/{idx}')
def frame(idx: int, market: str | None = Query(None),
          assets: str | None = Query(None)) -> JSONResponse:
    """Everything the panels display for a single point in time."""
    with STORE.session(market) as snapshot:
        return ok(compute.frame_payload(snapshot, idx, _parse_assets(assets)))


@app.get('/api/forecast')
def forecast(market: str | None = Query(None), idx: int | None = Query(None),
             assets: str | None = Query(None)) -> JSONResponse:
    """Forward projection, confidence bands, scenarios, transition matrix."""
    with STORE.session(market) as snapshot:
        return ok(compute.forecast_payload(snapshot, snapshot.clamp(idx), _parse_assets(assets)))


@app.get('/api/transitions')
def transitions(market: str | None = Query(None),
                idx: int | None = Query(None)) -> JSONResponse:
    """Historical quadrant-to-quadrant transition probabilities up to `idx`."""
    try:
        from ..analytics import transition_matrix as transition_mod
    except ImportError:
        from analytics import transition_matrix as transition_mod

    with STORE.session(market) as snapshot:
        frame_idx = snapshot.clamp(idx)
        return ok(transition_mod.compute_transition_matrix(snapshot.df.iloc[:frame_idx + 1]))


@app.get('/api/series')
def series(names: str = Query(..., description='Comma-separated column names'),
           market: str | None = Query(None)) -> JSONResponse:
    """Raw column values for sparklines and secondary charts."""
    requested = _parse_assets(names) or []
    if not requested:
        raise HTTPException(status_code=400, detail='At least one series name is required')

    with STORE.session(market) as snapshot:
        return ok(compute.series_payload(snapshot, requested))


# ----------------------------------------------------------------------
# Exports
# ----------------------------------------------------------------------
@app.get('/api/report')
def report_pdf(market: str | None = Query(None), idx: int | None = Query(None)) -> FileResponse:
    """Generate and return a publication-ready PDF strategy report."""
    try:
        from ..research import pdf as pdf_mod
    except ImportError:
        from research import pdf as pdf_mod

    os.makedirs(EXPORT_DIR, exist_ok=True)

    with STORE.session(market) as snapshot:
        frame_idx = snapshot.clamp(idx)
        # Reuse the same cached analytics bundle used by the frame and forecast
        # endpoints so the report and dashboard cannot diverge.
        bundle = compute.analysis_bundle(snapshot, frame_idx)

        stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'BusinessCycle_Report_{snapshot.market}_{stamp}.pdf'
        output_path = os.path.join(EXPORT_DIR, filename)

        chart_fd, chart_path = tempfile.mkstemp(suffix='.png', prefix='cycle_chart_')
        os.close(chart_fd)
        try:
            render_cycle_png(snapshot, frame_idx, chart_path, bundle['forecast'])
            pdf_mod.build_pdf_report(
                bundle['data'], bundle['analysis'], bundle['insights'],
                bundle['market_insights'], bundle['narrative'], bundle['analogues'],
                bundle['deltas'], chart_path, output_path, snapshot.data_health,
            )
        finally:
            if os.path.exists(chart_path):
                os.unlink(chart_path)

    return FileResponse(output_path, media_type='application/pdf', filename=filename, background=BackgroundTask(os.unlink, output_path))


@app.get('/api/chart.png')
def chart_png(market: str | None = Query(None), idx: int | None = Query(None)) -> FileResponse:
    """Server-rendered PNG of the cycle chart, for sharing or embedding."""
    with STORE.session(market) as snapshot:
        frame_idx = snapshot.clamp(idx)
        projection = compute.forecast_payload(snapshot, frame_idx)
        fd, path = tempfile.mkstemp(suffix='.png', prefix='cycle_')
        os.close(fd)
        render_cycle_png(snapshot, frame_idx, path, projection)
        filename = f'cycle_{snapshot.market}_{frame_idx}.png'

    return FileResponse(path, media_type='image/png', filename=filename, background=BackgroundTask(os.unlink, path))


@app.post('/api/cache/clear')
def clear_cache(market: str | None = Query(None)) -> JSONResponse:
    """Drop cached market snapshots so the next request refetches upstream data."""
    resolved = normalize_market(market) if market else None
    return ok({'cleared': STORE.invalidate(resolved)})


# ----------------------------------------------------------------------
# Static frontend (mounted last so /api/* always wins)
# ----------------------------------------------------------------------
if os.path.isdir(FRONTEND_DIST):
    app.mount('/', StaticFiles(directory=FRONTEND_DIST, html=True), name='frontend')
