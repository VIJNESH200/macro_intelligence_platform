import type { ForecastPayload, Regime } from '@/lib/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { REGIMES, fixed, signed } from '@/lib/regime'

function convictionTone(conviction: number): string {
  if (conviction >= 65) return 'var(--delta-up)'
  if (conviction >= 45) return 'var(--regime-slowdown)'
  return 'var(--delta-down)'
}

export function ForecastPanel({ forecast }: { forecast: ForecastPayload | null }) {
  if (!forecast) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Forecast</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-xs text-ink-muted">Loading projection…</p>
        </CardContent>
      </Card>
    )
  }

  const horizons = Object.entries(forecast.forecasts)

  return (
    <Card>
      <CardHeader>
        <CardTitle>Forecast</CardTitle>
        <span className="inline-flex items-center gap-1.5 text-[10px] text-ink-muted">
          <svg width="14" height="4" aria-hidden>
            <line
              x1="0"
              y1="2"
              x2="14"
              y2="2"
              stroke="var(--viz-forecast)"
              strokeWidth="2"
              strokeDasharray="4 3"
            />
          </svg>
          Projected
        </span>
      </CardHeader>
      <CardContent className="space-y-3">
        {horizons.map(([horizon, f]) => (
          <div key={horizon} className="space-y-1">
            <div className="flex items-baseline justify-between gap-2">
              <span className="inline-flex items-center gap-1.5">
                <span className="tabular text-xs font-semibold text-ink">{horizon}</span>
                <span
                  aria-hidden
                  className="size-2 rounded-[2px]"
                  style={{ backgroundColor: REGIMES[f.quadrant]?.color }}
                />
                <span className="text-xs text-ink-secondary">{f.quadrant}</span>
              </span>
              <span className="tabular text-[11px] text-ink-muted">
                H {fixed(f.x)} · M {fixed(f.y)}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="h-1.5 flex-1 rounded-full bg-ink/[0.07]">
                <div
                  className="h-full rounded-full"
                  style={{
                    width: `${Math.max(0, Math.min(100, f.conviction))}%`,
                    backgroundColor: convictionTone(f.conviction),
                  }}
                />
              </div>
              <span className="tabular w-[68px] text-right text-[10.5px] text-ink-secondary">
                {fixed(f.conviction, 0)}% conv.
              </span>
            </div>
          </div>
        ))}

        {forecast.scenarios?.length ? (
          <div className="border-t border-hairline pt-2.5">
            <div className="text-[10px] font-medium uppercase tracking-[0.09em] text-ink-muted">
              Scenarios
            </div>
            <div className="mt-1.5 space-y-2">
              {forecast.scenarios.map((scenario) => {
                const quadrant = scenario.projected_quadrant_6m
                const swatch = quadrant in REGIMES ? REGIMES[quadrant as Regime].color : undefined
                return (
                  <div key={scenario.name} className="space-y-0.5">
                    <div className="flex items-baseline justify-between gap-2 text-[11px]">
                      <span className="inline-flex items-center gap-1.5">
                        <span className="font-medium text-ink">{scenario.name}</span>
                        {swatch ? (
                          <span
                            aria-hidden
                            className="size-2 rounded-[2px]"
                            style={{ backgroundColor: swatch }}
                          />
                        ) : null}
                        <span className="text-ink-secondary">{quadrant}</span>
                      </span>
                      <span className="tabular text-ink-muted">
                        {fixed(scenario.probability, 0)}%
                        {Number.isFinite(scenario.expected_market_return_6m as number)
                          ? ` · ${signed(scenario.expected_market_return_6m, 1)}%`
                          : ''}
                      </span>
                    </div>
                    <p className="text-[10.5px] leading-snug text-ink-muted">{scenario.trigger}</p>
                  </div>
                )
              })}
            </div>
          </div>
        ) : null}
      </CardContent>
    </Card>
  )
}
