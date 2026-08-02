from __future__ import annotations
"""
Headless Chart Rendering — PNG for PDF embedding.
=================================================
The browser draws the interactive chart in SVG. The PDF report still needs a
raster image, and `research/pdf.py` takes a file path. This renders the same
quadrant chart offscreen with the Agg backend, reusing `ui/layout.create_main_axes`
so the PDF's chart geometry stays identical to the desktop app's.

This is the only place the web stack touches matplotlib.
"""
import matplotlib

if matplotlib.get_backend().lower() not in ('tkagg', 'qt5agg', 'qtagg', 'macosx'):
    matplotlib.use('Agg')

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.collections import LineCollection  # noqa: E402

try:
    from ..ui.layout import create_main_axes
    from .store import MarketSnapshot
except ImportError:
    from ui.layout import create_main_axes
    from web.store import MarketSnapshot


QUADRANT_COLORS = {
    'Expansion': 'darkgreen',
    'Slowdown': 'darkgoldenrod',
    'Contraction': 'darkred',
    'Recovery': 'darkblue',
}


def render_cycle_png(snapshot: MarketSnapshot, idx: int, output_path: str,
                     forecast: dict | None = None, dpi: int = 300) -> str:
    """Render the cycle chart at `idx` to `output_path`. Returns the path."""
    df = snapshot.df
    config = snapshot.config
    frame = snapshot.clamp(idx)

    tail_length = int(config.get('tail_length', 12))
    start = max(0, frame - tail_length + 1)
    window = df.iloc[start:frame + 1]

    fig = plt.figure(figsize=(11, 7))
    fig.patch.set_facecolor('#ffffff')
    try:
        ax = create_main_axes(fig, df, config)

        xs = window['X'].to_numpy()
        ys = window['Y'].to_numpy()

        # Fading trail: older segments more transparent, same as the desktop view.
        if len(xs) > 1:
            points = np.array([xs, ys]).T.reshape(-1, 1, 2)
            segments = np.concatenate([points[:-1], points[1:]], axis=1)
            alphas = np.linspace(0.15, 0.9, len(segments))
            collection = LineCollection(
                segments, colors=[(0.12, 0.29, 0.49, a) for a in alphas],
                linewidths=2.0, zorder=5
            )
            ax.add_collection(collection)

        current = window.iloc[-1]
        quadrant = current['Quadrant']
        ax.scatter([current['X']], [current['Y']], s=160, zorder=10,
                   color=QUADRANT_COLORS.get(quadrant, '#1f497d'),
                   edgecolor='white', linewidth=1.8)
        ax.annotate(f"  {current.name.strftime('%b %Y')}",
                    (current['X'], current['Y']), zorder=11,
                    fontsize=10, fontweight='bold', color='#333333')

        if forecast:
            path = forecast.get('projected_path') or []
            if len(path) > 1:
                fx = [float(p[0]) for p in path]
                fy = [float(p[1]) for p in path]
                ax.plot(fx, fy, linestyle='--', linewidth=1.8,
                        color='#6c3fb5', alpha=0.85, zorder=6)
                ax.scatter(fx[-1:], fy[-1:], s=90, marker='X', zorder=9,
                           color='#6c3fb5', edgecolor='white', linewidth=1.2)

        ax.set_title(current.name.strftime('%b %Y'), fontsize=13,
                     fontweight='bold', color='#1f497d', pad=12)

        fig.savefig(output_path, dpi=dpi, bbox_inches='tight', facecolor=fig.get_facecolor())
    finally:
        plt.close(fig)

    return output_path
