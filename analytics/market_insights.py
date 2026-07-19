"""
Market Insights — Deterministic rule-based market commentary.
==============================================================
Exact port of report_market_insights.py.
"""
import pandas as pd


def generate_market_insights(data: dict) -> dict:
    """Consumes multi-horizon market data and applies deterministic rules
    to generate professional market highlights.
    """
    market_data = data.get('market_data', [])
    if not market_data:
        return []

    insights = []

    all_positive = True
    all_1m_negative = True

    valid_assets = []
    for asset in market_data:
        raw = asset.get('returns_raw', {})
        if pd.isna(raw.get('1M')):
            continue
        valid_assets.append(asset)

        for h in ['1M', '3M', '6M', '12M']:
            val = raw.get(h, 0)
            if pd.isna(val) or val <= 0:
                all_positive = False

        if raw.get('1M', 0) >= 0:
            all_1m_negative = False

    if not valid_assets:
        return []

    # Rule 1: Uniform positivity
    if all_positive:
        insights.append("Risk assets remain constructive, printing positive returns across all observed investment horizons.")

    # Rule 2: Broad 1M weakness
    if all_1m_negative:
        insights.append("Recent market action indicates broad-based risk aversion, with broad indices negative over the trailing month.")

    # Rule 3: Short-term pullback in long-term uptrend
    for asset in valid_assets:
        if 'Nifty' in asset['name'] or 'Sensex' in asset['name'] or 'S&P' in asset['name']:
            raw = asset['returns_raw']
            if raw.get('1M', 0) < 0 and raw.get('12M', 0) > 0:
                insights.append(f"Short-term weakness in {asset['name']} appears to be a consolidation within a broader long-term uptrend.")
                break

    # Rule 4: Top performing asset over 12M
    max_12m = -float('inf')
    top_asset = None
    for asset in valid_assets:
        r12 = asset['returns_raw'].get('12M', 0)
        if not pd.isna(r12) and r12 > max_12m:
            max_12m = r12
            top_asset = asset['name']

    if top_asset and max_12m > 0:
        insights.append(f"{top_asset} currently demonstrates the strongest relative performance over the trailing 12-month horizon.")

    # Rule 5: Domestic vs Global
    dom_ret = []
    glob_ret = []
    for asset in valid_assets:
        name = asset['name']
        r12 = asset['returns_raw'].get('12M', 0)
        if pd.isna(r12):
            continue
        if 'S&P' in name or 'Nasdaq' in name:
            glob_ret.append(r12)
        elif 'Nifty' in name or 'Sensex' in name:
            dom_ret.append(r12)

    if dom_ret and glob_ret:
        avg_dom = sum(dom_ret) / len(dom_ret)
        avg_glob = sum(glob_ret) / len(glob_ret)
        if avg_dom > avg_glob:
            insights.append("Domestic indices continue to demonstrate relative strength versus global benchmarks.")
        elif avg_glob > avg_dom:
            insights.append("Global benchmarks are currently outperforming domestic markets over the trailing 12 months.")

    # Relative Leadership Spread
    best_asset = None
    worst_asset = None
    max_1m = -float('inf')
    min_1m = float('inf')

    for asset in valid_assets:
        r1m = asset['returns_raw'].get('1M', 0)
        if not pd.isna(r1m):
            if r1m > max_1m:
                max_1m = r1m
                best_asset = asset['name']
            if r1m < min_1m:
                min_1m = r1m
                worst_asset = asset['name']

    if best_asset and worst_asset and best_asset != worst_asset:
        spread = max_1m - min_1m
        insights.append(f"Relative Leadership: {best_asset} ({max_1m:+.1f}%) vs {worst_asset} ({min_1m:+.1f}%) over 1M. Spread: {spread:.1f} percentage points.")

    # Ensure we have at least one highlight
    if not insights:
        insights.append("Market performance remains mixed across measured investment horizons.")

    # Calculate a simple "Market Score" based on average 1M and 3M performance
    avg_returns = []
    for asset in valid_assets:
        r1 = asset['returns_raw'].get('1M', 0)
        r3 = asset['returns_raw'].get('3M', 0)
        if not pd.isna(r1):
            avg_returns.append(r1)
        if not pd.isna(r3):
            avg_returns.append(r3)

    if avg_returns:
        # Map average return to a 0-100 score (heuristic: -10% = 0, +10% = 100)
        avg = sum(avg_returns) / len(avg_returns)
        market_score = int(max(0, min(100, (avg + 10) * 5)))
    else:
        market_score = 50

    return {
        'insights': insights,
        'market_score': market_score,
        'best_asset': best_asset,
        'worst_asset': worst_asset,
        'spread': spread if 'spread' in locals() else 0
    }
