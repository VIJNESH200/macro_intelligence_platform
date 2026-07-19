"""
Economic Regime Intelligence Platform v2.5 — Entry Point
================================================
python -m macro_intelligence_platform.main

Runs the complete pipeline:
  DataEngine → FeatureEngine → App (GUI)
"""
try:
    from .config import CONFIG, MARKET_SERIES, MACRO_SERIES
    from .data.data_engine import DataEngine
    from .features.feature_engine import FeatureEngine
    from .ui.app import App
except ImportError:
    from config import CONFIG, MARKET_SERIES, MACRO_SERIES
    from data.data_engine import DataEngine
    from features.feature_engine import FeatureEngine
    from ui.app import App


def main():
    print(f"Macro Intelligence Platform v{CONFIG['version']}")
    print(f"Indicator: {CONFIG['name']}")
    print("=" * 50)

    # 1. Load data
    engine = DataEngine(CONFIG, MARKET_SERIES, MACRO_SERIES)
    df = engine.load_all()

    # 2. Compute features
    df, spline_data = FeatureEngine.compute_all(df, CONFIG)

    # 3. Launch GUI
    app = App(df, spline_data, CONFIG, MARKET_SERIES, data_metadata=engine.get_metadata)
    app.run()


if __name__ == '__main__':
    main()
