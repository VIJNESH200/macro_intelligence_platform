from __future__ import annotations
"""
Market Profiles — Centralized market-specific configurations.
==============================================================
Defines complete market profiles for India and US including
indicator config, market series, macro drivers, and market rules.
"""

from dataclasses import dataclass

@dataclass
class IndicatorConfig:
    name: str
    source: str
    ticker: str
    format: str = '{:.2f}'
    transformation: str = 'level'


MARKET_PROFILES = {
    'INDIA': {
        'label': 'India Market',
        'primary_indicator': {
            "name": "India CLI (OECD)",
            "ticker": "INDLOLITOAASTSAM",
            "window": 36,
            "source": "FRED",
            "frequency": "Monthly",
            "center": 100,
            "tail_length": 12,
            "points_per_segment": 10,
            "padding": 0.10,
        },
        'market_series': {
            'Sensex':           {'type': 'yfinance', 'symbol': '^BSESN',      'format': '{:,.2f}'},
            'Nifty 50':         {'type': 'yfinance', 'symbol': '^NSEI',       'format': '{:,.2f}'},
            'Nifty Bank':       {'type': 'yfinance', 'symbol': '^NSEBANK',    'format': '{:,.2f}'},
            'S&P 500':          {'type': 'yfinance', 'symbol': '^GSPC',       'format': '{:,.2f}'},
            'Nasdaq 100':       {'type': 'yfinance', 'symbol': '^NDX',        'format': '{:,.2f}'},
            'India 10Y Yield':  {'type': 'fred',     'symbol': 'INDIRLTLT01STM', 'format': '{:.2f}%'},
            'US 10Y Yield':     {'type': 'yfinance', 'symbol': '^TNX',        'format': '{:.2f}%'},
            'USD/INR':          {'type': 'yfinance', 'symbol': 'INR=X',       'format': '{:.2f}'},
            'Gold':             {'type': 'yfinance', 'symbol': 'GC=F',        'format': '{:,.2f}'},
            'Brent Crude':      {'type': 'yfinance', 'symbol': 'BZ=F',        'format': '{:.2f}'},
            'India VIX':        {'type': 'yfinance', 'symbol': '^INDIAVIX',   'format': '{:.2f}'}
        },
        'macro_series': {
            'ICI':              IndicatorConfig(name='ICI', source='ici', ticker='INDICI', format='{:.1f}', transformation='yoy'),
            'CPI':              IndicatorConfig(name='CPI', source='imf', ticker='IND.CPI._T.IX.M', format='{:.2f}', transformation='yoy'),
            'Yield 10Y':        IndicatorConfig(name='Yield 10Y', source='rbi', ticker='INDIRLTLT01STM', format='{:.2f}%', transformation='level'),
            'Yield Short':      IndicatorConfig(name='Yield Short', source='rbi', ticker='INDIRLSTT01STM', format='{:.2f}%', transformation='level'),
            'Yield Spread':     IndicatorConfig(name='Yield Spread', source='yield', ticker='SPREAD', format='{:.2f}%', transformation='spread'),
            'Real Policy Rate': IndicatorConfig(name='Real Policy Rate', source='rbi', ticker='IRSTCB01INM156N', format='{:.2f}%', transformation='real_rate')
        },
        'domestic_indices': ['Sensex', 'Nifty 50', 'Nifty Bank'],
        'global_indices': ['S&P 500', 'Nasdaq 100'],
    },
    'US': {
        'label': 'US Market',
        'primary_indicator': {
            "name": "US CLI (OECD)",
            "ticker": "USALOLITOAASTSAM",
            "window": 36,
            "source": "FRED",
            "frequency": "Monthly",
            "center": 100,
            "tail_length": 12,
            "points_per_segment": 10,
            "padding": 0.10,
        },
        'market_series': {
            'S&P 500':          {'type': 'yfinance', 'symbol': '^GSPC',       'format': '{:,.2f}'},
            'Nasdaq 100':       {'type': 'yfinance', 'symbol': '^NDX',        'format': '{:,.2f}'},
            'Dow Jones':        {'type': 'yfinance', 'symbol': '^DJI',        'format': '{:,.2f}'},
            'Russell 2000':     {'type': 'yfinance', 'symbol': '^RUT',        'format': '{:,.2f}'},
            'US 10Y Yield':     {'type': 'yfinance', 'symbol': '^TNX',        'format': '{:.2f}%'},
            'US 2Y Yield':      {'type': 'fred',     'symbol': 'DGS2',        'format': '{:.2f}%'},
            'Dollar Index':     {'type': 'yfinance', 'symbol': 'DX-Y.NYB',    'format': '{:.2f}'},
            'Gold':             {'type': 'yfinance', 'symbol': 'GC=F',        'format': '{:,.2f}'},
            'WTI Crude':        {'type': 'yfinance', 'symbol': 'CL=F',        'format': '{:.2f}'},
            'VIX':              {'type': 'yfinance', 'symbol': '^VIX',        'format': '{:.2f}'}
        },
        'macro_series': {
            'CPI':              IndicatorConfig(name='CPI', source='fred', ticker='CPIAUCSL', format='{:.2f}', transformation='yoy'),
            'Yield 10Y':        IndicatorConfig(name='Yield 10Y', source='fred', ticker='GS10', format='{:.2f}%', transformation='level'),
            'Yield Short':      IndicatorConfig(name='Yield Short', source='fred', ticker='TB3MS', format='{:.2f}%', transformation='level'),
            'Yield Spread':     IndicatorConfig(name='Yield Spread', source='fred', ticker='T10Y3M', format='{:.2f}%', transformation='spread'),
            'Real Policy Rate': IndicatorConfig(name='Real Policy Rate', source='fred', ticker='FEDFUNDS', format='{:.2f}%', transformation='real_rate')
        },
        'domestic_indices': ['S&P 500', 'Nasdaq 100'],
        'global_indices': [],
    }
}


def get_market_config(market: str = 'US') -> dict:
    """Get configuration for a specific market."""
    if market not in MARKET_PROFILES:
        raise ValueError(f"Unknown market: {market}. Choose from {list(MARKET_PROFILES.keys())}")
    return MARKET_PROFILES[market]
