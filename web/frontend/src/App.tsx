import * as React from 'react'
import { Download, Moon, RefreshCw, Sun } from 'lucide-react'
import { api } from '@/lib/api'
import type { CyclePayload, ForecastPayload, FramePayload, MarketProfile } from '@/lib/types'
import { QuadrantChart } from '@/components/QuadrantChart'
import { Controls, type DisplayOptions } from '@/components/Controls'
import { MarketPanel } from '@/components/MarketPanel'
import { MacroPanel } from '@/components/MacroPanel'
import { ForecastPanel } from '@/components/ForecastPanel'
import { PhasePanel } from '@/components/PhasePanel'
import { NarrativePanel } from '@/components/NarrativePanel'
import { DataHealth } from '@/components/DataHealth'
import { Sparkline } from '@/components/Sparkline'
import { StatusRail } from '@/components/StatusRail'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'

const MARKET_STORAGE_KEY = 'mip.market'
const THEME_STORAGE_KEY = 'mip.theme'
const PLAYBACK_BASE_MS = 420

function useTheme() {
  const [theme, setTheme] = React.useState<'light' | 'dark'>(() => {
    const saved = localStorage.getItem(THEME_STORAGE_KEY)
    if (saved === 'light' || saved === 'dark') return saved
    return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark'
  })

  React.useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
    localStorage.setItem(THEME_STORAGE_KEY, theme)
  }, [theme])

  return { theme, toggle: () => setTheme((t) => (t === 'dark' ? 'light' : 'dark')) }
}

