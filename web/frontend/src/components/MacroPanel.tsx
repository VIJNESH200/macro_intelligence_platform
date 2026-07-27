import type { MacroDriver } from '@/lib/types'
import { TabbedCard, type PanelTab } from '@/components/TabbedCard'
import { signed } from '@/lib/regime'

const STATE_COLOR: Record<string, string> = {
  Positive: 'var(--delta-up)',
  Negative: 'var(--delta-down)',
  Neutral: 'var(--ink-muted)',
}

/** Z-scores are unbounded; clamp the bar to a readable +/-2.5 sigma. */
const BAR_LIMIT = 2.5

/**
 * One driver per line: name, a diverging bar about zero, and the signed score.
 *
 * The bar and the sign both encode direction, so the reading never rests on
 * colour alone -- which matters because these three states are the reserved
 * status hues.
 */
function DriverRow({ driver }: { driver: MacroDriver }) {
  const score = Number.isFinite(driver.score as number) ? (driver.score as number) : 0
  const magnitude = Math.min(Math.abs(score) / BAR_LIMIT, 1)
  const color = STATE_COLOR[driver.state] ?? 'var(--ink-muted)'

  return (
    <div className="flex items-center gap-2" title={`${driver.indicator}: ${driver.state}`}>
      <span className="w-[40%] shrink-0 truncate text-[11px] leading-tight text-ink">
        {driver.indicator}
      </span>
      <div className="relative h-1.5 min-w-0 flex-1 rounded-full bg-ink/[0.07]">
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
      <span className="tabular w-[36px] shrink-0 text-right text-[10.5px]" style={{ color }}>
        {signed(score)}
      </span>
    </div>
  )
}

export function MacroPanel({
  drivers,
  shifts,
  className,
}: {
  drivers: MacroDriver[]
  shifts: string[] | null
  className?: string
}) {
  const tabs: PanelTab[] = [
    {
      id: 'drivers',
      label: 'Z-score',
      content: drivers?.length ? (
        <div className="space-y-2">
          {drivers.map((driver) => (
            <DriverRow key={driver.indicator} driver={driver} />
          ))}
        </div>
      ) : (
        <p className="text-[11px] text-ink-muted">No driver data for this frame.</p>
      ),
    },
  ]

  if (shifts?.length) {
    tabs.push({
      id: 'shifts',
      label: 'Shifts',
      content: (
        <ul className="space-y-1.5">
          {shifts.map((shift, i) => (
            <li key={i} className="text-[11px] leading-snug text-ink-secondary">
              {shift}
            </li>
          ))}
        </ul>
      ),
    })
  }

  return <TabbedCard title="Macro Drivers" tabs={tabs} className={className} />
}
