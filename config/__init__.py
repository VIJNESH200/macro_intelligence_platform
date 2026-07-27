from __future__ import annotations
"""
Configuration package for Macro Intelligence Platform.
"""
import os
from .markets import get_market_config

_MARKET_PREF_FILE = os.path.join(os.path.expanduser('~'), '.macro_intelligence_platform', 'market_preference.txt')


def _load_market_preference() -> str | None:
    """Read the last market the user switched to, if any was saved."""
    try:
        with open(_MARKET_PREF_FILE) as f:
            saved = f.read().strip()
        return saved if saved in ('INDIA', 'US') else None
    except OSError:
        return None


def save_market_preference(market: str) -> None:
    """Persist the selected market so it's restored on the next launch."""
    try:
        os.makedirs(os.path.dirname(_MARKET_PREF_FILE), exist_ok=True)
        with open(_MARKET_PREF_FILE, 'w') as f:
            f.write(market)
    except OSError:
        pass


# Global market selection (can be overridden at runtime).
# Precedence: explicit $MARKET env var > last saved preference > India default.
_CURRENT_MARKET = os.getenv('MARKET') or _load_market_preference() or 'INDIA'


def get_current_market() -> str:
    """Get the currently selected market."""
    return _CURRENT_MARKET


def set_market(market: str) -> None:
    """Set the current market and invalidate caches."""
    global _CURRENT_MARKET
    if market not in ['INDIA', 'US']:
        raise ValueError(f"Unknown market: {market}")
    _CURRENT_MARKET = market
    # Signal that caches should be cleared on reload
    os.environ['MARKET_CHANGED'] = '1'


def get_market_label() -> str:
    """Get a human-readable label for the current market."""
    market_config = get_market_config(_CURRENT_MARKET)
    return market_config['label']


VERSION = '2.5'

# Load active configuration
_active_config = get_market_config(_CURRENT_MARKET)

# Export active CONFIG for backward compatibility
CONFIG = {
    **_active_config['primary_indicator'],
    'version': VERSION
}

MARKET_SERIES = _active_config['market_series'].copy()
MACRO_SERIES = _active_config['macro_series'].copy()

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

QUADRANTS = {
    'Expansion':   {'color': 'green',      'alpha': 0.04, 'label_color': 'darkgreen'},
    'Slowdown':    {'color': 'goldenrod',   'alpha': 0.04, 'label_color': 'darkgoldenrod'},
    'Contraction': {'color': 'red',         'alpha': 0.04, 'label_color': 'darkred'},
    'Recovery':    {'color': 'blue',        'alpha': 0.04, 'label_color': 'darkblue'},
}

FORECAST_CONFIG = {
    'horizons': [3, 6, 9],
    'decay_factor': 0.85,
    # Per-market; reload_for_market() swaps these in place.
    'weights': dict(_active_config['forecast_weights']),
    'confidence_decay_per_month': 0.15,
    'scenario_sigma': 1.0,
    'analogue_similarity_weights': {
        'xy': 0.60,
        'macro': 0.40,
    },
}

INDICATOR_REGISTRY = {
    'oecd_cli_india': {
        'name': 'India CLI (OECD)',
        'ticker': 'INDLOLITOAASTSAM',
        'source': 'FRED',
        'frequency': 'Monthly',
        'normalization': 'z_score',
        'center': 100,
        'description': 'OECD Composite Leading Indicator for India'
    },
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


def reload_for_market(market: str) -> None:
    """Reload configuration for a new market."""
    global CONFIG, MARKET_SERIES, MACRO_SERIES, _CURRENT_MARKET

    if market not in ['INDIA', 'US']:
        raise ValueError(f"Unknown market: {market}")

    _CURRENT_MARKET = market
    _active_config = get_market_config(market)

    CONFIG.clear()
    CONFIG.update({
        **_active_config['primary_indicator'],
        'version': VERSION
    })

    MARKET_SERIES.clear()
    MARKET_SERIES.update(_active_config['market_series'])

    MACRO_SERIES.clear()
    MACRO_SERIES.update(_active_config['macro_series'])

    FORECAST_CONFIG['weights'].clear()
    FORECAST_CONFIG['weights'].update(_active_config['forecast_weights'])

    os.environ['MARKET_CHANGED'] = '1'
