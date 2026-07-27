import type { FramePayload, ForecastPayload, Regime } from '@/lib/types'
import { TabbedCard, type PanelTab } from '@/components/TabbedCard'
import { REGIMES, REGIME_ORDER, fixed } from '@/lib/regime'

function str(value: unknown, fallback = '—'): string {
  return value === null || value === undefined || value === '' ? fallback : String(value)
}

export function PhasePanel({
  frame,
  forecast,
  className,
}: {
  frame: FramePayload
  forecast: ForecastPayload | null
  className?: string
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

  const tabs: PanelTab[] = [
    {
      id: 'cycle',
      label: 'Cycle',
      content: (
        <div className="space-y-2.5">
          {Number.isFinite(completion) ? (
            <div className="space-y-1">
              <div className="flex items-baseline justify-between text-[10px] uppercase tracking-[0.08em] text-ink-muted">
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
            <div className="space-y-1.5">
              <div className="text-[10px] uppercase tracking-[0.08em] text-ink-muted">
                Next-month transition
              </div>
              {labels.map((label, i) => {
                const probability = (row[i] ?? 0) * 100
                return (
                  <div key={label} className="flex items-center gap-1.5">
                    <span
                      aria-hidden
                      className="size-2 shrink-0 rounded-[2px]"
                      style={{ backgroundColor: REGIMES[label]?.color }}
                    />
                    <span className="w-[70px] shrink-0 truncate text-[10.5px] text-ink-secondary">
                      {label}
                    </span>
                    <div className="h-1.5 min-w-0 flex-1 rounded-full bg-ink/[0.07]">
                      <div
                        className="h-full rounded-full bg-viz-history"
                        style={{ width: `${probability.toFixed(1)}%` }}
                      />
                    </div>
                    <span className="tabular w-[30px] shrink-0 text-right text-[10px] text-ink-muted">
                      {fixed(probability, 0)}%
                    </span>
                  </div>
                )
              })}
            </div>
          ) : null}
        </div>
      ),
    },
    {
      id: 'detail',
      label: 'Detail',
      content: (
        <dl className="space-y-1">
          {rows.map(([label, value]) => (
            <div key={label} className="flex items-baseline justify-between gap-3 text-[11px]">
              <dt className="shrink-0 text-ink-muted">{label}</dt>
              <dd className="tabular truncate text-ink">{value}</dd>
            </div>
          ))}
        </dl>
      ),
    },
  ]

  return <TabbedCard title="Phase Statistics" tabs={tabs} className={className} />
}