export default function App() {
  const { theme, toggle } = useTheme()

  const [markets, setMarkets] = React.useState<MarketProfile[]>([])
  const [market, setMarket] = React.useState<string>(
    () => localStorage.getItem(MARKET_STORAGE_KEY) ?? 'INDIA',
  )
  const [cycle, setCycle] = React.useState<CyclePayload | null>(null)
  const [frame, setFrame] = React.useState<FramePayload | null>(null)
  const [forecast, setForecast] = React.useState<ForecastPayload | null>(null)

  const [index, setIndex] = React.useState(0)
  const [playing, setPlaying] = React.useState(false)
  const [speed, setSpeed] = React.useState(1)
  const [reloadCount, setReloadCount] = React.useState(0)
  const [loading, setLoading] = React.useState(true)
  const [refreshing, setRefreshing] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)
  const [options, setOptions] = React.useState<DisplayOptions>({
    trail: true,
    fullHistory: false,
    forecast: true,
    label: true,
  })

  React.useEffect(() => {
    api.markets().then(setMarkets).catch(() => setMarkets([]))
  }, [])

  // Loading a market is expensive server-side, so it is keyed only on `market` and `reloadCount`;
  // scrubbing never refetches the series.
  React.useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError(null)

    api
      .cycle(market, controller.signal)
      .then((payload) => {
        setCycle(payload)
        setIndex(Math.max(0, payload.frames.length - 1))
        localStorage.setItem(MARKET_STORAGE_KEY, market)
      })
      .catch((err: Error) => {
        if (err.name !== 'AbortError') setError(err.message)
      })
      .finally(() => setLoading(false))

    return () => controller.abort()
  }, [market, reloadCount])

  // Panel data follows the scrubber. Requests are aborted on change so a slow
  // response for an old frame can never overwrite a newer one. Both frame and
  // forecast update atomically so the chart projection never desyncs from the historical dot.
  React.useEffect(() => {
    if (!cycle) return
    const controller = new AbortController()
    let active = true

    const pFrame = api.frame(market, index, controller.signal)
    const pForecast = api.forecast(market, index, controller.signal)

    Promise.all([pFrame, pForecast])
      .then(([fFrame, fForecast]) => {
        if (!active) return
        setFrame(fFrame)
        setForecast(fForecast)
      })
      .catch((err: Error) => {
        if (!active || err?.name === 'AbortError') return
        pFrame.then((f) => active && setFrame(f)).catch(() => undefined)
        pForecast.then((f) => active && setForecast(f)).catch(() => undefined)
      })

    return () => {
      active = false
      controller.abort()
    }
  }, [cycle, market, index])

  React.useEffect(() => {
    if (!playing || !cycle) return
    const last = cycle.frames.length - 1
    const timer = window.setInterval(() => {
      setIndex((i) => (i >= last ? (setPlaying(false), last) : i + 1))
    }, PLAYBACK_BASE_MS / speed)
    return () => window.clearInterval(timer)
  }, [playing, speed, cycle])

  const lastIndex = cycle ? cycle.frames.length - 1 : 0

  /** Pressing play while parked at the end replays from the start. */
  const togglePlay = React.useCallback(() => {
    setPlaying((wasPlaying) => {
      if (!wasPlaying && index >= lastIndex) setIndex(0)
      return !wasPlaying
    })
  }, [index, lastIndex])

  const restart = React.useCallback(() => {
    setPlaying(false)
    setIndex(0)
  }, [])

  const stepTo = React.useCallback(
    (next: number) => {
      setPlaying(false)
      setIndex(Math.max(0, Math.min(lastIndex, next)))
    },
    [lastIndex],
  )

  // Space is the conventional play/pause key, but the browser maps it to scroll,
  // so the default has to be suppressed. Skipped while a control is focused, so
  // space still activates a focused button and arrows still move the slider.
  React.useEffect(() => {
    if (!cycle) return

    const onKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null
      if (target?.closest('input, textarea, select, [role="slider"], button, a, [contenteditable]')) {
        return
      }
      if (event.metaKey || event.ctrlKey || event.altKey) return

      switch (event.key) {
        case ' ':
          event.preventDefault()
          togglePlay()
          break
        case 'ArrowLeft':
          event.preventDefault()
          stepTo(index - (event.shiftKey ? 12 : 1))
          break
        case 'ArrowRight':
          event.preventDefault()
          stepTo(index + (event.shiftKey ? 12 : 1))
          break
        case 'Home':
          event.preventDefault()
          stepTo(0)
          break
        case 'End':
          event.preventDefault()
          stepTo(lastIndex)
          break
      }
    }

    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [cycle, index, lastIndex, togglePlay, stepTo])

  const handleRefresh = async () => {
    setRefreshing(true)
    try {
      await api.clearCache(market)
      const payload = await api.cycle(market)
      setCycle(payload)
      setIndex(Math.max(0, payload.frames.length - 1))
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setRefreshing(false)
    }
  }

  if (loading && !cycle) {
    return (
      <div className="flex min-h-dvh items-center justify-center">
        <div className="text-sm text-ink-muted">Loading market data…</div>
      </div>
    )
  }

  if (error && !cycle) {
    return (
      <div className="flex min-h-dvh items-center justify-center p-6">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle>Could not load data</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-xs text-ink-secondary">{error}</p>
            <Button onClick={() => setReloadCount((c) => c + 1)}>Retry</Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!cycle) return null

  const current = cycle.frames[Math.min(index, cycle.frames.length - 1)]
  const center = cycle.config.center

  // The whole app is pinned to the viewport on desktop so the chart and every
  // live panel animate together without the page scrolling. Only the reference
  // column scrolls internally; below `lg` this relaxes to normal document flow.
  return (
    <div className="flex min-h-dvh flex-col bg-plane lg:h-dvh lg:min-h-0 lg:overflow-hidden">
      <header className="shrink-0 border-b border-hairline bg-plane/85 backdrop-blur">
        <div className="mx-auto flex max-w-[1600px] flex-wrap items-center gap-3 px-4 py-1">
          <p className="min-w-0 truncate text-xs font-medium text-ink">
            Macro Intelligence Platform
            <span className="text-ink-muted">
              {' · '}
              {cycle.config.name} · {cycle.config.source} · {cycle.config.window}M window
            </span>
          </p>

          <div className="ml-auto flex items-center gap-2">
            {markets.length > 1 ? (
              <Tabs value={market} onValueChange={setMarket}>
                <TabsList>
                  {markets.map((m) => (
                    <TabsTrigger key={m.id} value={m.id}>
                      {m.label.replace(' Market', '')}
                    </TabsTrigger>
                  ))}
                </TabsList>
              </Tabs>
            ) : null}

            <Button variant="ghost" size="icon" className="size-7" onClick={handleRefresh} aria-label="Refetch data">
              <RefreshCw className={refreshing ? 'animate-spin' : undefined} />
            </Button>
            <Button variant="ghost" size="icon" className="size-7" onClick={toggle} aria-label="Toggle theme">
              {theme === 'dark' ? <Sun /> : <Moon />}
            </Button>
            <Button variant="outline" size="sm" asChild>
              <a href={api.reportUrl(market, index)} download>
                <Download />
                Report
              </a>
            </Button>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-[1600px] flex-1 px-4 py-3 lg:min-h-0 lg:overflow-hidden">
        <div className="grid gap-3 lg:h-full lg:min-h-0 lg:grid-cols-[minmax(0,1fr)_296px]">
          <div className="flex min-w-0 flex-col gap-3 lg:min-h-0">
            <Card className="h-[58vh] lg:h-auto lg:min-h-[200px] lg:flex-1">
              <CardContent className="h-full px-2 pt-2 pb-1">
                <QuadrantChart
                  frames={cycle.frames}
                  spline={cycle.spline}
                  bounds={cycle.bounds}
                  pointsPerSegment={cycle.points_per_segment}
                  index={index}
                  tailLength={cycle.config.tail_length}
                  forecast={options.forecast ? forecast : null}
                  showTrail={options.trail}
                  showFullHistory={options.fullHistory}
                  showForecast={options.forecast}
                  showLabel={options.label}
                  windowMonths={cycle.config.window}
                  onScrub={setIndex}
                />
              </CardContent>
            </Card>

            <Controls
              frames={cycle.frames}
              index={index}
              playing={playing}
              speed={speed}
              options={options}
              onIndexChange={stepTo}
              onTogglePlay={togglePlay}
              onRestart={restart}
              onJumpToLatest={() => stepTo(lastIndex)}
              onSpeedChange={setSpeed}
              onOptionsChange={setOptions}
            />

            {/* Both panels animate with the scrubber, so they sit under the
                chart in the eye's path rather than off in the side column. */}
            {frame ? (
              <div className="grid shrink-0 gap-3 sm:grid-cols-2 lg:h-[184px]">
                <MacroPanel
                  drivers={frame.macro_contrib?.all_drivers ?? []}
                  shifts={frame.macro_shifts}
                />
                <PhasePanel frame={frame} forecast={forecast} />
              </div>
            ) : null}
          </div>

          <aside className="space-y-3 lg:min-h-0 lg:overflow-y-auto lg:pr-0.5">
            <StatusRail
              frame={frame}
              forecast={forecast}
              current={current}
              previous={index > 0 ? cycle.frames[index - 1] : null}
              totalFrames={cycle.frames.length}
              center={center}
            />

            <Card>
              <CardHeader>
                <CardTitle>Indicator</CardTitle>
              </CardHeader>
              <CardContent>
                <Sparkline frames={cycle.frames} index={index} label={cycle.config.name} />
              </CardContent>
            </Card>

            <ForecastPanel forecast={forecast} />
            {frame ? <MarketPanel rows={frame.market_data} /> : null}
            {frame ? <NarrativePanel narrative={frame.narrative} /> : null}
            <DataHealth
              health={cycle.data_health}
              warnings={cycle.warnings}
              asOf={cycle.as_of}
            />

            <footer className="shrink-0 pb-1 text-[10px] leading-snug text-ink-muted">
              {cycle.config.name} ({cycle.config.ticker}) · {cycle.config.frequency} ·
              model v{forecast?.model_version ?? '—'} · Market data via Yahoo Finance
            </footer>
          </aside>
        </div>
      </main>
    </div>
  )
}
