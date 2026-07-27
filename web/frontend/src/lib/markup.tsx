import * as React from 'react'

/**
 * The narrative engine emits reportlab markup (`<b>`, `<br/>`, `<font size=8>`,
 * `&bull;`) because its first consumer was the PDF. The PDF still needs it, so
 * rather than stripping it at the source this parses the known tags into React
 * nodes.
 *
 * Deliberately a whitelist parser and not `dangerouslySetInnerHTML`: the input
 * is server-generated today, but rendering arbitrary HTML from an API response
 * is a footgun worth not leaving armed.
 */

const ENTITIES: Record<string, string> = {
  '&bull;': '•',
  '&amp;': '&',
  '&lt;': '<',
  '&gt;': '>',
  '&nbsp;': ' ',
  '&quot;': '"',
  '&#39;': "'",
}

function decodeEntities(text: string): string {
  return text.replace(/&[a-z#0-9]+;/gi, (match) => ENTITIES[match.toLowerCase()] ?? match)
}

/** Matches an opening/closing b, i, or font tag, or a br. Nothing else. */
const TAG = /<\s*(\/?)\s*(b|i|br|font)\b[^>]*>/gi

interface Segment {
  text: string
  bold: boolean
  italic: boolean
  small: boolean
}

/** Split markup into paragraphs (on `<br/><br/>`) of styled inline segments. */
export function parseMarkup(input: string): Segment[][] {
  const paragraphs: Segment[][] = []
  let current: Segment[] = []
  let bold = 0
  let italic = 0
  let small = 0
  let pendingBreaks = 0

  const push = (text: string) => {
    if (!text) return
    // A single <br/> is a line break inside a paragraph; two or more start a new one.
    if (pendingBreaks >= 2 && current.length) {
      paragraphs.push(current)
      current = []
    } else if (pendingBreaks === 1 && current.length) {
      current.push({ text: '\n', bold: false, italic: false, small: false })
    }
    pendingBreaks = 0
    current.push({
      text: decodeEntities(text),
      bold: bold > 0,
      italic: italic > 0,
      small: small > 0,
    })
  }

  let lastIndex = 0
  for (const match of input.matchAll(TAG)) {
    push(input.slice(lastIndex, match.index))
    lastIndex = match.index + match[0].length

    const [, closing, rawTag] = match
    const tag = rawTag.toLowerCase()

    if (tag === 'br') {
      pendingBreaks += 1
    } else if (tag === 'b') {
      bold += closing ? -1 : 1
    } else if (tag === 'i') {
      italic += closing ? -1 : 1
    } else if (tag === 'font') {
      small += closing ? -1 : 1
    }
  }
  push(input.slice(lastIndex))

  if (current.length) paragraphs.push(current)
  return paragraphs.filter((p) => p.some((s) => s.text.trim()))
}

export function Markup({ text, className }: { text: string; className?: string }) {
  const paragraphs = React.useMemo(() => parseMarkup(text), [text])

  return (
    <div className={className}>
      {paragraphs.map((segments, i) => (
        <p key={i} className={i > 0 ? 'mt-2' : undefined} style={{ whiteSpace: 'pre-line' }}>
          {segments.map((segment, j) => {
            if (segment.text === '\n') return <br key={j} />
            const classes = [
              segment.bold ? 'font-semibold text-ink' : '',
              segment.italic ? 'italic' : '',
              segment.small ? 'text-[10.5px]' : '',
            ]
              .filter(Boolean)
              .join(' ')
            return classes ? (
              <span key={j} className={classes}>
                {segment.text}
              </span>
            ) : (
              <React.Fragment key={j}>{segment.text}</React.Fragment>
            )
          })}
        </p>
      ))}
    </div>
  )
}
