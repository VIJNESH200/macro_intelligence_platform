from __future__ import annotations
"""
Economic Regime Intelligence Platform — Configuration
============================================
Central configuration for indicators, market series, UI colors, and platform metadata.
"""

import os

VERSION = '2.5'

# ---------------------------------------------------------------------------
# Primary Indicator Configuration
# ---------------------------------------------------------------------------
CONFIG = {
    "name": "US CLI (OECD)",
    "ticker": "USALOLITOAASTSAM",
    "window": 36,
    "source": "FRED",
    "frequency": "Monthly",
    "center": 100,
    "tail_length": 12,
    "points_per_segment": 10,
    "padding": 0.10,
    "version": VERSION
}

# ---------------------------------------------------------------------------
# Market Context Series
# ---------------------------------------------------------------------------
MARKET_SERIES = {
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
}

from dataclasses import dataclass

@dataclass
class IndicatorConfig:
    name: str
    source: str
    ticker: str
    format: str = '{:.2f}'
    transformation: str = 'level'

# ---------------------------------------------------------------------------
# Macro Driver Series (Phase 2)
# ---------------------------------------------------------------------------
MACRO_SERIES = {
    'CPI':              IndicatorConfig(name='CPI', source='fred', ticker='CPIAUCSL', format='{:.2f}', transformation='yoy'),
    'Yield 10Y':        IndicatorConfig(name='Yield 10Y', source='fred', ticker='GS10', format='{:.2f}%', transformation='level'),
    'Yield Short':      IndicatorConfig(name='Yield Short', source='fred', ticker='TB3MS', format='{:.2f}%', transformation='level'),
    'Yield Spread':     IndicatorConfig(name='Yield Spread', source='fred', ticker='T10Y3M', format='{:.2f}%', transformation='spread'),
    'Real Policy Rate': IndicatorConfig(name='Real Policy Rate', source='fred', ticker='FEDFUNDS', format='{:.2f}%', transformation='real_rate')
}

# ---------------------------------------------------------------------------
# Indicator Registry (extensible for Phase 2+)
# ---------------------------------------------------------------------------
INDICATOR_REGISTRY = {
    'oecd_cli_us': {
        'name': 'US CLI (OECD)',
        'ticker': 'USALOLITOAASTSAM',
        'source': 'FRED',
        'frequency': 'Monthly',
        'normalization': 'z_score',
        'center': 100,
        'description': 'OECD Composite Leading Indicator for the United States'
    }
}

# ---------------------------------------------------------------------------
# UI Color Palette
# ---------------------------------------------------------------------------
COLORS = {
    'bg':           '#f8f9fa',
    'text':         '#333333',
    'text_light':   '#555555',
    'navy':         '#1f497d',
    'expansion':    'darkgreen',
    'slowdown':     'darkgoldenrod',
    'contraction':  'darkred',
    'recovery':     'darkblue',
    'grid':         'lightgray',
    'border':       '#cccccc',
    'highlight':    '#e8f0fe',
}

# ---------------------------------------------------------------------------
# Quadrant Definitions
# ---------------------------------------------------------------------------
QUADRANTS = {
    'Expansion':   {'color': 'green',      'alpha': 0.04, 'label_color': 'darkgreen'},
    'Slowdown':    {'color': 'goldenrod',   'alpha': 0.04, 'label_color': 'darkgoldenrod'},
    'Contraction': {'color': 'red',         'alpha': 0.04, 'label_color': 'darkred'},
    'Recovery':    {'color': 'blue',        'alpha': 0.04, 'label_color': 'darkblue'},
}

# ---------------------------------------------------------------------------
# Forecasting Configuration (Phase 3)
# ---------------------------------------------------------------------------
FORECAST_CONFIG = {
    'horizons': [3, 6, 9],              # months forward
    'decay_factor': 0.85,              # mean-reversion decay per month
    'weights': {
        'momentum': 0.55,
        'analogues': 0.45,
        'macro_drivers': 0.00,
    },
    'confidence_decay_per_month': 0.15,
    'scenario_sigma': 1.0,             # standard deviations for bull/bear
    'analogue_similarity_weights': {
        'xy': 0.60,                    # weight for X/Y Euclidean distance
        'macro': 0.40,                 # weight for macro driver Z-score distance
    },
}
