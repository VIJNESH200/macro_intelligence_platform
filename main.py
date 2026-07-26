from __future__ import annotations
"""
Economic Regime Intelligence Platform v2.5 — Entry Point
================================================
python -m macro_intelligence_platform.main

Runs the complete pipeline:
  DataEngine → FeatureEngine → App (GUI)
"""
try:
    from .config import CONFIG, MARKET_SERIES, MACRO_SERIES, reload_for_market, save_market_preference
    from .data.data_engine import DataEngine
    from .features.feature_engine import FeatureEngine
    from .ui.app import App
except ImportError:
    from config import CONFIG, MARKET_SERIES, MACRO_SERIES, reload_for_market, save_market_preference
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

    # Global app reference for market switching
    app_ref = {'app': None, 'df': df, 'spline_data': spline_data, 'engine': engine}

    def on_market_change(market: str):
        """Callback when user switches market via UI."""
        print(f"[Market] Switching to {market}...")
        reload_for_market(market)

        print(f"[Market] Loading {CONFIG['name']} data...")
        new_engine = DataEngine(CONFIG, MARKET_SERIES, MACRO_SERIES)
        new_df = new_engine.load_all()

        # Report any data load warnings
        if new_engine.load_warnings:
            print(f"[Market] ⚠ Data warnings:")
            for warning in new_engine.load_warnings:
                print(f"  - {warning}")

        print(f"[Market] Computing features...")
        new_df, new_spline = FeatureEngine.compute_all(new_df, CONFIG)

        # Update app state efficiently
        app = app_ref['app']
        app.df = new_df
        app.spline_data = new_spline
        app.config = CONFIG.copy()
        app.market_series = MARKET_SERIES.copy()
        app.rebuild_market_panel()
        app.data_metadata = new_engine.get_metadata
        app.max_frames = len(new_df) - 1
        app.state['current_frame'] = 0

        # Redraw at latest frame
        app.slider.set_val(app.max_frames)
        app.draw_frame(app.max_frames)
        app.fig.canvas.draw_idle()

        # Show brief warning if some market data failed to load
        if new_engine.load_warnings:
            pe = app.plot_elements
            pe['status_label'].set_text(
                f"⚠ {len(new_engine.load_warnings)} market data unavailable"
            )
            pe['status_label'].set_color('dimgray')
            pe['status_label'].set_fontweight('normal')
            pe['status_label'].set_bbox(dict(facecolor='none', edgecolor='none'))
            app.fig.canvas.draw_idle()
            app._schedule_status_restore(delay_ticks=100)

        save_market_preference(market)
        print(f"[Market] ✓ Switched to {CONFIG['name']}")

    # 3. Launch GUI
    app = App(df, spline_data, CONFIG, MARKET_SERIES, data_metadata=engine.get_metadata,
              on_market_change=on_market_change)
    app_ref['app'] = app
    app.run()


if __name__ == '__main__':
    main()
