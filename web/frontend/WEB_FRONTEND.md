# Web Frontend

React 19 + Vite + Tailwind single-page application for the Macro Intelligence Platform. Renders the business cycle quadrant chart, forecasts, and market panels with real-time market selection and playback controls.

## Tech Stack

- **React 19** — UI framework
- **Vite 6** — Fast dev server and build tool
- **TypeScript 5.7** — Type safety
- **Tailwind CSS 4** — Utility-first styling with `@tailwindcss/vite`
- **Radix UI** — Unstyled accessible components (`tabs`, `slider`, `switch`, `tooltip`, etc.)
- **Lucide React** — Icon library
- **D3 (scales & shapes)** — Quadrant chart rendering

## Running

### Development (with hot reload)

Two terminals:

```bash
# Terminal 1: Start the FastAPI backend on port 8000
uvicorn web.server:app --reload --port 8000

# Terminal 2: Start the Vite dev server on port 5173
cd web/frontend && npm run dev
```

Open [http://localhost:5173](http://localhost:5173). Vite proxies `/api/*` requests to port 8000, so the development experience mirrors production.

### Production (single port)

Build the SPA once, then serve from FastAPI:

```bash
cd web/frontend && npm install && npm run build && cd ../..
uvicorn web.server:app --port 8000
# http://127.0.0.1:8000
```

`npm run build` runs TypeScript compilation (`tsc -b`) then Vite's production build, outputting to `dist/`.

### Type Checking

```bash
cd web/frontend && npm run typecheck
```

## Architecture

**Root component** — `src/App.tsx` orchestrates market selection, frame scrubbing, theme toggle, and layout. Manages playback timer, keyboard shortcuts (space, arrows, home/end), and local storage for preferences.

**Layout** — Fixed desktop viewport on lg screens (Tailwind), responsive mobile-first below. The chart takes primary visual real estate; panels animate with the scrubber without full-page navigation.

**Shared utilities** — `src/lib/`:

- **api.ts** — Async fetch wrapper with error handling. Exports `api.markets()`, `api.cycle(market)`, `api.frame(idx)`, `api.forecast(idx)`, `api.reportUrl()`, `api.clearCache()`.
- **types.ts** — TypeScript interfaces for all payloads: `CyclePayload`, `FramePayload`, `ForecastPayload`, `MarketProfile`, `Frame`, `Regime`, etc.
- **regime.ts** — Constants and helpers for business cycle regimes: `REGIMES` (label/color/description), `regimeOf()`, `describeDirection()`.
- **markup.tsx** — Parses server-generated reportlab markup (`<b>`, `<br/>`, `<font>`, `&bull;`) from the narrative engine into React nodes (whitelist parser, not `dangerouslySetInnerHTML`).
- **utils.ts** — `cn()` utility for composing Tailwind classes with `clsx` + `tailwind-merge`.

**Components** — `src/components/`:

- **QuadrantChart** — D3 + Canvas quadrant render; handles chart pan/zoom, trail animation, forecast path, confidence bands, and click-to-scrub.
- **Controls** — Playback buttons, speed slider, frame input, display toggles (trail, history, forecast, label).
- **StatusRail** — Right sidebar: current regime, market data table, data health status.
- **ForecastPanel** — 3M and 6M projections with conviction scores.
- **MacroPanel** — Macro driver contribution bars.
- **PhasePanel** — Business cycle phase transitions.
- **MarketPanel** — Market-specific economic indicators.
- **NarrativePanel** — Server-generated markup (parsed by `Markup` component).
- **DataHealth** — Freshness warnings and data source metadata.
- **Sparkline** — Mini time series of the primary indicator.
- **UI/** — Radix-based button, card, slider, tabs, etc.

## State Management

All state lives in the App component:

- Market selection (stored in localStorage)
- Frame index (scrubber position)
- Playback state (playing, speed)
- Cycle data (loaded once per market)
- Frame/forecast panels (follow scrubber)
- Theme (light/dark, localStorage)
- Display options (trail, history, forecast, label)

No Redux or Zustand; React hooks and context are overkill for this tree size. Prop drilling is explicit and traceable.

## API Integration

The backend serves:

- `/api/cycle?market=` — Full frame sequence for a market
- `/api/frame/{idx}?market=` — Per-frame panel data
- `/api/forecast?market=&idx=` — Projections and conviction
- `/api/markets` — Available markets
- `/api/cache/clear` — Force a data reload

All requests are aborted on unmount or when a newer request supersedes the old one (prevents stale panel updates from overwriting fresh ones on rapid scrubbing).

## Building & Deployment

**Development build:**
```bash
npm run build
```

Outputs to `dist/`. The production build is baked into the repo so `uvicorn web.server:app` can serve it as static files (no separate Node process needed).

**Incremental builds:**
```bash
npm run typecheck
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Space | Play / Pause |
| ← / → | Step frame |
| Shift+← / Shift+→ | Jump 12 months |
| Home | Jump to start |
| End | Jump to latest |

Skipped when focus is on input, button, or slider.

## Dark Mode

Tailwind's `prefers-color-scheme` media query + manual toggle button. Theme stored in localStorage and stamped on `document.documentElement` as the `dark` class.

## Important Notes

**Market state is global.** The backend's `config.reload_for_market()` mutates module-level dicts. The web server holds a reentrant lock around each request, but the frontend must still respect the market tab — the tab is not just UI, it's a statement of which globals are active on the server. Switching markets invalidates panels until the backend has re-initialized (usually <100ms).

**Fetch cancellation.** Long-running requests (e.g., cycle load) are aborted when the market changes. Slower responses are silently dropped; faster ones land. Prevents race conditions on mobile with poor connectivity.

**Date format.** Frame labels render as `YYYY MMM` (e.g., "2026 Jul") rather than `MMM YYYY` to avoid timeline jitter when scrubbing — month name width varies, so year-first keeps the year glyph in place.

## Debugging

Browser DevTools' Network tab shows API payloads. The `/docs` endpoint (FastAPI's built-in OpenAPI UI) documents all endpoints with live try-it-out forms.

Example: Open [http://localhost:8000/docs](http://localhost:8000/docs) and hit `/api/markets` to see available profiles.
