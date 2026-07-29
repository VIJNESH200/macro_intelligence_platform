from __future__ import annotations
"""
CLI Script: Generate Static Single-Page HTML Dashboard for GitHub Pages.
========================================================================
Reads docs/latest_forecast_india.json and docs/latest_forecast_us.json
and renders docs/index.html with an interactive India/US tab toggle.
"""
import os
import sys
import json
import html
import argparse

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))


def _load_market(json_path: str) -> dict | None:
    """Load a single market JSON file, returning None if missing."""
    if not os.path.exists(json_path):
        return None
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _render_market_card(data: dict, market_id: str) -> str:
    """Render the HTML card grid and provider table for one market."""
    regime = data.get('current_regime', 'Unknown')
    conviction = data.get('conviction', 0.0)
    as_of = data.get('as_of', 'N/A')
    health_dict = data.get('data_health', {})

    f6m = data.get('forecasts', {}).get('6m', {})
    f6m_x = f6m.get('x', 'N/A')
    f6m_y = f6m.get('y', 'N/A')
    f6m_quad = f6m.get('quadrant', 'N/A')

    f3m = data.get('forecasts', {}).get('3m', {})
    f3m_quad = f3m.get('quadrant', 'N/A')

    f9m = data.get('forecasts', {}).get('9m', {})
    f9m_quad = f9m.get('quadrant', 'N/A')

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

    return f"""
        <div class="grid">
            <div class="card">
                <h3>Current Regime</h3>
                <div class="val" style="color:{regime_bg}">{regime}</div>
                <p class="sub">As of {as_of}</p>
            </div>
            <div class="card">
                <h3>Headline Conviction</h3>
                <div class="val">{conviction}%</div>
                <p class="sub">Three-Signal Consensus</p>
            </div>
            <div class="card">
                <h3>6-Month Projection</h3>
                <div class="val" style="color:{regime_colors.get(f6m_quad, '#f8fafc')}">{f6m_quad}</div>
                <p class="sub">X={f6m_x}, Y={f6m_y}</p>
            </div>
        </div>

        <div class="card" style="margin-bottom:1.5rem;">
            <h3>Forward Horizon Matrix</h3>
            <table>
                <thead><tr><th>Horizon</th><th>Projected Regime</th></tr></thead>
                <tbody>
                    <tr><td>3-Month</td><td><strong>{f3m_quad}</strong></td></tr>
                    <tr><td>6-Month</td><td><strong>{f6m_quad}</strong></td></tr>
                    <tr><td>9-Month</td><td><strong>{f9m_quad}</strong></td></tr>
                </tbody>
            </table>
        </div>

        <div class="card">
            <h3>Provider Data Provenance &amp; Freshness Status</h3>
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
    """


def generate_static_site(india_json: str = 'docs/latest_forecast_india.json',
                         us_json: str = 'docs/latest_forecast_us.json',
                         legacy_json: str = 'docs/latest_forecast.json',
                         out_html: str = 'docs/index.html') -> str:
    """Read forecast JSON payloads for both markets and generate a tabbed HTML dashboard."""

    # Load market data; fall back to legacy single-market file for India
    india_data = _load_market(india_json) or _load_market(legacy_json)
    us_data = _load_market(us_json)

    if india_data is None and us_data is None:
        raise FileNotFoundError("No forecast JSON payloads found for either market.")

    india_html = _render_market_card(india_data, 'india') if india_data else '<p style="color:#94a3b8;">India forecast data not available.</p>'
    us_html = _render_market_card(us_data, 'us') if us_data else '<p style="color:#94a3b8;">US forecast data not available.</p>'

    india_regime = india_data.get('current_regime', 'N/A') if india_data else 'N/A'
    us_regime = us_data.get('current_regime', 'N/A') if us_data else 'N/A'
    version = (india_data or us_data).get('model_version', '2.5.0')

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Economic Regime Intelligence Platform | Live Status</title>
    <meta name="description" content="Live macroeconomic business cycle dashboard tracking India and US economic regimes with 3-signal consensus forecasting.">
    <style>
        * {{ box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 2rem; }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap; gap: 0.5rem; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1.5rem; margin-bottom: 1.5rem; }}
        .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 1.5rem; }}
        .card h3 {{ margin-top: 0; color: #94a3b8; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.05em; }}
        .card .val {{ font-size: 2rem; font-weight: bold; margin: 0.5rem 0; }}
        .card .sub {{ color: #94a3b8; margin: 0; font-size: 0.9rem; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; }}
        th, td {{ padding: 0.75rem; text-align: left; border-bottom: 1px solid #334155; }}
        th {{ color: #94a3b8; font-size: 0.85rem; text-transform: uppercase; }}
        a {{ color: #38bdf8; text-decoration: none; }}
        footer {{ margin-top: 3rem; text-align: center; color: #64748b; font-size: 0.85rem; }}

        /* Tab toggle styles */
        .tab-bar {{ display: flex; gap: 0; margin-bottom: 1.5rem; }}
        .tab-btn {{
            flex: 1; padding: 0.85rem 1.2rem; border: 1px solid #334155; background: #1e293b;
            color: #94a3b8; font-size: 1rem; font-weight: 600; cursor: pointer;
            transition: all 0.2s ease; text-align: center;
        }}
        .tab-btn:first-child {{ border-radius: 8px 0 0 8px; }}
        .tab-btn:last-child {{ border-radius: 0 8px 8px 0; }}
        .tab-btn.active {{ background: #334155; color: #f8fafc; border-color: #475569; }}
        .tab-btn:hover:not(.active) {{ background: #263044; }}
        .tab-btn .flag {{ font-size: 1.3rem; margin-right: 0.4rem; }}
        .tab-btn .regime-tag {{ font-size: 0.75rem; font-weight: 400; opacity: 0.8; margin-left: 0.4rem; }}
        .tab-panel {{ display: none; }}
        .tab-panel.active {{ display: block; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1 style="margin:0; font-size:1.6rem;">Economic Regime Intelligence Platform</h1>
                <p style="margin:0.25rem 0 0 0; color:#94a3b8;">Institutional Business Cycle Tracing &amp; Quantitative Forecasting</p>
            </div>
        </div>

        <div class="tab-bar">
            <button class="tab-btn active" onclick="switchTab('india')">
                <span class="flag">\U0001F1EE\U0001F1F3</span> India
                <span class="regime-tag">{india_regime}</span>
            </button>
            <button class="tab-btn" onclick="switchTab('us')">
                <span class="flag">\U0001F1FA\U0001F1F8</span> United States
                <span class="regime-tag">{us_regime}</span>
            </button>
        </div>

        <div id="panel-india" class="tab-panel active">
            {india_html}
        </div>
        <div id="panel-us" class="tab-panel">
            {us_html}
        </div>

        <footer>
            <p>Model Version {version} | Exported automatically |
            <a href="latest_forecast_india.json">India JSON</a> |
            <a href="latest_forecast_us.json">US JSON</a> |
            <a href="track_record.csv">Live Track Record Ledger</a></p>
        </footer>
    </div>

    <script>
        function switchTab(market) {{
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
            document.getElementById('panel-' + market).classList.add('active');
            event.currentTarget.classList.add('active');
        }}
    </script>
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
    parser.add_argument('--india-json', default='docs/latest_forecast_india.json', help="India forecast JSON input.")
    parser.add_argument('--us-json', default='docs/latest_forecast_us.json', help="US forecast JSON input.")
    parser.add_argument('--out', default='docs/index.html', help="Output HTML path.")
    args = parser.parse_args()

    generate_static_site(india_json=args.india_json, us_json=args.us_json, out_html=args.out)
