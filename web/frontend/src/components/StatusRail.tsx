import { ArrowDown, ArrowRight, ArrowUp } from 'lucide-react'
import type { ForecastPayload, Frame, FramePayload } from '@/lib/types'
import { Card, CardContent } from '@/components/ui/card'
import { REGIMES, describeDirection, fixed, signed } from '@/lib/regime'

/**
 * Dense vertical readout of the current frame.
 *
 * Replaces a full-width tile strip: the same figures cost a fraction of the
 * space here, which buys the chart the room it actually needs. Every metric is
 * one row -- label, figure, and a mark showing where it sits relative to the
 * centre line -- so the eye scans a single column instead of a wide grid.
 */

/** Deviation is unbounded in principle; +/-3 sigma covers the readable range. */
const DEVIATION_LIMIT = 3

function DirectionIcon({ delta }: { delta: number }) {
  if (!Number.isFinite(delta) || Math.abs(delta) < 0.005) {
    return <ArrowRight className="size-3 shrink-0" style={{ color: 'var(--ink-muted)' }} />
  }
  const Icon = delta > 0 ? ArrowUp : ArrowDown
  return (
    <Icon
      className="size-3 shrink-0"
      style={{ color: delta > 0 ? 'var(--delta-up)' : 'var(--delta-down)' }}
    />
  )
}

/** A figure with a diverging bar showing its distance from the centre line. */
function Metric({
  label,
  value,
  deviation,
}: {
  label: string
  value: number | null | undefined
  deviation: number
}) {
  const magnitude = Math.min(Math.abs(deviation) / DEVIATION_LIMIT, 1)
  const color = deviation >= 0 ? 'var(--delta-up)' : 'var(--delta-down)'

  return (
    <div className="space-y-1">
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-[10px] font-medium uppercase tracking-[0.08em] text-ink-muted">
          {label}
        </span>
        <span className="tabular text-[15px] font-semibold leading-none text-ink">
          {fixed(value)}
        </span>
      </div>
      <div className="relative h-1 w-full rounded-full bg-ink/[0.08]">
        <div className="absolute left-1/2 top-[-2px] h-[5px] w-px bg-baseline" />
        <div
          className="absolute top-0 h-full rounded-full"
          style={{
            backgroundColor: color,
            width: `${(magnitude * 50).toFixed(1)}%`,
            left: deviation >= 0 ? '50%' : undefined,
            right: deviation < 0 ? '50%' : undefined,
          }}
        />
      </div>
      <div className="flex items-center gap-1">
        <DirectionIcon delta={deviation} />
        <span className="tabular text-[10.5px] text-ink-secondary">
          {signed(deviation)} vs centre
        </span>
      </div>
    </div>
  )
}

/** Conviction as a ring — reads as a gauge at a glance and costs one line. */
function ConvictionRing({ value }: { value: number }) {
  const radius = 15
  const circumference = 2 * Math.PI * radius
  const pct = Math.max(0, Math.min(100, value))
  const tone =
    pct >= 65 ? 'var(--delta-up)' : pct >= 45 ? 'var(--regime-slowdown)' : 'var(--delta-down)'

  return (
    <svg width="38" height="38" viewBox="0 0 38 38" className="shrink-0" aria-hidden>
      <circle cx="19" cy="19" r={radius} fill="none" stroke="var(--gridline)" strokeWidth="4" />
      <circle
        cx="19"
        cy="19"
        r={radius}
        fill="none"
        stroke={tone}
        strokeWidth="4"
        strokeLinecap="round"
        strokeDasharray={`${(circumference * pct) / 100} ${circumference}`}
        transform="rotate(-90 19 19)"
      />
      <text
        x="19"
        y="22.5"
        textAnchor="middle"
        className="tabular fill-ink text-[10px] font-semibold"
      >
        {Math.round(pct)}
      </text>
    </svg>
  )
}

function Divider() {
  return <div className="my-3 h-px w-full bg-hairline" />
}

