import type { HealthEntry } from '@/lib/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export function DataHealth({
  health,
  warnings,
  asOf,
}: {
  health: Record<string, HealthEntry>
  warnings: string[]
  asOf: string
}) {
  const entries = Object.entries(health ?? {})

  return (
    <Card>
      <CardHeader>
        <CardTitle>Data Provenance</CardTitle>
        <span className="tabular text-[10px] text-ink-muted">as of {asOf}</span>
      </CardHeader>
      <CardContent className="space-y-2">
        {warnings?.length ? (
          <ul className="space-y-1 rounded-md border border-hairline bg-ink/[0.03] p-2">
            {warnings.map((warning, i) => (
              <li key={i} className="flex gap-1.5 text-[11px] text-ink-secondary">
                <span aria-hidden style={{ color: 'var(--regime-slowdown)' }}>
                  ⚠
                </span>
                <span>{warning}</span>
              </li>
            ))}
          </ul>
        ) : null}

        {entries.length ? (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[300px] text-[11px]">
              <thead>
                <tr className="border-b border-hairline text-[10px] uppercase tracking-[0.07em] text-ink-muted">
                  <th className="py-1 text-left font-medium">Series</th>
                  <th className="py-1 text-left font-medium">Source</th>
                  <th className="py-1 text-right font-medium">Released</th>
                </tr>
              </thead>
              <tbody>
                {entries.map(([name, meta]) => (
                  <tr key={name} className="border-b border-hairline/60 last:border-0">
                    <td className="py-1 pr-2 text-ink">{name}</td>
                    <td className="py-1 pr-2 text-ink-secondary">{meta.source ?? '—'}</td>
                    <td className="tabular py-1 text-right text-ink-muted">
                      {meta.release_date ?? '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-xs text-ink-muted">No provenance metadata reported.</p>
        )}
      </CardContent>
    </Card>
  )
}
