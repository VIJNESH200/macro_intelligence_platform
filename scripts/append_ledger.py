from __future__ import annotations
"""
CLI Script: Append Forecast Entry to Live Track Record Ledger.
=============================================================
Opens docs/live_track_record.csv in append-only mode ('a')
and appends a structured forecast row without modifying historical entries.
"""
import os
import sys
import json
import csv
import argparse

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))


def append_to_live_ledger(json_path: str = 'docs/latest_forecast.json',
                           ledger_path: str = 'docs/live_track_record.csv') -> str:
    """Read latest forecast JSON and append a row to the live track record CSV."""
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Forecast JSON payload not found at {json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    as_of = data.get('as_of', '')
    current_regime = data.get('current_regime', '')
    conviction = data.get('conviction', 0.0)
    model_ver = data.get('model_version', '2.5.0')
    f3m = data.get('forecasts', {}).get('3m', {}).get('quadrant', '')
    f6m = data.get('forecasts', {}).get('6m', {}).get('quadrant', '')
    f9m = data.get('forecasts', {}).get('9m', {}).get('quadrant', '')

    headers = [
        'date', 'current_regime', 'forecast_3m', 'forecast_6m', 'forecast_9m',
        'conviction', 'model_version', 'realized_3m', 'realized_6m', 'realized_9m'
    ]

    os.makedirs(os.path.dirname(os.path.abspath(ledger_path)), exist_ok=True)
    file_exists = os.path.exists(ledger_path)

    # Check if entry for date already exists to prevent duplicate appends on same day
    if file_exists:
        with open(ledger_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            existing_dates = [row[0] for row in reader if row]
            if as_of in existing_dates:
                print(f"[*] Ledger entry for date {as_of} already present. Skipping duplicate append.")
                return ledger_path

    with open(ledger_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(headers)

        writer.writerow([
            as_of, current_regime, f3m, f6m, f9m,
            conviction, model_ver, '', '', ''  # Realized columns left empty until backfill
        ])

    print(f"[+] Appended forecast row for {as_of} ({current_regime} -> 6M: {f6m}) to {ledger_path}")
    return ledger_path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Append forecast entry to live track record ledger.")
    parser.add_argument('--json', default='docs/latest_forecast.json', help="Forecast JSON input path.")
    parser.add_argument('--ledger', default='docs/live_track_record.csv', help="Ledger CSV output path.")
    args = parser.parse_args()

    append_to_live_ledger(json_path=args.json, ledger_path=args.ledger)
