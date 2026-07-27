from __future__ import annotations
"""
CLI Script: Monthly Back-fill for Realized Outcomes in Live Track Record.
=======================================================================
Reads docs/live_track_record.csv, checks historical data, and populates
realized_3m, realized_6m, realized_9m columns once horizon dates pass.
"""
import os
import sys
import csv
import pandas as pd
import argparse

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    from ..api import load_macro_data, compute_features
except ImportError:
    from api import load_macro_data, compute_features


def backfill_realized_outcomes(ledger_path: str = None) -> str:
    """Read ledger, compute actual historical outcomes for past entries, and update realized columns."""
    if ledger_path is None:
        ledger_path = os.path.join(REPO_ROOT, 'docs', 'live_track_record.csv')

    if not os.path.exists(ledger_path):
        print(f"[*] Ledger file not found at {ledger_path}. Nothing to back-fill.")
        return ledger_path

    bundle = load_macro_data(offline=True)
    bundle = compute_features(bundle)
    df = bundle.df

    if 'Quadrant' not in df.columns:
        print("[!] Failed to compute quadrant metrics for back-fill.")
        return ledger_path

    rows = []
    with open(ledger_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for r in reader:
            rows.append(r)

    if not rows or not fieldnames:
        return ledger_path

    updated_count = 0
    for r in rows:
        entry_date_str = r['date']
        try:
            entry_dt = pd.to_datetime(entry_date_str)
        except Exception:
            continue

        for h, col_name in [(3, 'realized_3m'), (6, 'realized_6m'), (9, 'realized_9m')]:
            if not r.get(col_name):
                target_dt = entry_dt + pd.DateOffset(months=h)
                # Find matching month in historical df
                match = df[df.index >= target_dt]
                if not match.empty:
                    realized_quad = match['Quadrant'].iloc[0]
                    r[col_name] = realized_quad
                    updated_count += 1

    with open(ledger_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[+] Successfully back-filled {updated_count} realized outcomes in {ledger_path}")
    return ledger_path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Back-fill realized outcomes in live track record.")
    parser.add_argument('--ledger', default='docs/live_track_record.csv', help="Ledger CSV path.")
    args = parser.parse_args()

    backfill_realized_outcomes(ledger_path=args.ledger)
