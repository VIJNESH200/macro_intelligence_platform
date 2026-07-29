# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.5.0] - 2026-07-29

### Added
- **FastAPI Web Server & React 18 Frontend**: Added modern web interface (`web/server.py` and `web/frontend/`) built with React 18, Vite, TypeScript, and tabbed analytics cards alongside OpenAPI interactive docs.
- **Desktop GUI Overhaul**: Redesigned Matplotlib dashboard layout (`ui/app.py`) featuring a vertical status rail, playback toolbar, and zero-overlap coordinate math.
- **Code Audit & Stability Sweep**: Resolved 36 code review findings across engine calculation accuracy, provider fallback resilience, web UI state management, and test suites.

### Changed
- **Documentation Architecture Sync**: Synchronized `README.md` architecture diagram (6-layer), forecast horizon benchmark notes (6M primary), and signal consensus details (40/35/25 live blend).

## [2.3.0] - 2026-07-27

### Added
- **Multi-Market Regime Engine**: Introduced dual-market profiles (`config/markets.py`) with live runtime toggling between **India** (OECD CLI + Core Industries + Sensex/Nifty) and **US** (OECD CLI + Fed Rates + Dow Jones/Russell 2000).
- **Persistent Market Preference**: User-selected market selection is saved to local environment config (`~/.macro_intelligence_platform/market_preference.txt`) and restored automatically across app restarts.
- **Relative Rotation Graph (RRG) Integration**: Added `integrations/rrg/` for rotational momentum and velocity analysis across market sectors.

## [2.0.0] - 2026-07-25

### Added
- **Public Python API Alias**: Standardized top-level import contract (`from macro_intel import load_macro_data, compute_features, forecast_cycle`) with typed `DataBundle` and `ForecastResult` dataclasses.
- **Documented JSON Export**: Added JSON Schema draft-07 specification (`docs/forecast_schema.json`) and automated exporter (`scripts/export_forecast.py`).
- **Static Site Generator & GitHub Pages**: Created static HTML dashboard generator (`scripts/generate_site.py`) and automated weekly GitHub Pages publishing workflow (`.github/workflows/publish.yml`).
- **Live Track Record Ledger**: Implemented append-only CSV ledger (`docs/live_track_record.csv`) with automatic outcome backfilling (`scripts/backfill_realized.py`).

## [1.5.0] - 2026-07-23

### Added
- **Out-of-Sample Backtesting Framework**: Comprehensive historical validation benchmark (`tests/backtest_benchmarks.py`) over a 229-month rolling window (2007–2026) with held-out window evaluation (2019–2026).
- **Statistical Significance Tests**: Integrated McNemar's Test for quadrant classification accuracy ($\chi^2 = 29.26, p < 0.01$) and Diebold–Mariano Test for continuous error reduction ($DM = 5.07, p < 0.01$).
- **Conviction Calibration**: Probabilistic conviction scoring system achieving 89.8% realized quadrant accuracy for high-conviction signals ($\ge 58\%$).
- **Macro Driver Walk-Forward Signal**: Walk-forward Ridge regression covering Real Policy Rate, Core Industries, CPI, and Yield Spreads.

## [1.0.0] - 2026-07-19

### Added
- **Open-Source Release**: Initial public release of the Macro Intelligence Platform on GitHub.
- **4-Phase Business Cycle Engine**: Traces macro health ($X$) and momentum ($Y$) across Expansion, Slowdown, Contraction, and Recovery regimes.
- **Historical Analogue Search**: Multivariate Euclidean distance matching across historical business cycle footprints.
- **Automated Report Generation**: ReportLab PDF exporter creating presentation-ready institutional strategy briefs (`research/pdf.py`).
- **Open Data Pipeline**: Provider integration engine fetching open datasets from FRED, DPIIT, IMF SDMX, Yahoo Finance, and RBI with local CSV caching.
