import * as React from 'react'
import { scaleLinear } from 'd3-scale'
import type { Bounds, Frame, ForecastPayload, SplinePoint } from '@/lib/types'
import { REGIME_CORNERS, REGIME_ORDER, REGIMES, fixed } from '@/lib/regime'
import { cn } from '@/lib/utils'

const MARGIN = { top: 18, right: 20, bottom: 46, left: 56 }

/** Opacity ramp along the trail: one hue, oldest faint -> newest solid. */
const TRAIL_MIN_OPACITY = 0.16
const TRAIL_MAX_OPACITY = 1

/** Minimum pixel separation before two horizon labels are treated as colliding. */
const LABEL_MIN_GAP = 22

interface Props {
  frames: Frame[]
  spline: SplinePoint[]
  bounds: Bounds
  pointsPerSegment: number
  index: number
  tailLength: number
  forecast: ForecastPayload | null
  showTrail: boolean
  showFullHistory: boolean
  showForecast: boolean
  showLabel: boolean
  windowMonths: number
  onScrub?: (index: number) => void
  className?: string
}

interface HoverState {
  frame: Frame
  px: number
  py: number
}

export function QuadrantChart({
  frames,
  spline,
  bounds,
  pointsPerSegment,
  index,
  tailLength,
  forecast,
  showTrail,
  showFullHistory,
  showForecast,
  showLabel,
  windowMonths,
  onScrub,
  className,
}: Props) {
  const wrapRef = React.useRef<HTMLDivElement>(null)
  const [size, setSize] = React.useState({ width: 720, height: 560 })
  const [hover, setHover] = React.useState<HoverState | null>(null)

  React.useEffect(() => {
    const node = wrapRef.current
    if (!node) return
    const observer = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect
      if (width > 0 && height > 0) setSize({ width, height })
    })
    observer.observe(node)
    return () => observer.disconnect()
  }, [])

  const { width, height } = size

  const plotW = Math.max(10, width - MARGIN.left - MARGIN.right)
  const plotH = Math.max(10, height - MARGIN.top - MARGIN.bottom)
  const offsetX = MARGIN.left

  // A unit must measure the same on both axes, or the reported distance-from-
  // centre and trajectory stop being true. Rather than letterbox a square plot
  // and waste the container, hold the scale equal and let the longer axis show
  // more range: the shorter one covers exactly +/- extent, the longer covers
  // proportionally more. The centre stays centred either way.
  const unitsPerPixel = (2 * bounds.extent) / Math.min(plotW, plotH)
  const halfX = (plotW * unitsPerPixel) / 2
  const halfY = (plotH * unitsPerPixel) / 2

  const x = React.useMemo(
    () => scaleLinear().domain([bounds.center - halfX, bounds.center + halfX]).range([0, plotW]),
    [bounds.center, halfX, plotW],
  )
  const y = React.useMemo(
    () => scaleLinear().domain([bounds.center - halfY, bounds.center + halfY]).range([plotH, 0]),
    [bounds.center, halfY, plotH],
  )

  const cx = x(bounds.center)
  const cy = y(bounds.center)
  const current = frames[Math.min(index, frames.length - 1)]

  // The server already fit a cubic B-spline; walking it keeps the web trail
  // geometrically identical to the desktop chart rather than re-smoothing here.
  const trailPoints = React.useMemo(() => {
    if (!spline.length) return []
    const end = Math.min(index * pointsPerSegment, spline.length - 1)
    const startFrame = showFullHistory ? 0 : Math.max(0, index - tailLength + 1)
    const start = Math.min(startFrame * pointsPerSegment, end)
    return spline.slice(start, end + 1)
  }, [spline, index, pointsPerSegment, tailLength, showFullHistory])

  const historyPath = React.useMemo(() => {
    if (!showFullHistory || !spline.length) return ''
    const end = Math.min(index * pointsPerSegment, spline.length - 1)
    return spline
      .slice(0, end + 1)
      .map((p, i) => `${i === 0 ? 'M' : 'L'}${x(p.x).toFixed(2)},${y(p.y).toFixed(2)}`)
      .join('')
  }, [spline, index, pointsPerSegment, showFullHistory, x, y])

  const forecastPath = React.useMemo(() => {
    const path = forecast?.projected_path ?? []
    if (path.length < 2) return ''
    return path
      .map((p, i) => `${i === 0 ? 'M' : 'L'}${x(p[0]).toFixed(2)},${y(p[1]).toFixed(2)}`)
      .join('')
  }, [forecast, x, y])

  // Separate tick sets: the axes now cover different ranges at the same scale.
  const xTicks = React.useMemo(
    () => x.ticks(Math.max(3, Math.round((plotW / 130)))),
    [x, plotW],
  )
  const yTicks = React.useMemo(
    () => y.ticks(Math.max(3, Math.round((plotH / 90)))),
    [y, plotH],
  )

  /**
   * Horizon markers, with labels dropped where they would collide. When the
   * projection is tight the 3m/6m/9m points bunch into a few pixels, and three
   * stacked labels are less readable than one -- the forecast panel carries the
   * full set of values regardless.
   */
  const horizonMarkers = React.useMemo(() => {
    const entries = Object.entries(forecast?.forecasts ?? {})
    const placed: Array<{ px: number; py: number }> = []

    return entries.map(([horizon, f]) => {
      const px = x(f.x)
      const py = y(f.y)
      const collides = placed.some(
        (p) => Math.abs(p.px - px) < LABEL_MIN_GAP && Math.abs(p.py - py) < LABEL_MIN_GAP,
      )
      if (!collides) placed.push({ px, py })
      return { horizon, px, py, label: !collides }
    })
  }, [forecast, x, y])

  const handleMove = (event: React.MouseEvent<SVGRectElement>) => {
    const rect = event.currentTarget.getBoundingClientRect()
    const px = event.clientX - rect.left
    const py = event.clientY - rect.top
    const dataX = x.invert(px)
    const dataY = y.invert(py)

    // Nearest visible frame, so the tooltip can never describe a hidden point.
    const from = showFullHistory ? 0 : Math.max(0, index - tailLength + 1)
    let best: Frame | null = null
    let bestDist = Infinity
    for (let i = from; i <= index; i += 1) {
      const f = frames[i]
      const d = (f.x - dataX) ** 2 + (f.y - dataY) ** 2
      if (d < bestDist) {
        bestDist = d
        best = f
      }
    }
    if (best) setHover({ frame: best, px: x(best.x), py: y(best.y) })
  }

  if (!current) return null

  return (
    <div ref={wrapRef} className={cn('relative h-full w-full', className)}>
      <svg width={width} height={height} role="img" aria-label="Business cycle quadrant chart">
        <title>
          {`Economic health vs momentum, ${current.label}. Current regime: ${current.quadrant}.`}
        </title>

        <g transform={`translate(${offsetX},${MARGIN.top})`}>
          {/* Quadrant territory: low-alpha washes, never the sole cue for regime. */}
          <rect x={cx} y={0} width={plotW - cx} height={cy} fill="var(--regime-expansion)" opacity={0.06} />
          <rect x={cx} y={cy} width={plotW - cx} height={plotH - cy} fill="var(--regime-slowdown)" opacity={0.06} />
          <rect x={0} y={cy} width={cx} height={plotH - cy} fill="var(--regime-contraction)" opacity={0.06} />
          <rect x={0} y={0} width={cx} height={cy} fill="var(--regime-recovery)" opacity={0.06} />

          {/* Recessive grid */}
          <g stroke="var(--gridline)" strokeWidth={1}>
            {xTicks.map((t) => (
              <line key={`gx-${t}`} x1={x(t)} y1={0} x2={x(t)} y2={plotH} />
            ))}
            {yTicks.map((t) => (
              <line key={`gy-${t}`} x1={0} y1={y(t)} x2={plotW} y2={y(t)} />
            ))}
          </g>

          {/* Centre crosshair -- the regime boundary */}
          <g stroke="var(--baseline)" strokeWidth={1} strokeDasharray="4 4">
            <line x1={0} y1={cy} x2={plotW} y2={cy} />
            <line x1={cx} y1={0} x2={cx} y2={plotH} />
          </g>

          {REGIME_ORDER.map((regime) => {
            const corner = REGIME_CORNERS[regime]
            const tx = corner.fx * plotW
            const ty = corner.fy * plotH
            const swatchOffset = corner.anchor === 'end' ? 6 : -6
            return (
              <g key={regime}>
                <rect
                  x={corner.anchor === 'end' ? tx + swatchOffset : tx + swatchOffset - 1}
                  y={ty - 8}
                  width={7}
                  height={7}
                  rx={1.5}
                  fill={REGIMES[regime].color}
                />
                <text
                  x={corner.anchor === 'end' ? tx : tx + 11}
                  y={ty}
                  textAnchor={corner.anchor === 'end' ? 'end' : 'start'}
                  className="fill-ink-secondary text-[10.5px] font-semibold uppercase tracking-[0.09em]"
                >
                  {REGIMES[regime].label}
                </text>
              </g>
            )
          })}

          {/* Ghost of the full path, when enabled */}
          {showFullHistory && historyPath ? (
            <path
              d={historyPath}
              fill="none"
              stroke="var(--viz-history)"
              strokeOpacity={0.18}
              strokeWidth={1.25}
              strokeLinecap="round"
            />
          ) : null}

          {/* Emphasised trail: one hue, oldest faint -> newest solid */}
          {showTrail
            ? trailPoints.slice(0, -1).map((p, i) => {
                const next = trailPoints[i + 1]
                const t = trailPoints.length > 1 ? i / (trailPoints.length - 1) : 1
                return (
                  <line
                    key={`trail-${i}`}
                    x1={x(p.x)}
                    y1={y(p.y)}
                    x2={x(next.x)}
                    y2={y(next.y)}
                    stroke="var(--viz-history)"
                    strokeOpacity={TRAIL_MIN_OPACITY + t * (TRAIL_MAX_OPACITY - TRAIL_MIN_OPACITY)}
                    strokeWidth={2}
                    strokeLinecap="round"
                  />
                )
              })
            : null}

          {/* Forecast: distinct hue, dashed to read as "not observed" */}
          {showForecast && forecast ? (
            <g>
              {/* Each horizon's uncertainty is an ellipse, and the band is their
                  union. Opacity lives on the group so overlapping ellipses
                  composite once -- per-ellipse alpha would stack into a lumpy
                  blob where the path doubles back. */}
              <g opacity={0.1}>
                {(forecast.confidence_band.outer ?? []).map((band, i) => (
                  <ellipse
                    key={`outer-${i}`}
                    cx={x(band.x)}
                    cy={y(band.y)}
                    rx={Math.abs(x(band.x + band.dx) - x(band.x))}
                    ry={Math.abs(y(band.y + band.dy) - y(band.y))}
                    fill="var(--viz-forecast)"
                  />
                ))}
              </g>
              <g opacity={0.14}>
                {(forecast.confidence_band.inner ?? []).map((band, i) => (
                  <ellipse
                    key={`inner-${i}`}
                    cx={x(band.x)}
                    cy={y(band.y)}
                    rx={Math.abs(x(band.x + band.dx) - x(band.x))}
                    ry={Math.abs(y(band.y + band.dy) - y(band.y))}
                    fill="var(--viz-forecast)"
                  />
                ))}
              </g>
              {forecastPath ? (
                <path
                  d={forecastPath}
                  fill="none"
                  stroke="var(--viz-forecast)"
                  strokeWidth={2}
                  strokeDasharray="5 4"
                  strokeLinecap="round"
                />
              ) : null}
              {horizonMarkers.map(({ horizon, px, py, label }) => (
                <g key={horizon}>
                  <circle
                    cx={px}
                    cy={py}
                    r={4.5}
                    fill="var(--viz-forecast)"
                    stroke="var(--surface)"
                    strokeWidth={2}
                  />
                  {label ? (
                    <text
                      x={px}
                      y={py - 10}
                      textAnchor="middle"
                      className="fill-ink-secondary tabular text-[10px] font-medium"
                    >
                      {horizon}
                    </text>
                  ) : null}
                </g>
              ))}
            </g>
          ) : null}

          {/* Hovered point marker */}
          {hover ? (
            <circle
              cx={hover.px}
              cy={hover.py}
              r={5}
              fill="none"
              stroke="var(--viz-history)"
              strokeWidth={2}
            />
          ) : null}

          {/* Current position: ink, not regime-coloured. Position already says
              which quadrant it sits in, and this keeps it legible against every
              wash while staying clear of the forecast hue. */}
          <circle
            cx={x(current.x)}
            cy={y(current.y)}
            r={7}
            fill="var(--viz-point)"
            stroke="var(--surface)"
            strokeWidth={2.5}
          />
          {showLabel ? (
            <text
              x={x(current.x) + 12}
              y={y(current.y) + 4}
              className="fill-ink text-[11px] font-semibold"
            >
              {current.label}
            </text>
          ) : null}

          {/* Axes */}
          <g stroke="var(--baseline)" strokeWidth={1}>
            <line x1={0} y1={plotH} x2={plotW} y2={plotH} />
            <line x1={0} y1={0} x2={0} y2={plotH} />
          </g>
          <g className="fill-ink-muted tabular text-[10px]">
            {xTicks.map((t) => (
              <text key={`tx-${t}`} x={x(t)} y={plotH + 15} textAnchor="middle">
                {t.toFixed(1)}
              </text>
            ))}
            {yTicks.map((t) => (
              <text key={`ty-${t}`} x={-8} y={y(t) + 3.5} textAnchor="end">
                {t.toFixed(1)}
              </text>
            ))}
          </g>

          <rect
            x={0}
            y={0}
            width={plotW}
            height={plotH}
            fill="transparent"
            onMouseMove={handleMove}
            onMouseLeave={() => setHover(null)}
            onClick={() => hover && onScrub?.(hover.frame.i)}
            style={{ cursor: onScrub ? 'crosshair' : 'default' }}
          />
        </g>

        <text
          x={offsetX + plotW / 2}
          y={height - 6}
          textAnchor="middle"
          className="fill-ink-secondary text-[11px]"
        >
          {`Economic Health (${windowMonths}M Z-Score)`}
        </text>
        <text
          transform={`translate(${Math.max(13, offsetX - 42)},${MARGIN.top + plotH / 2}) rotate(-90)`}
          textAnchor="middle"
          className="fill-ink-secondary text-[11px]"
        >
          {`Economic Momentum (1M Δ → ${windowMonths}M Z-Score)`}
        </text>
      </svg>

      {hover ? (
        <div
          className="pointer-events-none absolute z-20 min-w-[152px] rounded-md border border-hairline bg-surface-raised px-2.5 py-2 shadow-lg"
          style={{
            left: Math.min(hover.px + offsetX + 14, width - 170),
            top: Math.max(hover.py + MARGIN.top - 52, 4),
          }}
        >
          <div className="text-[11px] font-semibold text-ink">{hover.frame.label}</div>
          <div className="mt-1 flex items-center gap-1.5">
            <span
              aria-hidden
              className="size-2 rounded-[2px]"
              style={{ backgroundColor: REGIMES[hover.frame.quadrant].color }}
            />
            <span className="text-[11px] text-ink-secondary">{hover.frame.quadrant}</span>
          </div>
          <dl className="mt-1.5 space-y-0.5 text-[10.5px] text-ink-muted">
            <div className="flex justify-between gap-3">
              <dt>Health</dt>
              <dd className="tabular text-ink-secondary">{fixed(hover.frame.x)}</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt>Momentum</dt>
              <dd className="tabular text-ink-secondary">{fixed(hover.frame.y)}</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt>Indicator</dt>
              <dd className="tabular text-ink-secondary">{fixed(hover.frame.raw)}</dd>
            </div>
          </dl>
        </div>
      ) : null}

      {/* Legend is always present for the two mark series. */}
      <div className="pointer-events-none absolute right-4 top-0 flex items-center gap-3 text-[10.5px] text-ink-secondary">
        <span className="inline-flex items-center gap-1.5">
          <svg width="16" height="4" aria-hidden>
            <line x1="0" y1="2" x2="16" y2="2" stroke="var(--viz-history)" strokeWidth="2" />
          </svg>
          History
        </span>
        {showForecast ? (
          <span className="inline-flex items-center gap-1.5">
            <svg width="16" height="4" aria-hidden>
              <line
                x1="0"
                y1="2"
                x2="16"
                y2="2"
                stroke="var(--viz-forecast)"
                strokeWidth="2"
                strokeDasharray="4 3"
              />
            </svg>
            Forecast
          </span>
        ) : null}
      </div>
    </div>
  )
}
