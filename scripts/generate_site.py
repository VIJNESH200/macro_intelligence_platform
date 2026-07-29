from __future__ import annotations
"""
CLI Script: Generate Static Single-Page HTML Dashboard for GitHub Pages.
========================================================================
Reads docs/latest_forecast.json and renders docs/index.html.
"""
import os
import sys
import json
import html
import argparse

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))


def generate_static_site(json_path: str = 'docs/latest_forecast.json',
                         out_html: str = 'docs/index.html') -> str:
    """Read forecast JSON payload and generate single-page static HTML dashboard."""
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Forecast JSON payload not found at {json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    as_of = data.get('as_of', 'N/A')
    regime = data.get('current_regime', 'Unknown')
    conviction = data.get('conviction', 0.0)
    version = data.get('model_version', '2.5.0')
    health_dict = data.get('data_health', {})

    f6m = data.get('forecasts', {}).get('6m', {})
    f6m_x = f6m.get('x', 'N/A')
    f6m_y = f6m.get('y', 'N/A')
    f6m_quad = f6m.get('quadrant', 'N/A')

    regime_colors = {
        'Expansion': '#1b5e20',
        'Slowdown': '#b78103',
        'Contraction': '#b71c1c',
        'Recovery': '#0d47a1'
    }
    regime_bg = regime_colors.get(regime, '#333333')

    health_rows = ""
    for series_name, meta in health_dict.items():
        src = html.escape(str(meta.get('source', 'unknown')))
        rel = html.escape(str(meta.get('release_date', 'N/A')))
        status = html.escape(str(meta.get('cache_status', '⚪ Unknown')))
        s_name = html.escape(str(series_name))
        health_rows += f"""
        <tr>
            <td><strong>{s_name}</strong></td>
            <td><code>{src}</code></td>
            <td>{rel}</td>
            <td>{status}</td>
        </tr>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Economic Regime Intelligence Platform | Live Status</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 2rem; }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 1rem; margin-bottom: 2rem; }}
        .badge {{ background: {regime_bg}; color: white; padding: 0.5rem 1rem; border-radius: 6px; font-weight: bold; font-size: 1.2rem; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }}
        .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 1.5rem; }}
        .card h3 {{ margin-top: 0; color: #94a3b8; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.05em; }}
        .card .val {{ font-size: 2rem; font-weight: bold; margin: 0.5rem 0; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; }}
        th, td {{ padding: 0.75rem; text-align: left; border-bottom: 1px solid #334155; }}
        th {{ color: #94a3b8; font-size: 0.85rem; text-transform: uppercase; }}
        a {{ color: #38bdf8; text-decoration: none; }}
        footer {{ margin-top: 3rem; text-align: center; color: #64748b; font-size: 0.85rem; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1 style="margin:0; font-size:1.6rem;">Economic Regime Intelligence Platform</h1>
                <p style="margin:0.25rem 0 0 0; color:#94a3b8;">Institutional Business Cycle Tracing & Quantitative Forecasting</p>
            </div>
            <div class="badge">{regime}</div>
        </div>

        <div class="grid">
            <div class="card">
                <h3>Current Regime (As-Of)</h3>
                <div class="val">{regime}</div>
                <p style="color:#94a3b8; margin:0;">As of {as_of}</p>
            </div>
            <div class="card">
                <h3>6-Month Horizon Projection</h3>
                <div class="val">{f6m_quad}</div>
                <p style="color:#94a3b8; margin:0;">Coords: X={f6m_x}, Y={f6m_y}</p>
            </div>
            <div class="card">
                <h3>Headline Forecast Conviction</h3>
                <div class="val">{conviction}%</div>
                <p style="color:#94a3b8; margin:0;">Active Two-Signal Consensus</p>
            </div>
        </div>

        <div class="card">
            <h3>Provider Data Provenance & Freshness Status</h3>
            <table>
                <thead>
                    <tr>
                        <th>Series</th>
                        <th>Source</th>
                        <th>Release Date</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {health_rows}
                </tbody>
            </table>
        </div>

        <footer>
            <p>Model Version {version} | Exported automatically | <a href="latest_forecast.json">Raw JSON Contract</a> | <a href="track_record.csv">Live Track Record Ledger</a></p>
        </footer>
    </div>
</body>
</html>
"""

    os.makedirs(os.path.dirname(os.path.abspath(out_html)), exist_ok=True)
    with open(out_html, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"[+] Static HTML dashboard generated -> {out_html}")
    return out_html


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate static HTML dashboard.")
    parser.add_argument('--json', default='docs/latest_forecast.json', help="Forecast JSON input path.")
    parser.add_argument('--out', default='docs/index.html', help="Output HTML path.")
    args = parser.parse_args()

    generate_static_site(json_path=args.json, out_html=args.out)
