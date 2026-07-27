import * as React from 'react'
import { cn } from '@/lib/utils'

/**
 * A labelled figure. Values use default proportional figures; `tabular` is
 * reserved for columns that must align vertically.
 */
export function StatTile({
  label,
  value,
  hint,
  accent,
  className,
}: {
  label: string
  value: React.ReactNode
  hint?: React.ReactNode
  accent?: string
  className?: string
}) {
  return (
    <div className={cn('flex flex-col gap-0.5', className)}>
      <div className="flex items-center gap-1.5">
        {accent ? (
          <span aria-hidden className="size-2 rounded-[2px]" style={{ backgroundColor: accent }} />
        ) : null}
        <span className="text-[10px] font-medium uppercase tracking-[0.09em] text-ink-muted">
          {label}
        </span>
      </div>
      <span className="text-[22px] leading-tight font-semibold text-ink">{value}</span>
      {hint ? <span className="text-[11px] text-ink-secondary">{hint}</span> : null}
    </div>
  )
}
