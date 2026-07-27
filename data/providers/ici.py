from __future__ import annotations
"""
ICI Provider — Direct fetcher for India's Index of Eight Core Industries (ICI).
==============================================================================
Sources data directly from the official portal of the Office of the Economic Adviser (OEA),
Department for Promotion of Industry and Internal Trade (DPIIT), Ministry of Commerce & Industry:
https://eaindustry.nic.in/ici_download_data.asp

No API keys or third-party gateways (e.g., data.gov.in) required.
"""
import io
import os
import re
from urllib.parse import urljoin

import certifi
import pandas as pd
import requests
from bs4 import BeautifulSoup
from .base import BaseProvider, ProviderResult, create_provider_result


class ICIProvider(BaseProvider):
    BASE_URL = "https://eaindustry.nic.in/ici_download_data.asp"

    def __init__(self):
        super().__init__()
        self.fallback_dir = os.path.join(
            os.path.expanduser('~'), '.macro_intelligence_platform', 'data'
        )
        os.makedirs(self.fallback_dir, exist_ok=True)
        self.cache_file = os.path.join(self.fallback_dir, 'ici_cache.csv')

    @property
    def name(self) -> str:
        return 'DPIIT (eaindustry.nic.in)'

    @property
    def update_frequency(self) -> str:
        return 'monthly'

    def _parse_excel_content(self, content: bytes) -> pd.Series:
        """Parse DPIIT Core Industries Excel file into a clean date-indexed Series."""
        excel = pd.ExcelFile(io.BytesIO(content))
        sheet_name = 'Index' if 'Index' in excel.sheet_names else excel.sheet_names[0]
        df = pd.read_excel(excel, sheet_name=sheet_name)

        # Check if first row contains column headers
        if 'month' not in str(df.columns[0]).lower():
            df.columns = [str(x).strip() for x in df.iloc[0]]
            df = df.iloc[1:].reset_index(drop=True)

        date_col = df.columns[0]
        val_col = None
        for col in df.columns:
            if 'overall' in str(col).lower():
                val_col = col
                break
        if val_col is None:
            val_col = df.columns[1]

        series_data = {}
        for _, row in df.iterrows():
            d_val = str(row[date_col]).strip()
            v_val = row[val_col]

            if any(term in d_val for term in ['(', 'Apr-Mar', 'Apr-Jun']) or d_val.lower() in ['nan', 'none', 'months/years', 'months']:
                continue

            try:
                val_float = float(v_val)
                dt = pd.NaT

                # Try format like 'Apr-23' or 'Jun-26'
                if re.match(r'^[A-Za-z]{3}-\d{2}$', d_val):
                    dt = pd.to_datetime('01-' + d_val, format='%d-%b-%y', errors='coerce')
                elif re.match(r'^[A-Za-z]{3}-\d{4}$', d_val):
                    dt = pd.to_datetime('01-' + d_val, format='%d-%b-%Y', errors='coerce')

                if pd.isna(dt):
                    dt = pd.to_datetime(d_val, errors='coerce')

                if not pd.isna(dt):
                    series_data[dt.strftime('%Y-%m-01')] = val_float
            except Exception:
                continue

        s = pd.Series(series_data)
        s.index = pd.to_datetime(s.index)
        return s.sort_index()

    def fetch(self, symbol: str = 'INDICI', start_date: str = '2000-01-01', end_date: str | None = None,
              return_meta: bool = False) -> pd.Series | ProviderResult:
        """Fetch ICI data directly from DPIIT website, chain-linking historical bases."""
        print(f"Fetching ICI data directly from DPIIT ({self.BASE_URL})...")
        headers = {'User-Agent': 'Mozilla/5.0'}
        source_type = "live"

        try:
            html = requests.get(self.BASE_URL, headers=headers, timeout=12,
                                 verify=certifi.where()).text
            soup = BeautifulSoup(html, 'html.parser')

            excel_urls = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                if 'Core_Industries' in href:
                    excel_urls.append(urljoin(self.BASE_URL, href))

            if not excel_urls:
                raise Exception("No Core Industries download links found on DPIIT portal")

            url_2022 = next((u for u in excel_urls if '2022_23' in u), None)
            url_2011 = next((u for u in excel_urls if '2011_12' in u), None)

            s11, s22 = None, None
            if url_2011:
                content_11 = requests.get(url_2011, headers=headers, timeout=15,
                                           verify=certifi.where()).content
                s11 = self._parse_excel_content(content_11)

            if url_2022:
                content_22 = requests.get(url_2022, headers=headers, timeout=15,
                                           verify=certifi.where()).content
                s22 = self._parse_excel_content(content_22)

            if (s11 is None or s11.empty) and (s22 is None or s22.empty):
                raise Exception("Failed to parse any valid ICI series from DPIIT Excel files")

            if s11 is not None and not s11.empty and s22 is not None and not s22.empty:
                # Chain-link the 2011-12 base series to the 2022-23 base.
                # The two series use different base years (2011-12=100 vs 2022-23=100),
                # so raw concatenation creates an artificial step-jump.
                # We scale the older series so its value at the overlap point matches
                # the first value of the newer series, producing a continuous index.
                overlap_date = s22.index[0]
                # Find the closest date in the old series at or just before the overlap
                s11_before_overlap = s11[s11.index < overlap_date]
                if not s11_before_overlap.empty:
                    old_value_at_join = s11_before_overlap.iloc[-1]
                    new_value_at_join = s22.iloc[0]
                    if old_value_at_join != 0:
                        scale_factor = new_value_at_join / old_value_at_join
                        s11_rebased = s11_before_overlap * scale_factor
                        combined = pd.concat([s11_rebased, s22])
                    else:
                        combined = s22
                else:
                    combined = s22
            elif s22 is not None and not s22.empty:
                combined = s22
            else:
                combined = s11

            combined.name = 'ICI'
            combined.index.name = 'Date'

            # Save to cache
            combined.to_csv(self.cache_file)
            print(f"  [+] Successfully fetched {len(combined)} months of ICI data (Latest: {combined.index[-1].strftime('%b %Y')})")

            series = combined[combined.index >= start_date]

        except Exception as e:
            print(f"  [!] Direct DPIIT fetch failed: {e}. Falling back to cache...")
            series, source_type = self._load_from_cache(start_date)

        if return_meta:
            return create_provider_result(series, source_type, symbol, details=self.name)
        return series

    def _load_from_cache(self, start_date: str) -> tuple[pd.Series, str]:
        if os.path.exists(self.cache_file):
            try:
                df = pd.read_csv(self.cache_file, index_col='Date', parse_dates=True)
                series = df.iloc[:, 0]
                return series[series.index >= start_date], "cache"
            except Exception as e:
                print(f"Error reading ICI cache: {e}")

        print("Warning: No valid local ICI cache found.")
        return pd.Series(dtype=float, name='ICI'), "bundled_fallback"
