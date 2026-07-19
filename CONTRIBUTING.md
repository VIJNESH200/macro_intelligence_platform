# Contributing to Macro Intelligence Platform

First off, thank you for considering contributing to the Macro Intelligence Platform! This project is an open-source quantitative research tool, and we welcome improvements to the forecasting logic, data providers, UI, and documentation.

## How to Contribute

1. **Fork the repository** on GitHub.
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/VIJNESH200/macro_intelligence_platform.git
   ```
3. **Create a new branch** for your feature or bugfix:
   ```bash
   git checkout -b feature/my-new-feature
   ```
4. **Make your changes** and commit them with clear, descriptive messages.
5. **Push to your fork** and submit a **Pull Request**.

## Development Guidelines

- **Code Style**: We follow standard PEP 8. Please run `flake8` before submitting a PR.
- **Testing**: Run `python tests/backtest_benchmarks.py` to ensure any changes to the quantitative models do not introduce look-ahead bias or degrade the model's accuracy below baseline thresholds.
- **Data Providers**: If adding a new data provider (e.g., in `data/providers/`), ensure it inherits from `BaseProvider` and implements local caching to respect API rate limits.

## Reporting Bugs

Please use the provided Issue Templates to report bugs. Include a reproducible example and the stack trace if applicable.

## Suggesting Enhancements

If you have an idea for a new macro indicator, forecasting model, or UI feature, please open an Issue using the Feature Request template to discuss it before implementing.