export function StatusRail({
  frame,
  forecast,
  current,
  previous,
  totalFrames,
  center,
}: {
  frame: FramePayload | null
  forecast: ForecastPayload | null
  current: Frame
  previous: Frame | null
  totalFrames: number
  center: number
}) {
  const regime = frame?.quadrant ?? current.quadrant
  const meta = REGIMES[regime]
  const headline = forecast?.forecasts?.['6m']
  const progress = totalFrames > 1 ? ((current.i + 1) / totalFrames) * 100 : 100

  // Distance from the centre line -- where the economy stands.
  const healthDeviation = current.x - center
  const momentumDeviation = current.y - center

  // Change since last month -- which way it is moving. Different question.
  const healthChange = previous ? current.x - previous.x : 0
  const momentumChange = previous ? current.y - previous.y : 0

  return (
    <Card>
      <CardContent className="px-4 py-3.5">
        {/* Regime */}
        <div className="flex items-center gap-2">
          <span
            aria-hidden
            className="size-2.5 shrink-0 rounded-[3px]"
            style={{ backgroundColor: meta?.color }}
          />
          <span className="text-[17px] font-semibold leading-none text-ink">{regime}</span>
        </div>
        <p className="mt-1 text-[11px] leading-snug text-ink-secondary">{meta?.blurb}</p>

        <Divider />

        {/* Position in history */}
        <div className="flex items-baseline justify-between gap-2">
          <span className="text-[13px] font-medium text-ink">{current.label}</span>
          <span className="tabular text-[10.5px] text-ink-muted">
            {current.i + 1} / {totalFrames}
          </span>
        </div>
        <div className="mt-1.5 h-1 w-full rounded-full bg-ink/[0.08]">
          <div
            className="h-full rounded-full bg-viz-history"
            style={{ width: `${progress.toFixed(1)}%` }}
          />
        </div>

        <Divider />

        <div className="space-y-3">
          <Metric label="Health" value={current.x} deviation={healthDeviation} />
          <Metric label="Momentum" value={current.y} deviation={momentumDeviation} />
        </div>

        <Divider />

        {/* Trajectory: month-over-month change, which is a different question
            from the deviation bars above -- where it stands vs where it is going. */}
        <div className="flex items-baseline justify-between">
          <span className="text-[10px] font-medium uppercase tracking-[0.08em] text-ink-muted">
            Trajectory
          </span>
          <span className="text-[10px] text-ink-muted">1M Δ</span>
        </div>
        <div className="mt-1.5 space-y-1">
          {([
            ['Health', healthChange],
            ['Momentum', momentumChange],
          ] as const).map(([label, change]) => (
            <div key={label} className="flex items-center gap-1.5">
              <DirectionIcon delta={change} />
              <span className="text-[11.5px] text-ink-secondary">{label}</span>
              <span className="tabular ml-auto text-[11px] text-ink-muted">{signed(change)}</span>
            </div>
          ))}
        </div>
        {frame?.direction ? (
          <p className="mt-1.5 text-[10.5px] leading-snug text-ink-muted">
            {describeDirection(frame.direction).long}
          </p>
        ) : null}

        <Divider />

        {/* 6-month outlook */}
        <div className="flex items-center gap-2.5">
          <ConvictionRing value={headline?.conviction ?? 0} />
          <div className="min-w-0">
            <div className="text-[10px] font-medium uppercase tracking-[0.08em] text-ink-muted">
              6M Outlook
            </div>
            <div className="mt-0.5 flex items-center gap-1.5">
              {headline ? (
                <span
                  aria-hidden
                  className="size-2 shrink-0 rounded-[2px]"
                  style={{ backgroundColor: REGIMES[headline.quadrant]?.color }}
                />
              ) : null}
              <span className="truncate text-[12.5px] font-medium text-ink">
                {headline?.quadrant ?? '—'}
              </span>
            </div>
            <div className="text-[10.5px] text-ink-muted">conviction</div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
