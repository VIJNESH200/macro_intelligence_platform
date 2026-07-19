"""
Economic Regime Intelligence Platform — Configuration
============================================
Central configuration for indicators, market series, UI colors, and platform metadata.
"""

VERSION = '2.5'

# ---------------------------------------------------------------------------
# Primary Indicator Configuration
# ---------------------------------------------------------------------------
CONFIG = {
    "name": "India CLI (OECD)",
    "ticker": "INDLOLITOAASTSAM",
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
    'Nifty 50':         {'type': 'yfinance', 'symbol': '^NSEI',       'format': '{:,.2f}'},
    'Sensex':           {'type': 'yfinance', 'symbol': '^BSESN',      'format': '{:,.2f}'},
    'Nifty Bank':       {'type': 'yfinance', 'symbol': '^NSEBANK',    'format': '{:,.2f}'},
    'S&P 500':          {'type': 'yfinance', 'symbol': '^GSPC',       'format': '{:,.2f}'},
    'Nasdaq 100':       {'type': 'yfinance', 'symbol': '^NDX',        'format': '{:,.2f}'},
    'India 10Y Yield':  {'type': 'fred',     'symbol': 'INDIRLTLT01STM', 'format': '{:.2f}%'},
    'US 10Y Yield':     {'type': 'yfinance', 'symbol': '^TNX',        'format': '{:.2f}%'},
    'USD/INR':          {'type': 'yfinance', 'symbol': 'INR=X',       'format': '{:.2f}'},
    'Gold':             {'type': 'yfinance', 'symbol': 'GC=F',        'format': '{:,.2f}'},
    'Brent Crude':      {'type': 'yfinance', 'symbol': 'BZ=F',        'format': '{:.2f}'},
    'India VIX':        {'type': 'yfinance', 'symbol': '^INDIAVIX',   'format': '{:.2f}'}
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
    'PMI':              IndicatorConfig(name='PMI', source='s_and_p', ticker='INDPMI', format='{:.1f}', transformation='level'),
    'CPI':              IndicatorConfig(name='CPI', source='mospi', ticker='INDCPIALLMINMEI', format='{:.2f}', transformation='yoy'),
    'IIP':              IndicatorConfig(name='IIP', source='mospi', ticker='INDPROINDMISMEI', format='{:.2f}', transformation='yoy'),
    'Yield 10Y':        IndicatorConfig(name='Yield 10Y', source='rbi', ticker='INDIRLTLT01STM', format='{:.2f}%', transformation='level'),
    'Yield Short':      IndicatorConfig(name='Yield Short', source='rbi', ticker='INDIRLSTT01STM', format='{:.2f}%', transformation='level'),
    'Yield Spread':     IndicatorConfig(name='Yield Spread', source='yield', ticker='SPREAD', format='{:.2f}%', transformation='spread'),
    'Real Policy Rate': IndicatorConfig(name='Real Policy Rate', source='rbi', ticker='IRSTCB01INM156N', format='{:.2f}%', transformation='real_rate') 
}

# ---------------------------------------------------------------------------
# Indicator Registry (extensible for Phase 2+)
# ---------------------------------------------------------------------------
INDICATOR_REGISTRY = {
    'oecd_cli_india': {
        'name': 'India CLI (OECD)',
        'ticker': 'INDLOLITOAASTSAM',
        'source': 'FRED',
        'frequency': 'Monthly',
        'normalization': 'z_score',
        'center': 100,
        'description': 'OECD Composite Leading Indicator for India'
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
    'horizons': [3, 6],                # months forward
    'decay_factor': 0.85,              # mean-reversion decay per month
    'weights': {
        'momentum': 0.40,
        'analogues': 0.35,
        'macro_drivers': 0.25,
    },
    'confidence_decay_per_month': 0.15,
    'scenario_sigma': 1.0,             # standard deviations for bull/bear
    'analogue_similarity_weights': {
        'xy': 0.60,                    # weight for X/Y Euclidean distance
        'macro': 0.40,                 # weight for macro driver Z-score distance
    },
}
