import type { Regime } from './types'

/**
 * Regime presentation.
 *
 * `color` is the reserved status palette. Those four hues do NOT clear CVD
 * separation against each other (red vs green, deutan dE 4.1), so they are used
 * only as low-alpha territory washes and as swatches beside text. Every place a
 * regime appears it is named in words -- `label` is not optional decoration.
 */
export const REGIMES: Record<Regime, { label: string; color: string; blurb: string }> = {
  Expansion: {
    label: 'Expansion',
    color: 'var(--regime-expansion)',
    blurb: 'Bullish macro environment',
  },
  Slowdown: {
    label: 'Slowdown',
    color: 'var(--regime-slowdown)',
    blurb: 'Cautious / peak environment',
  },
  Contraction: {
    label: 'Contraction',
    color: 'var(--regime-contraction)',
    blurb: 'Bearish macro environment',
  },
  Recovery: {
    label: 'Recovery',
    color: 'var(--regime-recovery)',
    blurb: 'Improving macro environment',
  },
}

export const REGIME_ORDER: Regime[] = ['Expansion', 'Slowdown', 'Contraction', 'Recovery']

/** Quadrant corner each regime occupies, in fractional plot coordinates. */
export const REGIME_CORNERS: Record<Regime, { fx: number; fy: number; anchor: 'start' | 'end' }> = {
  Expansion: { fx: 0.98, fy: 0.04, anchor: 'end' },
  Slowdown: { fx: 0.98, fy: 0.97, anchor: 'end' },
  Contraction: { fx: 0.02, fy: 0.97, anchor: 'start' },
  Recovery: { fx: 0.02, fy: 0.04, anchor: 'start' },
}

export function regimeOf(x: number, y: number, center: number): Regime {
  if (x >= center) return y >= center ? 'Expansion' : 'Slowdown'
  return y >= center ? 'Recovery' : 'Contraction'
}

/**
 * The engines report movement as a compass bearing in the health/momentum
 * plane ("Northeast"). That is an artefact of the chart's geometry, not
 * something a reader can act on -- so it is translated back into the two things
 * it actually encodes: which way health moved, and which way momentum moved.
 *
 * X (east/west) is health, Y (north/south) is momentum.
 */
const DIRECTION_MEANING: Record<string, { short: string; long: string }> = {
  Northeast: { short: 'Health ↑ · Momentum ↑', long: 'Both strengthening' },
  North: { short: 'Momentum ↑', long: 'Momentum strengthening' },
  Northwest: { short: 'Health ↓ · Momentum ↑', long: 'Momentum turning up off weak health' },
  West: { short: 'Health ↓', long: 'Health weakening' },
  Southwest: { short: 'Health ↓ · Momentum ↓', long: 'Both deteriorating' },
  South: { short: 'Momentum ↓', long: 'Momentum rolling over' },
  Southeast: { short: 'Health ↑ · Momentum ↓', long: 'Health holding as momentum fades' },
  East: { short: 'Health ↑', long: 'Health strengthening' },
  Neutral: { short: 'Flat', long: 'No material change' },
}

export function describeDirection(direction: string | null | undefined): {
  short: string
  long: string
} {
  return DIRECTION_MEANING[direction ?? ''] ?? { short: direction || '—', long: '' }
}

export function signed(value: number | null | undefined, digits = 2): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return '—'
  return `${value > 0 ? '+' : ''}${value.toFixed(digits)}`
}

export function fixed(value: number | null | undefined, digits = 2): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return '—'
  return value.toFixed(digits)
}
