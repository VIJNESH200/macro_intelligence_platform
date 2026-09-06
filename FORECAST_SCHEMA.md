# Forecast Output Specification (`forecast_schema.json`)

The Macro Intelligence Platform serializes its forecast payload into a standardized JSON format. This document describes the structure of `docs/latest_forecast.json`.

---

## Field Specifications

| Field | Type | Description |
|---|---|---|
| `as_of` | `string` (ISO Date) | Observation date of the latest historical datapoint (e.g. `"2026-06-30"`). |
| `current_regime` | `string` | Quadrant call: `"Expansion"`, `"Slowdown"`, `"Contraction"`, or `"Recovery"`. |
| `forecasts` | `object` | Map of horizon forecasts (`"3m"`, `"6m"`, `"9m"`). |
| `forecasts.<h>.x` | `number` | Projected Economic Health coordinate ($X$). |
| `forecasts.<h>.y` | `number` | Projected Economic Momentum coordinate ($Y$). |
| `forecasts.<h>.quadrant` | `string` | Projected regime quadrant at horizon $h$. |
| `forecasts.<h>.conviction` | `number` | Horizon conviction percentage score (0–100%). |
| `conviction` | `number` | Headline 6-month forecast conviction percentage score. |
| `model_version` | `string` | Platform version string (e.g. `"2.5.0"`). |
| `data_health` | `object` | Provider metadata per series (`source`, `as_of`, `schema_ok`, `fetched_at`). |
| `projected_path` | `array` | List of 2D `[X, Y]` coordinate tuples tracing the projected 6-month trajectory. |
| `confidence_band` | `object` | Inner (50th percentile) and outer (80th percentile) confidence ellipse boundaries. |

---

## Example Payload

```json
{
  "as_of": "2026-06-30",
  "current_regime": "Expansion",
  "forecasts": {
    "6m": {
      "x": 101.42,
      "y": 100.85,
      "quadrant": "Expansion",
      "conviction": 71.6
    }
  },
  "conviction": 71.6,
  "model_version": "2.5.0",
  "data_health": {
    "India CLI (OECD)": {
      "source": "live",
      "as_of": "2026-06-30",
      "schema_ok": true
    }
  }
}
```
