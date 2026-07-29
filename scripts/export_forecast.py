from __future__ import annotations
"""
CLI Script: Export Latest Forecast to Documented JSON Contract.
=============================================================
Usage:
    python scripts/export_forecast.py [--offline] [--out docs/latest_forecast.json]
"""
import os
import sys
import argparse

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from config import reload_for_market
from api import load_macro_data, compute_features, forecast_cycle

def export_latest_forecast(out_path: str = 'docs/latest_forecast.json', market: str = 'INDIA', offline: bool = True) -> str:
    """Run pipeline for specified market and write serialized ForecastResult JSON to out_path."""
    print(f"Running Macro Intelligence Platform forecast export [{market}]...")
    reload_for_market(market)

    bundle = load_macro_data(offline=offline)
    feat_bundle = compute_features(bundle)
    forecast = forecast_cycle(feat_bundle)

    if not forecast.validate_schema():
        raise ValueError(f"Generated forecast payload for {market} failed schema validation!")

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    json_payload = forecast.to_json()

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(json_payload)

    print(f"[+] Successfully exported [{market}] latest forecast JSON -> {out_path}")
    print(f"    As-Of: {forecast.as_of} | Regime: {forecast.current_regime} | Conviction: {forecast.conviction}%")
    return out_path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Export latest forecast JSON.")
    parser.add_argument('--out', default='docs/latest_forecast.json', help="Output path for JSON forecast.")
    parser.add_argument('--market', default='INDIA', choices=['INDIA', 'US'], help="Market profile (INDIA or US).")
    parser.add_argument('--live', action='store_true', help="Run in live fetch mode (default: offline).")
    args = parser.parse_args()

    export_latest_forecast(out_path=args.out, market=args.market, offline=not args.live)
