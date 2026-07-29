# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.5.0] - 2026-07-29

### Added
- **Multi-Market Selector**: Seamless toggle between India and US market regimes (`config/markets.py`).
- **Relative Rotation Graph (RRG) Integration**: Added `integrations/rrg/` for rotational momentum analysis across economic sectors.
- **FastAPI Web Server & React 18 Frontend**: Modern web platform UI with real-time OpenAPI docs.
- **Documentation Architecture Sync**: Updated system architecture diagram, forecast horizon notes, and signal consensus specifications in `README.md`.

## [1.0.0] - 2026-07-19

### Added
- **Open-Source Release**: Initial public release of the Macro Intelligence Platform on GitHub.
- **Three-Signal Consensus**: Advanced forecasting model blending CLI momentum, historical analogues, and macro driver z-scores.
- **Conviction Calibration**: Probabilistic scenario analysis mapping conviction tiers (Low/Medium/High) to empirical accuracy.
- **Automated Reporting**: Export module that builds comprehensive presentation-ready PDF reports with dynamic narrative generation.
- **Data Engine Caching**: Local CSV caching for FRED and Yahoo Finance API calls to prevent rate-limiting and improve application startup time.
- **Look-Ahead Bias Elimination**: Rewrote the historical analogue search algorithm to strictly prevent projecting future index values during backtesting.
- **Macro Drivers**: Utilizing Real Policy Rate (Repo - CPI YoY) for accurate monetary tightness analysis.
