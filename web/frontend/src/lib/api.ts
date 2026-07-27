import type { CyclePayload, ForecastPayload, FramePayload, MarketProfile } from './types'

async function get<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(path, { signal })
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

  frame: (market: string, idx: number, signal?: AbortSignal) =>
    get<FramePayload>(`/api/frame/${idx}?market=${encodeURIComponent(market)}`, signal),

  forecast: (market: string, idx: number, signal?: AbortSignal) =>
    get<ForecastPayload>(
      `/api/forecast?market=${encodeURIComponent(market)}&idx=${idx}`,
      signal,
    ),

  reportUrl: (market: string, idx: number) =>
    `/api/report?market=${encodeURIComponent(market)}&idx=${idx}`,

  chartUrl: (market: string, idx: number) =>
    `/api/chart.png?market=${encodeURIComponent(market)}&idx=${idx}`,

  clearCache: async (market?: string) => {
    const query = market ? `?market=${encodeURIComponent(market)}` : ''
    const response = await fetch(`/api/cache/clear${query}`, { method: 'POST' })
    if (!response.ok) throw new Error(`Cache clear failed: ${response.status}`)
    return response.json() as Promise<{ cleared: string[] }>
  },
}
