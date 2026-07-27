export type Regime = 'Expansion' | 'Slowdown' | 'Contraction' | 'Recovery'

export interface Frame {
  i: number
  date: string
  label: string
  x: number
  y: number
  velocity: number | null
  quadrant: Regime
  raw: number | null
}

export interface SplinePoint {
  t: number
  x: number
  y: number
}

export interface Bounds {
  center: number
  min: number
  max: number
  extent: number
}

export interface SeriesMeta {
  type: string | null
  symbol: string | null
}

export interface HealthEntry {
  source?: string
  release_date?: string
  cache_status?: string
  [key: string]: unknown
}

export interface CyclePayload {
  market: string
  label: string
  as_of: string
  config: {
    name: string
    ticker: string
    source: string
    frequency: string
    window: number
    center: number
    tail_length: number
  }
  bounds: Bounds
  frames: Frame[]
  spline: SplinePoint[]
  points_per_segment: number
  data_health: Record<string, HealthEntry>
  warnings: string[]
  market_series: Record<string, SeriesMeta>
  domestic_indices: string[]
  global_indices: string[]
}

export interface MarketProfile {
  id: string
  label: string
  indicator: string
  ticker: string
  market_series: string[]
  macro_series: string[]
  domestic_indices: string[]
  global_indices: string[]
}

export interface AssetRow {
  name: string
  current_val_str: string
  returns_str: Record<string, string>
  returns_raw: Record<string, number | null>
  type: string | null
}

export interface MacroDriver {
  indicator: string
  score: number | null
  state: string
  symbol: string
}

export interface PhaseContext {
  quadrant: Regime
  entered: string
  entered_label: string
  duration_months: number
  previous_quadrant: Regime | null
}

export interface Narrative {
  executive_summary?: string
  takeaways?: string[]
  interpretation?: string
  risks?: string[]
  methodology?: string
  [key: string]: unknown
}

export interface FramePayload {
  market: string
  index: number
  date: string
  quadrant: Regime
  health: number
  momentum: number
  center: number
  distance: number
  direction: string
  indicator: string
  source: string
  window: string
  raw_value: number | null
  phase: PhaseContext
  macro_contrib: {
    all_drivers?: MacroDriver[]
    macro_score?: number | null
    [key: string]: unknown
  } | null
  macro_shifts: string[] | null
  research_narrative: unknown
  market_data: AssetRow[]
  analysis: Record<string, unknown>
  insights: Record<string, unknown>
  market_insights: {
    insights?: string[]
    market_score?: number
    best_asset?: unknown
    worst_asset?: unknown
    [key: string]: unknown
  }
  analogues: {
    matches?: Array<Record<string, unknown>>
    [key: string]: unknown
  }
  narrative: Narrative
  selected_assets: string[]
}

export interface HorizonForecast {
  x: number
  y: number
  quadrant: Regime
  conviction: number
}

export interface BandPoint {
  x: number
  y: number
  dx: number
  dy: number
}

export interface Scenario {
  name: string
  probability: number
  projected_quadrant_3m: Regime | 'N/A'
  projected_quadrant_6m: Regime | 'N/A'
  projected_quadrant_9m: Regime | 'N/A'
  expected_market_return_6m: number | null
  path: Array<[number, number]>
  key_assumption: string
  trigger: string
}

export interface ForecastPayload {
  market: string
  index: number
  as_of: string
  current_regime: Regime
  forecasts: Record<string, HorizonForecast>
  conviction: number | null
  projected_path: Array<[number, number]>
  confidence_band: { inner?: BandPoint[]; outer?: BandPoint[] }
  residual_std: Record<string, number>
  signal_contributions: Record<string, unknown>
  scenarios: Scenario[]
  transitions: {
    matrix?: number[][]
    labels?: Regime[]
    counts?: number[][]
    steady_state?: number[]
    durations?: Record<string, Record<string, number>>
  }
  analogues: Record<string, unknown>
  model_version: string
}
