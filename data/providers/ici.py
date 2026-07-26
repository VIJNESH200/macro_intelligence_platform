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
from datetime import datetime
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

        except Exception as e:
            print(f"  [!] Failed to parse DPIIT Excel file: {e}")
            return pd.Series(dtype=float)

    def fetch(self, symbol: str = 'INDICI', start_date: str = '2000-01-01', return_meta: bool = False) -> pd.Series | ProviderResult:
        """Fetch ICI data directly from DPIIT website, chain-linking historical bases."""
        source_type = "live"
        try:
            req = urllib.request.Request(
                self.BASE_URL,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            html_content = self._urlopen_secure(req, timeout=15)
            soup = BeautifulSoup(html_content, 'html.parser')

            link_1112 = None
            link_2223 = None

            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                text = a_tag.get_text()
                if '2011' in href or '2011' in text:
                    link_1112 = urljoin(self.BASE_URL, href)
                elif '2022' in href or '2022' in text:
                    link_2223 = urljoin(self.BASE_URL, href)

            s11 = None
            s22 = None

            if link_1112:
                req11 = urllib.request.Request(link_1112, headers={'User-Agent': 'Mozilla/5.0'})
                content11 = self._urlopen_secure(req11, timeout=15)
                s11 = self._parse_excel_content(content11)

            if link_2223:
                req22 = urllib.request.Request(link_2223, headers={'User-Agent': 'Mozilla/5.0'})
                content22 = self._urlopen_secure(req22, timeout=15)
                s22 = self._parse_excel_content(content22)

            if s11 is not None and not s11.empty and s22 is not None and not s22.empty:
                overlap_date = s22.index[0]
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
