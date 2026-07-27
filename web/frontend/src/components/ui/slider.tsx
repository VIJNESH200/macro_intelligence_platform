import * as React from 'react'
import * as SliderPrimitive from '@radix-ui/react-slider'
import { cn } from '@/lib/utils'

export function Slider({ className, ...props }: React.ComponentProps<typeof SliderPrimitive.Root>) {
  return (
    <SliderPrimitive.Root
      data-slot="slider"
      className={cn('relative flex w-full touch-none items-center select-none', className)}
      {...props}
    >
      <SliderPrimitive.Track className="relative h-1.5 w-full grow overflow-hidden rounded-full bg-ink/10">
        <SliderPrimitive.Range className="absolute h-full bg-viz-history" />
      </SliderPrimitive.Track>
      <SliderPrimitive.Thumb className="block size-4 shrink-0 rounded-full border-2 border-viz-history bg-surface shadow-sm transition-[box-shadow] outline-none hover:ring-4 hover:ring-viz-history/20 focus-visible:ring-4 focus-visible:ring-viz-history/40" />
    </SliderPrimitive.Root>
  )
}
