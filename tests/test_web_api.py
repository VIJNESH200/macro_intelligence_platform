from __future__ import annotations
"""
Tests for the FastAPI web layer.
================================
Covers the contract the React frontend depends on, plus the two hazards
specific to serving this compute layer over HTTP:

  1. JSON validity -- pandas produces NaN, which is not a JSON literal.
  2. Market isolation -- `reload_for_market` mutates module globals that the
     analytics engines read at call time, so concurrent cross-market requests
     could otherwise return data computed under the wrong configuration.

These hit the real data path (served from the on-disk cache), so they are
slower than the unit tests but exercise the composition end to end.
"""
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from web.server import app  # noqa: E402
from web.serialization import to_jsonable  # noqa: E402

EXPECTED_INDICATOR = {'INDIA': 'India CLI (OECD)', 'US': 'US CLI (OECD)'}


@pytest.fixture(scope='module')
def client():
    with TestClient(app) as test_client:
        yield test_client


# ----------------------------------------------------------------------
# Serialization
# ----------------------------------------------------------------------
def test_non_finite_floats_become_null():
    """NaN and Infinity are not valid JSON; they must serialize as null."""
    import numpy as np

    payload = to_jsonable({
        'nan': float('nan'),
        'inf': float('inf'),
        'neg_inf': float('-inf'),
        'np_nan': np.float64('nan'),
        'np_int': np.int64(7),
        'np_bool': np.bool_(True),
        'ok': 1.5,
    })

    assert payload['nan'] is None
    assert payload['inf'] is None
    assert payload['neg_inf'] is None
    assert payload['np_nan'] is None
    assert payload['np_int'] == 7
    assert payload['np_bool'] is True
    assert payload['ok'] == 1.5
    json.dumps(payload)  # must not raise


def test_responses_contain_no_bare_nan(client):
    """Early frames have incomplete market history -- a prime source of NaN."""
    for path in ('/api/frame/40?market=INDIA', '/api/frame/0?market=INDIA', '/api/cycle?market=INDIA'):
        response = client.get(path)
        assert response.status_code == 200, path
        assert 'NaN' not in response.text, f'bare NaN leaked in {path}'
        assert 'Infinity' not in response.text, f'bare Infinity leaked in {path}'
        json.loads(response.text)


# ----------------------------------------------------------------------
# Contract
# ----------------------------------------------------------------------
def test_health_and_markets(client):
    health = client.get('/api/health').json()
    assert health['status'] == 'ok'
    assert set(health['markets']) == {'INDIA', 'US'}

    markets = client.get('/api/markets').json()
    assert {m['id'] for m in markets} == {'INDIA', 'US'}
    assert all(m['market_series'] for m in markets)


@pytest.mark.parametrize('market', ['INDIA', 'US'])
def test_cycle_shape(client, market):
    payload = client.get(f'/api/cycle?market={market}').json()

    assert payload['market'] == market
    assert payload['config']['name'] == EXPECTED_INDICATOR[market]
    assert len(payload['frames']) > 100

    # The spline is the render path; it must cover every frame gap.
    expected_spline = (len(payload['frames']) - 1) * payload['points_per_segment'] + 1
    assert len(payload['spline']) == expected_spline

    bounds = payload['bounds']
    assert bounds['min'] < bounds['center'] < bounds['max']

    frame = payload['frames'][-1]
    assert frame['quadrant'] in {'Expansion', 'Slowdown', 'Contraction', 'Recovery'}
    assert bounds['min'] <= frame['x'] <= bounds['max']


def test_quadrant_matches_coordinates(client):
    """The label must agree with the geometry it is derived from."""
    payload = client.get('/api/cycle?market=INDIA').json()
    center = payload['bounds']['center']

    for frame in payload['frames'][-40:]:
        x, y = frame['x'], frame['y']
        if x >= center:
            expected = 'Expansion' if y >= center else 'Slowdown'
        else:
            expected = 'Recovery' if y >= center else 'Contraction'
        assert frame['quadrant'] == expected, frame['date']


