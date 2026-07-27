import type { FramePayload, ForecastPayload, Regime } from '@/lib/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { REGIMES, REGIME_ORDER, fixed } from '@/lib/regime'

function str(value: unknown, fallback = '—'): string {
  return value === null || value === undefined || value === '' ? fallback : String(value)
}

export function PhasePanel({
  frame,
  forecast,
}: {
  frame: FramePayload
  forecast: ForecastPayload | null
}) {
  const analysis = frame.analysis ?? {}
  const completion = Number(analysis.completion_pct)
  const transitions = forecast?.transitions
  const labels = (transitions?.labels ?? REGIME_ORDER) as Regime[]
  const rowIndex = labels.indexOf(frame.quadrant)
  const row = rowIndex >= 0 ? transitions?.matrix?.[rowIndex] : undefined

  const rows: Array<[string, string]> = [
    ['Entered', str(frame.phase?.entered_label)],
    ['Duration', str(analysis.current_duration, `${frame.phase?.duration_months ?? '—'} months`)],
    ['Historical avg', str(analysis.avg_duration)],
    ['Range', `${str(analysis.shortest_duration)} – ${str(analysis.longest_duration)}`],
    ['Occurrences', str(analysis.occurrences)],
    ['Previous phase', str(frame.phase?.previous_quadrant)],
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle>Phase Statistics</CardTitle>
        <span className="inline-flex items-center gap-1.5 text-[10px] text-ink-muted">
          <span
            aria-hidden
            className="size-2 rounded-[2px]"
            style={{ backgroundColor: REGIMES[frame.quadrant]?.color }}
          />
          {frame.quadrant}
        </span>
      </CardHeader>
      <CardContent className="space-y-3">
        <dl className="space-y-1">
          {rows.map(([label, value]) => (
            <div key={label} className="flex items-baseline justify-between gap-3 text-[11.5px]">
              <dt className="text-ink-muted">{label}</dt>
              <dd className="tabular text-ink">{value}</dd>
            </div>
          ))}
        </dl>

        {Number.isFinite(completion) ? (
          <div className="space-y-1">
            <div className="flex items-baseline justify-between text-[10px] uppercase tracking-[0.09em] text-ink-muted">
              <span>Phase maturity</span>
              <span className="tabular">{fixed(completion, 0)}%</span>
            </div>
            <div className="h-1.5 w-full rounded-full bg-ink/[0.07]">
              <div
                className="h-full rounded-full bg-viz-history"
                style={{ width: `${Math.max(0, Math.min(100, completion))}%` }}
              />
            </div>
          </div>
        ) : null}

        {row ? (
          <div className="border-t border-hairline pt-2.5">
            <div className="text-[10px] font-medium uppercase tracking-[0.09em] text-ink-muted">
              Next-month transition
            </div>
            <div className="mt-1.5 space-y-1.5">
              {labels.map((label, i) => {
                const probability = (row[i] ?? 0) * 100
                return (
                  <div key={label} className="flex items-center gap-2">
                    <span
                      aria-hidden
                      className="size-2 shrink-0 rounded-[2px]"
                      style={{ backgroundColor: REGIMES[label]?.color }}
                    />
                    <span className="w-[86px] shrink-0 text-[11px] text-ink-secondary">{label}</span>
                    <div className="h-1.5 flex-1 rounded-full bg-ink/[0.07]">
                      <div
                        className="h-full rounded-full bg-viz-history"
                        style={{ width: `${probability.toFixed(1)}%` }}
                      />
                    </div>
                    <span className="tabular w-[38px] text-right text-[10.5px] text-ink-muted">
                      {fixed(probability, 0)}%
                    </span>
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
