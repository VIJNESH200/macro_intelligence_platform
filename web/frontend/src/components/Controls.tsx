import { ChevronLast, Pause, Play, SkipBack, SkipForward, RotateCcw } from 'lucide-react'
import type { Frame } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { Slider } from '@/components/ui/slider'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'

export interface DisplayOptions {
  trail: boolean
  fullHistory: boolean
  forecast: boolean
  label: boolean
}

const SPEEDS = [1, 2, 3] as const

export function Controls({
  frames,
  index,
  playing,
  speed,
  options,
  onIndexChange,
  onTogglePlay,
  onRestart,
  onJumpToLatest,
  onSpeedChange,
  onOptionsChange,
}: {
  frames: Frame[]
  index: number
  playing: boolean
  speed: number
  options: DisplayOptions
  onIndexChange: (index: number) => void
  onTogglePlay: () => void
  onRestart: () => void
  onJumpToLatest: () => void
  onSpeedChange: (speed: number) => void
  onOptionsChange: (options: DisplayOptions) => void
}) {
  const last = Math.max(0, frames.length - 1)
  const current = frames[Math.min(index, last)]
  const step = (delta: number) => onIndexChange(Math.max(0, Math.min(last, index + delta)))
  const atEnd = index >= last

  const toggles: Array<[keyof DisplayOptions, string]> = [
    ['trail', 'Trail'],
    ['fullHistory', 'Full history'],
    ['forecast', 'Forecast'],
    ['label', 'Date label'],
  ]

  return (
    <div className="flex shrink-0 flex-col gap-2.5 rounded-lg border border-hairline bg-surface px-3 py-2.5">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            onClick={onRestart}
            disabled={index === 0}
            aria-label="Restart from the beginning"
            title="Restart from the beginning (Home)"
          >
            <RotateCcw />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => step(-1)}
            disabled={index === 0}
            aria-label="Previous month"
            title="Previous month (←)"
          >
            <SkipBack />
          </Button>
          <Button
            variant={playing ? 'default' : 'outline'}
            size="icon"
            onClick={onTogglePlay}
            aria-label={playing ? 'Pause' : atEnd ? 'Replay from the beginning' : 'Play'}
            title={playing ? 'Pause (space)' : atEnd ? 'Replay from the start (space)' : 'Play (space)'}
          >
            {playing ? <Pause /> : <Play />}
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => step(1)}
            disabled={atEnd}
            aria-label="Next month"
            title="Next month (→)"
          >
            <SkipForward />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={onJumpToLatest}
            disabled={atEnd}
            aria-label="Jump to latest"
            title="Jump to latest (End)"
          >
            <ChevronLast />
          </Button>
        </div>

        <div className="min-w-0 flex-1">
          <Slider
            value={[Math.min(index, last)]}
            min={0}
            max={last}
            step={1}
            onValueChange={([value]) => onIndexChange(value)}
            aria-label="Scrub through history"
          />
        </div>

        <span className="tabular w-[74px] shrink-0 text-right text-xs font-medium text-ink">
          {current?.label ?? '—'}
        </span>

        <Tabs value={String(speed)} onValueChange={(value) => onSpeedChange(Number(value))}>
          <TabsList>
            {SPEEDS.map((s) => (
              <TabsTrigger key={s} value={String(s)}>
                {s}×
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
      </div>

      <div className="flex flex-wrap items-center gap-x-5 gap-y-2 border-t border-hairline pt-2.5">
        {toggles.map(([key, label]) => (
          <label key={key} className="flex cursor-pointer items-center gap-2 text-[11.5px] text-ink-secondary">
            <Switch
              checked={options[key]}
              onCheckedChange={(checked) => onOptionsChange({ ...options, [key]: checked })}
            />
            {label}
          </label>
        ))}
        <span className="ml-auto hidden text-[10.5px] text-ink-muted sm:inline">
          space play · ←/→ step · shift+← year · home/end
        </span>
      </div>
    </div>
  )
}
