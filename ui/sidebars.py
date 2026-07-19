"""
UI Sidebars — Left and right sidebar text element creation.
============================================================
Extracted from prepare_plot() in business_cycle_tracer.py.
"""
import matplotlib.pyplot as plt


def create_sparkline_axes(fig: plt.Figure, df) -> tuple:
    """Create the sparkline axes on the right sidebar. Returns (ax, scatter_point)."""
    ax_spark = fig.add_axes([0.84, 0.84, 0.14, 0.10])
    ax_spark.plot(df.index, df['PMI'], color='#1f497d', linewidth=1.5)
    ax_spark.axis('off')
    ax_spark.set_title("Historical Trend", fontsize=10, color='gray', pad=5, fontweight='bold')
    spark_pt = ax_spark.scatter([], [], color='red', s=40, zorder=5)
    return ax_spark, spark_pt


def create_left_sidebar(fig: plt.Figure) -> dict:
    """Create left sidebar text elements. Returns dict of text objects."""
    texts = {}

    texts['left_header1'] = fig.text(0.02, 0.95, "CURRENT OBSERVATION",
                                     fontsize=11, fontweight='bold', color='#1f497d')
    texts['info_date'] = fig.text(0.02, 0.90, "Date:\n--",
                                  fontsize=10, linespacing=1.5, color='#333333')
    texts['info_val'] = fig.text(0.02, 0.84, "Value:\n--",
                                 fontsize=10, linespacing=1.5, color='#333333')
    texts['info_quad'] = fig.text(0.02, 0.78, "Quadrant:\n--",
                                  fontsize=10, linespacing=1.5, fontweight='bold', color='#333333')

    # Separator
    texts['left_sep'] = fig.add_artist(
        plt.Line2D([0.02, 0.14], [0.75, 0.75], color='lightgray', linewidth=1,
                   transform=fig.transFigure)
    )

    texts['left_header2'] = fig.text(0.02, 0.72, "CYCLE STATISTICS",
                                     fontsize=11, fontweight='bold', color='#1f497d')
    texts['stat_entered'] = fig.text(0.02, 0.67, "Entered:\n--",
                                     fontsize=10, linespacing=1.5, color='#333333')
    texts['stat_duration'] = fig.text(0.02, 0.61, "Duration:\n--",
                                      fontsize=10, linespacing=1.5, color='#333333')
    texts['stat_prev'] = fig.text(0.02, 0.55, "Previous Phase:\n--",
                                  fontsize=10, linespacing=1.5, color='#333333')

    return texts