def test_frame_payload(client):
    payload = client.get('/api/frame/200?market=INDIA').json()

    assert payload['index'] == 200
    assert payload['quadrant'] in {'Expansion', 'Slowdown', 'Contraction', 'Recovery'}
    assert payload['phase']['duration_months'] >= 1
    assert isinstance(payload['market_data'], list)
    assert payload['analysis']
    assert payload['narrative']


def test_forecast_payload(client):
    payload = client.get('/api/forecast?market=INDIA').json()

    assert payload['forecasts'], 'expected at least one horizon'
    for horizon, forecast in payload['forecasts'].items():
        assert horizon.endswith('m')
        assert 0 <= forecast['conviction'] <= 100
        assert forecast['quadrant'] in {'Expansion', 'Slowdown', 'Contraction', 'Recovery'}

    # Confidence bands must line up with the path they wrap.
    for band in ('inner', 'outer'):
        assert len(payload['confidence_band'][band]) == len(payload['projected_path'])

    # Uncertainty grows with horizon; the last band is never tighter than the first.
    outer = payload['confidence_band']['outer']
    assert outer[-1]['dx'] >= outer[0]['dx']

    assert {s['name'] for s in payload['scenarios']} == {'Bull', 'Base', 'Bear'}


def test_transition_matrix_rows_sum_to_one(client):
    payload = client.get('/api/transitions?market=INDIA').json()

    for row in payload['matrix']:
        total = sum(row)
        assert total == pytest.approx(1.0, abs=1e-6) or total == pytest.approx(0.0)


def test_series_endpoint(client):
    payload = client.get('/api/series?market=INDIA&names=CLI_Raw,Sensex,NotAColumn').json()

    assert set(payload['series']) == {'CLI_Raw', 'Sensex'}
    assert payload['missing'] == ['NotAColumn']
    assert len(payload['dates']) == len(payload['series']['CLI_Raw'])


def test_report_download_is_a_pdf(client):
    """The Report button must download a real PDF, never a text error page."""
    response = client.get('/api/report?market=INDIA')

    assert response.status_code == 200
    assert response.headers['content-type'].startswith('application/pdf')
    assert '.pdf' in response.headers['content-disposition']
    assert response.content.startswith(b'%PDF-')


# ----------------------------------------------------------------------
# Error handling
# ----------------------------------------------------------------------
def test_unknown_market_is_404(client):
    response = client.get('/api/cycle?market=ATLANTIS')
    assert response.status_code == 404
    assert 'ATLANTIS' in response.json()['detail']


def test_out_of_range_index_clamps(client):
    assert client.get('/api/frame/99999?market=INDIA').json()['index'] > 0
    assert client.get('/api/frame/-5?market=INDIA').json()['index'] == 0


def test_series_requires_names(client):
    assert client.get('/api/series?market=INDIA&names=').status_code == 400


# ----------------------------------------------------------------------
# Market isolation -- the reason MarketStore serializes access
# ----------------------------------------------------------------------
def test_concurrent_cross_market_requests_stay_isolated(client):
    """Interleaved requests must never return another market's configuration."""
    def fetch(i: int) -> tuple[str, str]:
        market = 'INDIA' if i % 2 == 0 else 'US'
        return market, client.get(f'/api/frame/150?market={market}').json()['indicator']

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(fetch, range(16)))

    assert results, 'expected results'
    for market, indicator in results:
        assert indicator == EXPECTED_INDICATOR[market]


def test_switching_market_does_not_leak_config(client):
    """Sequential switches must fully re-key, including back to the original."""
    first = client.get('/api/cycle?market=INDIA').json()
    client.get('/api/cycle?market=US')
    again = client.get('/api/cycle?market=INDIA').json()

    assert first['config'] == again['config']
    assert set(first['market_series']) == set(again['market_series'])
