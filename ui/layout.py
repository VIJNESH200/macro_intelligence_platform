"""
UI Layout — Figure and axes creation.
======================================
Extracted from prepare_plot() in business_cycle_tracer.py.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np


def create_figure(config: dict) -> plt.Figure:
    """Create the main 16x9 figure with modern styling."""
    fig = plt.figure(figsize=(16, 9))
    fig.patch.set_facecolor('#f8f9fa')
    fig.canvas.manager.set_window_title(
        f"Macro Intelligence Platform - {config['name']}"
    )
    return fig


def create_main_axes(fig: plt.Figure, df, config: dict) -> plt.Axes:
    """Create and configure the main chart axes with quadrant fills, labels, grid."""
    ax = fig.add_axes([0.16, 0.20, 0.68, 0.75])
    ax.set_facecolor('white')

    x_min, x_max = df['X'].min(), df['X'].max()
    y_min, y_max = df['Y'].min(), df['Y'].max()
    center = config['center']
    max_dist_x = max(abs(x_max - center), abs(center - x_min))
    max_dist_y = max(abs(y_max - center), abs(center - y_min))
    max_dist = max(max_dist_x, max_dist_y) * (1 + config['padding'])
    max_dist = max(max_dist, 5)

    # Preserve equal aspect ratio filling the rectangular axes
    fig_w, fig_h = 16, 9
    ax_w_frac, ax_h_frac = 0.68, 0.75
    ax_w_inch = fig_w * ax_w_frac
    ax_h_inch = fig_h * ax_h_frac

    data_height = max_dist * 2
    data_width = data_height * (ax_w_inch / ax_h_inch)

    y_lim_min, y_lim_max = center - max_dist, center + max_dist
    x_lim_min, x_lim_max = center - data_width / 2, center + data_width / 2

    ax.set_xlim(x_lim_min, x_lim_max)
    ax.set_ylim(y_lim_min, y_lim_max)
    ax.set_aspect('equal', adjustable='box')

    # Clean spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('gray')
    ax.spines['bottom'].set_color('gray')

    ax.grid(True, linestyle=':', color='lightgray', alpha=0.7)
    ax.axhline(center, color='gray', linestyle='--', linewidth=1)
    ax.axvline(center, color='gray', linestyle='--', linewidth=1)

    # Fill quadrants
    ax.fill_between([center, x_lim_max], center, y_lim_max, color='green', alpha=0.04, zorder=1)
    ax.fill_between([center, x_lim_max], y_lim_min, center, color='goldenrod', alpha=0.04, zorder=1)
    ax.fill_between([x_lim_min, center], y_lim_min, center, color='red', alpha=0.04, zorder=1)
    ax.fill_between([x_lim_min, center], center, y_lim_max, color='blue', alpha=0.04, zorder=1)

    # Corner labels
    font_props = {'fontsize': 13, 'fontweight': 'bold', 'zorder': 8, 'transform': ax.transAxes}
    ax.text(0.98, 0.97, '■ EXPANSION', color='darkgreen', ha='right', va='top', **font_props)
    ax.text(0.98, 0.03, '■ SLOWDOWN', color='darkgoldenrod', ha='right', va='bottom', **font_props)
    ax.text(0.02, 0.03, '■ CONTRACTION', color='darkred', ha='left', va='bottom', **font_props)
    ax.text(0.02, 0.97, '■ RECOVERY', color='darkblue', ha='left', va='top', **font_props)

    ax.set_xlabel(f'Economic Health ({config["window"]}M Z-Score)', fontsize=11, labelpad=10, color='#333333')
    ax.set_ylabel(f'Economic Momentum (1M Δ → {config["window"]}M Z-Score)', fontsize=11, labelpad=10, color='#333333')
    ax.tick_params(colors='#555555')

    return ax


def create_background_axes(fig: plt.Figure) -> plt.Axes:
    """Create a background axes for drawing control group containers."""
    ax_bg = fig.add_axes([0, 0, 1, 1])
    ax_bg.set_zorder(-1)
    ax_bg.axis('off')
    ax_bg.set_xlim(0, 1)
    ax_bg.set_ylim(0, 1)
    return ax_bg


def draw_group_container(fig: plt.Figure, ax_bg: plt.Axes,
                         x0: float, y0: float, width: float, height: float,
                         title: str, pad: float = 0.005) -> list:
    """Draw a labeled container box for a group of controls."""
    box = mpatches.FancyBboxPatch(
        (x0 + pad, y0 + pad), width - 2 * pad, height - 2 * pad,
        boxstyle=f"round,pad={pad}",
        edgecolor='#ced4da', facecolor='#ffffff', linewidth=1,
        transform=ax_bg.transData
    )
    ax_bg.add_patch(box)
    txt = fig.text(
        x0 + width / 2, y0 + height - 0.005, title,
        ha='center', va='top', fontsize=9, fontweight='bold', color='#6c757d'
    )
    return [box, txt]
