# Web Interface

A FastAPI service over the existing compute layer, plus a React single-page
frontend. Additive — the matplotlib desktop app (`python -m main`) is untouched
and still runs independently.

## Running

**Production** — build the SPA once, then serve everything from FastAPI on one port:

```bash
cd web/frontend && npm install && npm run build && cd ../..
uvicorn web.server:app --port 8000
# http://127.0.0.1:8000
```

**Development** — two processes, with hot reload on the frontend:

```bash
uvicorn web.server:app --reload --port 8000     # terminal 1
cd web/frontend && npm run dev                  # terminal 2 -> http://localhost:5173
```

Vite proxies `/api/*` to port 8000, so the dev and production origins behave
identically.

## Endpoints

| Method | Path | Returns |
|--------|------|---------|
| GET | `/api/health` | Liveness, version, warm markets |
| GET | `/api/markets` | Available market profiles and their series |
| GET | `/api/cycle?market=` | Frames, spline path, axis bounds, data health |
| GET | `/api/frame/{idx}?market=&assets=` | Per-frame panel data: regime, drivers, market table, narrative |
| GET | `/api/forecast?market=&idx=` | Projection, confidence bands, scenarios, transitions |
| GET | `/api/transitions?market=&idx=` | Quadrant transition probability matrix |
| GET | `/api/series?names=&market=` | Raw column values for sparklines |
| GET | `/api/report?market=&idx=` | Institutional PDF report |
| GET | `/api/chart.png?market=&idx=` | Server-rendered chart PNG |
| POST | `/api/cache/clear?market=` | Drop cached snapshots, forcing a refetch |

Interactive docs are at `/docs`.

## Layout

```
web/
  server.py          FastAPI routes
  store.py           Per-market cache + the lock that makes it concurrency-safe
  compute.py         Engine composition (same chain as the desktop PDF export)
  chart.py           Headless matplotlib PNG, for PDF embedding only
  serialization.py   NaN/numpy -> JSON-safe conversion
  frontend/          Vite + React + Tailwind + shadcn/ui
```

## Two things worth knowing

**Market state is global.** `config.reload_for_market()` mutates module-level
dicts that `FeatureEngine.compute_macro_features`, `MacroIntelligenceEngine`, and
`analytics.market_insights` read at call time. That is fine for a single-user
desktop app, but a server interleaves requests. `MarketStore.session(market)`
therefore holds a reentrant lock while the globals point at the requested
market, and every engine call happens inside that block. `tests/test_web_api.py`
covers this with concurrent cross-market requests.

**pandas emits NaN, JSON has no NaN.** Every response goes through
`to_jsonable`, which maps non-finite floats to `null` and unwraps numpy scalars.
Skipping it produces responses that `JSON.parse` rejects — usually only on early
frames, where market history is incomplete.

## Chart colours

Mark colours were validated with the dataviz palette validator (`--pairs all`,
both light and dark): history blue vs forecast orange clears every gate. The four
regime hues are the reserved status palette and do *not* separate under CVD
simulation (red vs green, deutan ΔE 4.1), so they are used only as low-alpha
territory washes and always appear alongside the regime name in text. Regime
colour never carries meaning on its own.
