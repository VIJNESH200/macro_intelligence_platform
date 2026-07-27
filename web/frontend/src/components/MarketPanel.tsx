import type { AssetRow } from '@/lib/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

const HORIZONS = ['1M', '3M', '6M', '12M'] as const

/**
 * Sign is part of the string the backend formats ("+1.2%", "-38 bp"), so
 * direction never rests on colour alone.
 */
function deltaColor(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return 'var(--ink-muted)'
  if (value > 0) return 'var(--delta-up)'
  if (value < 0) return 'var(--delta-down)'
  return 'var(--ink-secondary)'
}

export function MarketPanel({ rows }: { rows: AssetRow[] }) {
  if (!rows?.length) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Market Context</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-xs text-ink-muted">No market series selected.</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Market Context</CardTitle>
        <span className="text-[10px] text-ink-muted">Trailing returns</span>
      </CardHeader>
      <CardContent className="px-0 pb-2">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[420px] text-xs">
            <thead>
              <tr className="border-b border-hairline text-[10px] uppercase tracking-[0.07em] text-ink-muted">
                <th className="px-4 py-1.5 text-left font-medium">Asset</th>
                <th className="px-2 py-1.5 text-right font-medium">Level</th>
                {HORIZONS.map((h) => (
                  <th key={h} className="px-2 py-1.5 text-right font-medium last:pr-4">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.name} className="border-b border-hairline/60 last:border-0">
                  <td className="px-4 py-1.5 text-ink">{row.name}</td>
                  <td className="tabular px-2 py-1.5 text-right text-ink-secondary">
                    {row.current_val_str}
                  </td>
                  {HORIZONS.map((h) => (
                    <td
                      key={h}
                      className="tabular px-2 py-1.5 text-right last:pr-4"
                      style={{ color: deltaColor(row.returns_raw?.[h]) }}
                    >
                      {row.returns_str?.[h] ?? '—'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}
