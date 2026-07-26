from __future__ import annotations
"""
UI Sidebars — Left and right sidebar text element creation.
============================================================
Extracted from prepare_plot() in business_cycle_tracer.py.
"""
import matplotlib.pyplot as plt


def create_sparkline_axes(fig: plt.Figure, df, indicator_name: str = "Indicator") -> tuple:
    """Create the sparkline axes on the right sidebar. Returns (ax, scatter_point)."""
    ax_spark = fig.add_axes([0.84, 0.84, 0.14, 0.10])
    ax_spark.plot(df.index, df['CLI_Raw'], color='#1f497d', linewidth=1.5)
    ax_spark.axis('off')
    ax_spark.set_title(f"{indicator_name} — History", fontsize=9, color='gray', pad=5, fontweight='bold')
    spark_pt = ax_spark.scatter([], [], color='red', s=40, zorder=5)
    return ax_spark, spark_pt


def create_left_sidebar(fig: plt.Figure) -> dict:
    """Create left sidebar text elements. Returns dict of text objects."""
    texts = {}

    texts['left_header1'] = fig.text(0.02, 0.955, "CURRENT OBSERVATION",
                                     fontsize=11, fontweight='bold', color='#1f497d')
    texts['info_date'] = fig.text(0.02, 0.925, "Date: --",
                                  fontsize=10, color='#333333')
    texts['info_val'] = fig.text(0.02, 0.900, "Value: --",
                                 fontsize=10, color='#333333')
    texts['info_quad'] = fig.text(0.02, 0.875, "Quadrant: --",
                                  fontsize=10, fontweight='bold', color='#333333')

    # Separator
    texts['left_sep'] = fig.add_artist(
        plt.Line2D([0.02, 0.14], [0.855, 0.855], color='lightgray', linewidth=1,
                   transform=fig.transFigure)
    )

    texts['left_header2'] = fig.text(0.02, 0.825, "CYCLE STATISTICS",
                                     fontsize=11, fontweight='bold', color='#1f497d')
    texts['stat_entered'] = fig.text(0.02, 0.795, "Entered: --",
                                     fontsize=10, color='#333333')
    texts['stat_duration'] = fig.text(0.02, 0.770, "Duration: --",
                                      fontsize=10, color='#333333')
    texts['stat_prev'] = fig.text(0.02, 0.745, "Previous Phase: --",
                                  fontsize=10, color='#333333')

    return texts


def create_right_sidebar(fig: plt.Figure) -> dict:
    """Create right sidebar text elements. Returns dict of text objects."""
    texts = {}

    texts['right_header1'] = fig.text(0.845, 0.80, "MARKET INTERPRETATION",
                                      fontsize=9.5, fontweight='bold', color='#1f497d')
    texts['interp_phase'] = fig.text(0.845, 0.775, "Current Phase: --",
                                     fontsize=8.5, color='#333333')
    texts['interp_trend'] = fig.text(0.845, 0.75, "Trend: --",
                                     fontsize=8.5, color='#333333')
    texts['interp_signal'] = fig.text(0.845, 0.725, "Signal: --",
                                      fontsize=8.5, color='#333333')
    texts['interp_mom'] = fig.text(0.845, 0.70, "Momentum: --",
                                   fontsize=8.5, color='#333333')
    texts['interp_overall'] = fig.text(0.845, 0.675, "Overall: --",
                                       fontsize=8.5, color='#333333')

    # Separator
    texts['right_sep'] = fig.add_artist(
        plt.Line2D([0.845, 0.985], [0.655, 0.655], color='lightgray', linewidth=1,
                   transform=fig.transFigure)
    )

    texts['right_header2'] = fig.text(0.845, 0.63, "CURRENT READING",
                                      fontsize=9.5, fontweight='bold', color='#1f497d')
    texts['read_health'] = fig.text(0.845, 0.605, "Health: --",
                                    fontsize=8.5, color='#333333')
    texts['read_mom'] = fig.text(0.845, 0.58, "Momentum: --",
                                 fontsize=8.5, color='#333333')
    texts['read_dist'] = fig.text(0.845, 0.555, "Distance from Center: --",
                                  fontsize=8.5, color='#333333')
    texts['read_dir'] = fig.text(0.845, 0.53, "Direction: --",
                                 fontsize=8.5, color='#333333')

    # Macro Drivers Separator
    texts['right_sep2'] = fig.add_artist(
        plt.Line2D([0.845, 0.985], [0.51, 0.51], color='lightgray', linewidth=1,
                   transform=fig.transFigure)
    )

    texts['right_header3'] = fig.text(0.845, 0.485, "MACRO DRIVERS",
                                      fontsize=9.5, fontweight='bold', color='#1f497d')

    try:
        from ..config import MACRO_SERIES
    except ImportError:
        from config import MACRO_SERIES
    y_pos = 0.455
    for name in MACRO_SERIES.keys():
        if name in ['Yield 10Y', 'Yield Short']:
            continue
        display_name = name if name != 'Yield Spread' else 'Yield Curve'
        texts[f'driver_{name}_line1'] = fig.text(0.845, y_pos, f"{display_name}", fontsize=8.0, fontweight='bold', color='#333333')
        texts[f'driver_{name}_val'] = fig.text(0.985, y_pos, "--", fontsize=8.0, fontweight='bold', color='#333333', ha='right')
        texts[f'driver_{name}_line2'] = fig.text(0.845, y_pos-0.014, "--", fontsize=7.5, color='#666666')
        texts[f'driver_{name}_pct'] = fig.text(0.985, y_pos-0.014, "--", fontsize=7.0, color='#666666', ha='right')
        y_pos -= 0.04

    # Forecast Separator
    texts['right_sep3'] = fig.add_artist(
        plt.Line2D([0.845, 0.985], [0.345, 0.345], color='lightgray', linewidth=1,
                   transform=fig.transFigure)
    )
    texts['right_header4'] = fig.text(0.845, 0.32, "FORECAST (9M)",
                                      fontsize=9.5, fontweight='bold', color='#1f497d')
    texts['fc_base'] = fig.text(0.845, 0.295, "Base: --", fontsize=8.5, color='#333333')
    texts['fc_bull'] = fig.text(0.845, 0.27, "Bull: --", fontsize=8.5, color='#333333')
    texts['fc_bear'] = fig.text(0.845, 0.245, "Bear: --", fontsize=8.5, color='#333333')

    return texts