def create_right_sidebar(fig: plt.Figure) -> dict:
    """Create right sidebar text elements. Returns dict of text objects."""
    texts = {}

    texts['right_header1'] = fig.text(0.84, 0.77, "MARKET INTERPRETATION",
                                      fontsize=11, fontweight='bold', color='#1f497d')
    texts['interp_phase'] = fig.text(0.84, 0.72, "Current Phase:\n--",
                                     fontsize=10, linespacing=1.5, color='#333333')
    texts['interp_trend'] = fig.text(0.84, 0.66, "Trend:\n--",
                                     fontsize=10, linespacing=1.5, color='#333333')
    texts['interp_signal'] = fig.text(0.84, 0.60, "Signal:\n--",
                                      fontsize=10, linespacing=1.5, color='#333333')
    texts['interp_mom'] = fig.text(0.84, 0.54, "Momentum:\n--",
                                   fontsize=10, linespacing=1.5, color='#333333')
    texts['interp_overall'] = fig.text(0.84, 0.48, "Overall:\n--",
                                       fontsize=10, linespacing=1.5, color='#333333')

    # Separator
    texts['right_sep'] = fig.add_artist(
        plt.Line2D([0.84, 0.98], [0.45, 0.45], color='lightgray', linewidth=1,
                   transform=fig.transFigure)
    )

    texts['right_header2'] = fig.text(0.84, 0.42, "CURRENT READING",
                                      fontsize=11, fontweight='bold', color='#1f497d')
    texts['read_health'] = fig.text(0.84, 0.39, "Health:\n--",
                                    fontsize=10, linespacing=1.2, color='#333333')
    texts['read_mom'] = fig.text(0.84, 0.35, "Momentum:\n--",
                                 fontsize=10, linespacing=1.2, color='#333333')
    texts['read_dist'] = fig.text(0.84, 0.31, "Distance from Center:\n--",
                                  fontsize=10, linespacing=1.2, color='#333333')
    texts['read_dir'] = fig.text(0.84, 0.27, "Direction:\n--",
                                 fontsize=10, linespacing=1.2, color='#333333')

    # Macro Drivers Separator
    texts['right_sep2'] = fig.add_artist(
        plt.Line2D([0.84, 0.98], [0.24, 0.24], color='lightgray', linewidth=1,
                   transform=fig.transFigure)
    )
    
    texts['right_header3'] = fig.text(0.84, 0.22, "MACRO DRIVERS",
                                      fontsize=10, fontweight='bold', color='#1f497d')
                                      
    try:
        from ..config import MACRO_SERIES
    except ImportError:
        from config import MACRO_SERIES
    y_pos = 0.19
    for name in MACRO_SERIES.keys():
        if name in ['Yield 10Y', 'Yield Short']:
            continue
        display_name = name if name != 'Yield Spread' else 'Yield Curve'
        texts[f'driver_{name}_line1'] = fig.text(0.84, y_pos, f"{display_name}", fontsize=8.5, fontweight='bold', color='#333333')
        texts[f'driver_{name}_val'] = fig.text(0.98, y_pos, "--", fontsize=8.5, fontweight='bold', color='#333333', ha='right')
        texts[f'driver_{name}_line2'] = fig.text(0.84, y_pos-0.014, "--", fontsize=8.0, color='#666666')
        texts[f'driver_{name}_pct'] = fig.text(0.98, y_pos-0.014, "--", fontsize=7.5, color='#666666', ha='right')
        y_pos -= 0.033

    # Forecast Separator
    texts['right_sep3'] = fig.add_artist(
        plt.Line2D([0.84, 0.98], [0.065, 0.065], color='lightgray', linewidth=1,
                   transform=fig.transFigure)
    )
    texts['right_header4'] = fig.text(0.84, 0.045, "FORECAST (6M)",
                                      fontsize=10, fontweight='bold', color='#1f497d')
    texts['fc_base'] = fig.text(0.84, 0.025, "Base: --", fontsize=8.5, color='#333333')
    texts['fc_bull'] = fig.text(0.84, 0.010, "Bull: --", fontsize=8.5, color='#333333')
    texts['fc_bear'] = fig.text(0.98, 0.010, "Bear: --", fontsize=8.5, color='#333333', ha='right')

    return texts


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
        plt.Line2D([0.02, 0.14], [0.50, 0.50], color='lightgray', linewidth=1,
                   transform=fig.transFigure)
    )
    market_header = fig.text(0.02, 0.45, "MARKET CONTEXT",
                             fontsize=11, fontweight='bold', color='#1f497d')

    ax_market_mode = fig.add_axes([0.02, 0.41, 0.09, 0.025])
    btn_market_mode = style_button(ax_market_mode, '1M Change ▼')

    ax_market_cfg = fig.add_axes([0.12, 0.41, 0.03, 0.025])
    btn_market_cfg = style_button(ax_market_cfg, '⚙')

    ax_market = fig.add_axes([0.02, 0.10, 0.14, 0.30])
    ax_market.set_facecolor('#f8f9fa')
    for spine in ax_market.spines.values():
        spine.set_visible(False)
    ax_market.get_xaxis().set_visible(False)
    ax_market.get_yaxis().set_visible(False)
    ax_market.set_xlim(0, 1)
    ax_market.set_ylim(0, 1)

    market_texts = {}
    y_pos = 0.95
    for name in market_series.keys():
        t_name = ax_market.text(0.02, y_pos, name, fontsize=8.5, fontweight='bold',
                                color='#333333', transform=ax_market.transData, clip_on=True)
        t_val = ax_market.text(0.68, y_pos, "--", fontsize=8.5, ha='right',
                               color='#333333', transform=ax_market.transData, clip_on=True)
        t_chg = ax_market.text(0.98, y_pos, "--", fontsize=8.5, ha='right',
                               color='gray', transform=ax_market.transData, clip_on=True)

        sep_line, = ax_market.plot([0.02, 0.95], [y_pos - 0.08, y_pos - 0.08],
                                   color='lightgray', linewidth=0.5,
                                   transform=ax_market.transData)
        sep_line.set_clip_on(True)

        market_texts[name] = {'name': t_name, 'val': t_val, 'chg': t_chg, 'y0': y_pos}
        y_pos -= 0.16

    ax_market.set_ylim(0, 1)

    return (ax_market, market_texts, market_sep, market_header,
            ax_market_mode, btn_market_mode, ax_market_cfg, btn_market_cfg)
