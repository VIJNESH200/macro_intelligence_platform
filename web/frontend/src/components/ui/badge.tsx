import * as React from 'react'
import { cn } from '@/lib/utils'

/**
 * A label with an optional leading swatch.
 *
 * Regime identity is never carried by color alone -- the swatch is decorative
 * reinforcement beside the always-present text, which wears ink tokens.
 */
export function Badge({
  className,
  swatch,
  children,
  ...props
}: React.ComponentProps<'span'> & { swatch?: string }) {
  return (
    <span
      data-slot="badge"
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border border-hairline px-2 py-0.5 text-xs font-medium text-ink',
        className,
      )}
      {...props}
    >
      {swatch ? (
        <span
          aria-hidden
          className="size-2 rounded-[2px]"
          style={{ backgroundColor: swatch }}
        />
      ) : null}
      {children}
    </span>
  )
}
