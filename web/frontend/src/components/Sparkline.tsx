import * as React from 'react'
import { scaleLinear } from 'd3-scale'
import type { Frame } from '@/lib/types'
import { fixed } from '@/lib/regime'

const HEIGHT = 52

/** Raw indicator level over the full history, with the scrubbed point marked. */
export function Sparkline({
  frames,
  index,
  label,
}: {
  frames: Frame[]
  index: number
  label: string
}) {
  const wrapRef = React.useRef<HTMLDivElement>(null)
  const [width, setWidth] = React.useState(280)

  React.useEffect(() => {
    const node = wrapRef.current
    if (!node) return
    const observer = new ResizeObserver(([entry]) => {
      if (entry.contentRect.width > 0) setWidth(entry.contentRect.width)
    })
    observer.observe(node)
    return () => observer.disconnect()
  }, [])

  const points = React.useMemo(
    () => frames.filter((f) => f.raw !== null && Number.isFinite(f.raw)),
    [frames],
  )

  const { path, marker, current } = React.useMemo(() => {
    if (points.length < 2) return { path: '', marker: null, current: null }

    const values = points.map((p) => p.raw as number)
    const x = scaleLinear().domain([0, points.length - 1]).range([2, width - 2])
    const y = scaleLinear()
      .domain([Math.min(...values), Math.max(...values)])
      .range([HEIGHT - 6, 6])

    const d = points
      .map((p, i) => `${i === 0 ? 'M' : 'L'}${x(i).toFixed(2)},${y(p.raw as number).toFixed(2)}`)
      .join('')

    const currentFrame = frames[Math.min(index, frames.length - 1)]
    const pos = points.findIndex((p) => p.i >= currentFrame.i)
    const at = pos < 0 ? points.length - 1 : pos

    return {
      path: d,
      marker: { cx: x(at), cy: y(points[at].raw as number) },
      current: currentFrame,
    }
  }, [points, frames, index, width])

  return (
    <div ref={wrapRef} className="w-full">
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-[10px] font-medium uppercase tracking-[0.09em] text-ink-muted">
          {label}
        </span>
        <span className="tabular text-[11px] text-ink-secondary">{fixed(current?.raw)}</span>
      </div>
      <svg width={width} height={HEIGHT} className="mt-1" aria-hidden>
        <path d={path} fill="none" stroke="var(--viz-history)" strokeWidth={1.5} strokeOpacity={0.55} />
        {marker ? (
          <circle
            cx={marker.cx}
            cy={marker.cy}
            r={3.5}
            fill="var(--viz-point)"
            stroke="var(--surface)"
            strokeWidth={1.5}
          />
        ) : null}
      </svg>
    </div>
  )
}