def build_market_texts(ax_market, market_series: dict) -> dict:
    """Create the per-series label/value/change text artists on the market axes."""
    market_texts = {}
    y_pos = 0.97
    for name in market_series.keys():
        t_name = ax_market.text(0.02, y_pos, name, fontsize=8.5, fontweight='bold',
                                color='#333333', transform=ax_market.transData, clip_on=True)
        t_val = ax_market.text(0.98, y_pos, "--", fontsize=8.5, ha='right',
                               color='#333333', transform=ax_market.transData, clip_on=True)
        t_chg = ax_market.text(0.98, y_pos - 0.042, "--", fontsize=8.0, ha='right',
                               color='gray', transform=ax_market.transData, clip_on=True)

        sep_line, = ax_market.plot([0.02, 0.98], [y_pos - 0.075, y_pos - 0.075],
                                   color='lightgray', linewidth=0.5,
                                   transform=ax_market.transData)
        sep_line.set_clip_on(True)

        market_texts[name] = {'name': t_name, 'val': t_val, 'chg': t_chg,
                              'sep': sep_line, 'y0': y_pos}
        y_pos -= 0.095

    return market_texts


def create_market_panel(fig: plt.Figure, market_series: dict) -> tuple:
    """Create the market context panel on the left sidebar.

    Returns (ax_market, market_texts, market_sep, market_header,
             ax_market_mode, btn_market_mode, ax_market_cfg, btn_market_cfg).
    """
    from matplotlib.widgets import Button

    def style_button(ax_btn, label):
        btn = Button(ax_btn, label, color='#ffffff', hovercolor='#f8f9fa')
        btn.label.set_fontsize(10)
        btn.label.set_fontweight('bold')
        btn.label.set_color('#495057')
        for spine in ax_btn.spines.values():
            spine.set_color('#ced4da')
        return btn

    market_sep = fig.add_artist(
        plt.Line2D([0.02, 0.14], [0.725, 0.725], color='lightgray', linewidth=1,
                   transform=fig.transFigure)
    )
    market_header = fig.text(0.02, 0.695, "MARKET CONTEXT",
                             fontsize=11, fontweight='bold', color='#1f497d')

    ax_market_mode = fig.add_axes([0.02, 0.645, 0.09, 0.025])
    btn_market_mode = style_button(ax_market_mode, '1M Change ▼')

    ax_market_cfg = fig.add_axes([0.12, 0.645, 0.03, 0.025])
    btn_market_cfg = style_button(ax_market_cfg, '⚙')

    ax_market = fig.add_axes([0.02, 0.06, 0.14, 0.57])
    ax_market.set_facecolor('#f8f9fa')
    for spine in ax_market.spines.values():
        spine.set_visible(False)
    ax_market.get_xaxis().set_visible(False)
    ax_market.get_yaxis().set_visible(False)
    ax_market.set_xlim(0, 1)
    ax_market.set_ylim(0, 1)

    market_texts = build_market_texts(ax_market, market_series)

    ax_market.set_ylim(0, 1)

    return (ax_market, market_texts, market_sep, market_header,
            ax_market_mode, btn_market_mode, ax_market_cfg, btn_market_cfg)
