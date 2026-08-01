import type { CyclePayload, ForecastPayload, FramePayload, MarketProfile } from './types'

const BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')

const frameCache = new Map<string, FramePayload>()
const forecastCache = new Map<string, ForecastPayload>()

async function get<T>(path: string, signal?: AbortSignal): Promise<T> {
  const url = `${BASE_URL}${path}`
  const response = await fetch(url, { signal })
  if (!response.ok) {
    const detail = await response.text().catch(() => '')
    throw new Error(`${response.status} ${response.statusText}${detail ? ` — ${detail}` : ''}`)
  }
  return (await response.json()) as T
}

export const api = {
  markets: (signal?: AbortSignal) => get<MarketProfile[]>('/api/markets', signal),

  cycle: (market: string, signal?: AbortSignal) =>
    get<CyclePayload>(`/api/cycle?market=${encodeURIComponent(market)}`, signal),

  frame: (market: string, idx: number, signal?: AbortSignal): Promise<FramePayload> => {
    const key = `${market}:${idx}`
    if (frameCache.has(key)) {
      return Promise.resolve(frameCache.get(key)!)
    }
    return get<FramePayload>(`/api/frame/${idx}?market=${encodeURIComponent(market)}`, signal).then(
      (data) => {
        frameCache.set(key, data)
        return data
      },
    )
  },

  forecast: (market: string, idx: number, signal?: AbortSignal): Promise<ForecastPayload> => {
    const key = `${market}:${idx}`
    if (forecastCache.has(key)) {
      return Promise.resolve(forecastCache.get(key)!)
    }
    return get<ForecastPayload>(
      `/api/forecast?market=${encodeURIComponent(market)}&idx=${idx}`,
      signal,
    ).then((data) => {
      forecastCache.set(key, data)
      return data
    })
  },

  reportUrl: (market: string, idx: number) =>
    `${BASE_URL}/api/report?market=${encodeURIComponent(market)}&idx=${idx}`,

  chartUrl: (market: string, idx: number) =>
    `${BASE_URL}/api/chart.png?market=${encodeURIComponent(market)}&idx=${idx}`,

  clearCache: async (market?: string) => {
    frameCache.clear()
    forecastCache.clear()
    const query = market ? `?market=${encodeURIComponent(market)}` : ''
    const response = await fetch(`${BASE_URL}/api/cache/clear${query}`, { method: 'POST' })
    if (!response.ok) throw new Error(`Cache clear failed: ${response.status}`)
    return response.json() as Promise<{ cleared: string[] }>
  },
}
