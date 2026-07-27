import type { Narrative } from '@/lib/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Markup, parseMarkup } from '@/lib/markup'

/** Flatten markup to plain text, for short strings rendered inside list items. */
function plain(text: string): string {
  return parseMarkup(text)
    .map((segments) => segments.map((s) => s.text).join(''))
    .join(' ')
    .replace(/\s+/g, ' ')
    .trim()
}

function asList(value: unknown): string[] {
  if (Array.isArray(value)) return value.map((v) => String(v))
  if (typeof value === 'string' && value.trim()) return [value]
  return []
}

export function NarrativePanel({ narrative }: { narrative: Narrative | null }) {
  if (!narrative) return null

  const summary = typeof narrative.executive_summary === 'string' ? narrative.executive_summary : ''
  const interpretation =
    typeof narrative.interpretation === 'string' ? narrative.interpretation : ''
  const takeaways = asList(narrative.takeaways)
  const risks = asList(narrative.risks)

  if (!summary && !interpretation && !takeaways.length && !risks.length) return null

  return (
    <Card>
      <CardHeader>
        <CardTitle>Research Narrative</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {summary ? (
          <Markup text={summary} className="text-[12px] leading-relaxed text-ink-secondary" />
        ) : null}

        {takeaways.length ? (
          <div>
            <div className="text-[10px] font-medium uppercase tracking-[0.09em] text-ink-muted">
              Key Takeaways
            </div>
            <ul className="mt-1.5 space-y-1.5">
              {takeaways.map((item, i) => (
                <li key={i} className="flex gap-2 text-[11.5px] leading-snug text-ink-secondary">
                  <span aria-hidden className="mt-[6px] size-1 shrink-0 rounded-full bg-viz-history" />
                  <span>{plain(item)}</span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {interpretation ? (
          <div>
            <div className="text-[10px] font-medium uppercase tracking-[0.09em] text-ink-muted">
              Interpretation
            </div>
            <Markup
              text={interpretation}
              className="mt-1 text-[11.5px] leading-relaxed text-ink-secondary"
            />
          </div>
        ) : null}

        {risks.length ? (
          <div>
            <div className="text-[10px] font-medium uppercase tracking-[0.09em] text-ink-muted">
              Risks
            </div>
            <ul className="mt-1.5 space-y-1.5">
              {risks.map((item, i) => (
                <li key={i} className="flex gap-2 text-[11.5px] leading-snug text-ink-secondary">
                  <span
                    aria-hidden
                    className="mt-[6px] size-1 shrink-0 rounded-full"
                    style={{ backgroundColor: 'var(--regime-slowdown)' }}
                  />
                  <span>{plain(item)}</span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </CardContent>
    </Card>
  )
}
