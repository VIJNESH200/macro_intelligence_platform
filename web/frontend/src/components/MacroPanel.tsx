import type { MacroDriver } from '@/lib/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { fixed } from '@/lib/regime'

const STATE_COLOR: Record<string, string> = {
  Positive: 'var(--delta-up)',
  Negative: 'var(--delta-down)',
  Neutral: 'var(--ink-muted)',
}

/** Z-scores are unbounded; clamp the bar to a readable +/-2.5 sigma. */
const BAR_LIMIT = 2.5

export function MacroPanel({
  drivers,
  shifts,
}: {
  drivers: MacroDriver[]
  shifts: string[] | null
}) {
  if (!drivers?.length) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Macro Drivers</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-xs text-ink-muted">No driver data for this frame.</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Macro Drivers</CardTitle>
        <span className="text-[10px] text-ink-muted">Z-score</span>
      </CardHeader>
      <CardContent className="space-y-2">
        {drivers.map((driver) => {
          const score = Number.isFinite(driver.score as number) ? (driver.score as number) : 0
          const magnitude = Math.min(Math.abs(score) / BAR_LIMIT, 1)
          const color = STATE_COLOR[driver.state] ?? 'var(--ink-muted)'
          return (
            <div key={driver.indicator} className="space-y-1">
              <div className="flex items-baseline justify-between gap-2">
                <span className="text-xs text-ink">{driver.indicator}</span>
                <span className="tabular text-xs" style={{ color }}>
                  {driver.state} {fixed(driver.score, 2)}
                </span>
              </div>
              {/* Diverging bar about a neutral zero line. */}
              <div className="relative h-1.5 w-full rounded-full bg-ink/[0.07]">
                <div className="absolute left-1/2 top-0 h-full w-px bg-baseline" />
                <div
                  className="absolute top-0 h-full rounded-full"
                  style={{
                    backgroundColor: color,
                    width: `${(magnitude * 50).toFixed(1)}%`,
                    left: score >= 0 ? '50%' : undefined,
                    right: score < 0 ? '50%' : undefined,
                  }}
                />
              </div>
            </div>
          )
        })}

        {shifts?.length ? (
          <div className="mt-3 border-t border-hairline pt-2.5">
            <div className="text-[10px] font-medium uppercase tracking-[0.09em] text-ink-muted">
              Regime Shifts
            </div>
            <ul className="mt-1.5 space-y-1">
              {shifts.map((shift, i) => (
                <li key={i} className="text-[11px] leading-snug text-ink-secondary">
                  {shift}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </CardContent>
    </Card>
  )
}
