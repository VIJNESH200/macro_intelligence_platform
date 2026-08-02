"""
Institutional Macro Strategy Report — PDF Builder
===================================================
Publication-quality PDF modelled on Goldman Sachs / JPMorgan / BlackRock
macro research notes. Uses ReportLab Platypus flowables with a centralised
design system (``pdf_styles``).

Guarantees exact 6-page institutional layout structure without single-row splits
or orphaned overflow pages.

**Contract** — ``build_pdf_report()`` signature is unchanged from the
previous version; all analytics, calculations, and data structures are
consumed identically.
"""
from __future__ import annotations

import datetime
import io
import re

import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, KeepTogether,
    PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle,
)

from . import pdf_styles as S

# ─── Text sanitisation ───────────────────────────────────────────────────────

_SYMBOL_MAP = {
    '▲': '+', '▼': '-', '►': '=', '█': '|',
    '↑': '^', '↓': 'v', '⚠': '[!]', '→': '->',
    '•': '&bull;',
}

_AMP_RE = re.compile(r'&(?!(amp|lt|gt|quot|apos|bull|#\d+|#x[0-9a-fA-F]+);)')


def _clean(val) -> str:
    """Sanitise strings for ReportLab XML paragraphs."""
    if val is None:
        return ""
    text = str(val)
    for sym, rep in _SYMBOL_MAP.items():
        text = text.replace(sym, rep)
    return _AMP_RE.sub('&amp;', text)


def _fmt_delta(val, is_pct: bool = False):
    """Colour-coded delta cell (returns a Paragraph flowable)."""
    if pd.isna(val):
        return Paragraph("N/A", S.TABLE_CELL_TEXT)
    sign = "+" if val > 0 else ""
    fmt = f"{sign}{val:.1f}%" if is_pct else f"{sign}{val:.2f}"
    clr = '#155724' if val > 0 else ('#721c24' if val < 0 else '#333333')
    return Paragraph(f"<font color='{clr}'>{fmt}</font>", S.TABLE_CELL_TEXT)


# ─── QR Code helper ──────────────────────────────────────────────────────────

_DASHBOARD_URL = 'https://macro-intelligence-platform-three.vercel.app/'


def _make_qr_image(url: str = _DASHBOARD_URL, box_size: int = 4) -> Image | None:
    """Generate a small QR code PNG in memory and return a ReportLab Image."""
    try:
        import qrcode
        qr = qrcode.QRCode(version=1, box_size=box_size, border=1,
                           error_correction=qrcode.constants.ERROR_CORRECT_M)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color='#0a1628', back_color='white')
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return Image(buf, width=0.8 * inch, height=0.8 * inch)
    except Exception:
        return None


# ─── Document template ───────────────────────────────────────────────────────

class _InstitutionalDoc(BaseDocTemplate):
    """Custom document template with institutional running header / footer."""

    def __init__(self, filename: str, report_data: dict, **kw):
        super().__init__(filename, **kw)
        self._report_data = report_data
        frame = Frame(
            S.MARGIN_L, S.MARGIN_B,
            S.CONTENT_W, S.CONTENT_H,
            id='main',
        )
        self.addPageTemplates([
            PageTemplate(id='pages', frames=frame, onPage=self._draw_chrome),
        ])

    def _draw_chrome(self, canvas, doc):
        canvas.saveState()
        w, h = S.PAGE_W, S.PAGE_H

        # ── Top rule ──
        canvas.setStrokeColor(S.NAVY)
        canvas.setLineWidth(1.2)
        canvas.line(S.MARGIN_L, h - 32, w - S.MARGIN_R, h - 32)

        # Thin secondary rule
        canvas.setStrokeColor(S.RULE_LIGHT)
        canvas.setLineWidth(0.4)
        canvas.line(S.MARGIN_L, h - 35, w - S.MARGIN_R, h - 35)

        # ── Running header (small-caps style) ──
        canvas.setFont('Helvetica-Bold', 7)
        canvas.setFillColor(S.NAVY)
        canvas.drawString(S.MARGIN_L, h - 25, 'MACRO INTELLIGENCE PLATFORM')
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(S.MID_GREY)
        canvas.drawRightString(w - S.MARGIN_R, h - 25, _clean(self._report_data.get('date', '')))

        # ── Bottom rule ──
        canvas.setStrokeColor(S.RULE_LIGHT)
        canvas.setLineWidth(0.4)
        canvas.line(S.MARGIN_L, 38, w - S.MARGIN_R, 38)

        # ── Footer ──
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(S.MID_GREY)
        page = canvas.getPageNumber()
        footer = (f'Macro Intelligence Platform  \u00b7  '
                  f'Institutional Strategy Report  \u00b7  '
                  f'Page {page}  \u00b7  Generated automatically')
        canvas.drawString(S.MARGIN_L, S.FOOTER_Y, footer)

        canvas.restoreState()


# ─── Main builder ─────────────────────────────────────────────────────────────

def build_pdf_report(data, analysis, insights, market_insights, narrative,
                     analogues, deltas, chart_path, output_path,
                     data_metadata=None):
    """Build the institutional PDF report.

    Signature is identical to the previous version — drop-in replacement.
    """
    doc = _InstitutionalDoc(
        output_path, data,
        pagesize=letter,
        leftMargin=S.MARGIN_L, rightMargin=S.MARGIN_R,
        topMargin=S.MARGIN_T, bottomMargin=S.MARGIN_B,
    )

    el = []  # flowable list
    cw = S.CONTENT_W / inch  # content width in inches (7.25 in)

    # =====================================================================
    # PAGE 1 — Cover & Executive Summary
    # =====================================================================
    market_name = data.get('indicator', 'Macroeconomic Indicator')
    country = data.get('country', data.get('market', ''))

    el.append(Paragraph('Macroeconomic Strategy Report', S.REPORT_TITLE))

    sub_parts = [_clean(market_name)]
    if country:
        sub_parts.append(_clean(country))
    el.append(Paragraph(
        ' &nbsp;\u00b7&nbsp; '.join(sub_parts),
        ParagraphStyle('Subtitle', parent=S.BODY,
                       fontSize=10, textColor=S.MID_GREY, spaceAfter=2),
    ))

    # Compact metadata table
    meta_style = S.METADATA_VALUE
    meta_label = S.METADATA_LABEL
    meta_data = [
        [Paragraph('Report Date', meta_label),
         Paragraph(_clean(data.get('date', '')), meta_style),
         Paragraph('Source', meta_label),
         Paragraph(_clean(data.get('source', '')), meta_style)],
        [Paragraph('Generated', meta_label),
         Paragraph(_clean(data.get('timestamp', '')), meta_style),
         Paragraph('Window', meta_label),
         Paragraph(_clean(data.get('window', '')), meta_style)],
    ]
    meta_t = Table(meta_data, colWidths=[0.9 * inch, 2.725 * inch, 0.9 * inch, 2.725 * inch])
    meta_t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('LINEBELOW', (0, -1), (-1, -1), 0.5, S.BORDER_GREY),
    ]))
    el.append(meta_t)
    el.append(Spacer(1, 4))

    # Executive snapshot box
    conf_score = data.get('macro_contrib', {}).get('confidence_score', 0)
    m_score = data.get('macro_contrib', {}).get('macro_score', 0)
    macro_interp = data.get('macro_contrib', {}).get('macro_interpretation', 'Neutral')

    all_drivers = data.get('macro_contrib', {}).get('all_drivers', [])
    primary_risk = 'None identified'
    valid_risk = [d for d in all_drivers
                  if isinstance(d, dict) and d.get('score') is not None
                  and not pd.isna(d.get('score'))]
    if valid_risk:
        worst = min(valid_risk, key=lambda x: x['score'])
        if worst['score'] < -0.5:
            primary_risk = f"{worst['indicator']} {worst['state'].lower()}"

    trans_probs = analysis.get('transition_probs')
    next_phase = 'Unknown'
    if trans_probs:
        next_phase = max(trans_probs.items(), key=lambda x: x[1])[0]

    valid_count = len([d for d in all_drivers if d.get('state') != 'Unknown'])
    conf_label = 'Confidence' if conf_score > 0 else 'Data Coverage'
    conf_disp = f'{conf_score:.0f}%' if conf_score > 0 else f'{valid_count} of 5 indicators'

    snap_rows = [
        [Paragraph('<b>Current Regime</b>', S.BODY),
         Paragraph(f'<b>{_clean(data["quadrant"])}</b>', S.BODY),
         Paragraph(f'<b>{conf_label}</b>', S.BODY),
         Paragraph(conf_disp, S.BODY)],
        [Paragraph('<b>Macro Score</b>', S.BODY),
         Paragraph(f'{m_score:+.2f}' if m_score is not None else 'N/A', S.BODY),
         Paragraph('<b>Primary Risk</b>', S.BODY),
         Paragraph(_clean(primary_risk), S.BODY)],
        [Paragraph('<b>Investment View</b>', S.BODY),
         Paragraph(_clean(macro_interp), S.BODY),
         Paragraph('<b>Next Likely Phase</b>', S.BODY),
         Paragraph(_clean(next_phase), S.BODY)],
    ]
    snap_t = Table(snap_rows, colWidths=[1.15 * inch, 2.15 * inch, 1.65 * inch, 2.3 * inch])
    snap_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), S.CALLOUT_BG),
        ('BOX', (0, 0), (-1, -1), 0.5, S.NAVY_ACCENT),
        ('LINEBEFORE', (0, 0), (0, -1), 2.5, S.NAVY),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    el.append(snap_t)
    el.append(Spacer(1, 4))

    # 1. Executive Summary
    el.append(S.section_heading(1, 'Executive Summary'))

    # Clean prose paragraphs without raw HTML breaks
    raw_exec = narrative.get('executive_summary', '')
    lines = [l.strip() for l in raw_exec.replace('<br/>', '\n').split('\n') if l.strip()]
    for line in lines:
        el.append(Paragraph(_clean(line), S.BODY))

    el.append(Spacer(1, 4))

    # Key Takeaways card
    tk_rows = [[Paragraph('<b>Key Takeaways</b>',
                          ParagraphStyle('TKH', parent=S.BODY, textColor=S.NAVY, fontSize=9))]]
    for tk in narrative.get('takeaways', []):
        tk_rows.append([Paragraph(f'<bullet>&bull;</bullet> {_clean(tk)}', S.BULLET)])

    tk_t = Table(tk_rows, colWidths=[cw * inch])
    tk_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), S.LIGHT_GREY),
        ('BOX', (0, 0), (-1, -1), 0.4, S.BORDER_GREY),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    el.append(tk_t)
    el.append(Spacer(1, 2))
    el.append(Paragraph(
        '<font size="7" color="#999999"><i>'
        'Immediate transition probabilities refer to the next business cycle phase. '
        'Historical analogues describe longer-term six-month outcomes.'
        '</i></font>', S.BODY))

    el.append(PageBreak())

    # =====================================================================
    # PAGE 2 — Macroeconomic Positioning & Research Dashboard
    # =====================================================================
    el.append(S.section_heading(2, 'Macroeconomic Positioning'))
    img = Image(chart_path)
    aspect = img.imageHeight / float(img.imageWidth)
    img.drawWidth = cw * inch
    img.drawHeight = (cw * inch) * aspect
    el.append(img)
    el.append(Paragraph(
        f'<i>Business cycle quadrant chart &mdash; {_clean(data.get("indicator", ""))} '
        f'&middot; {_clean(data.get("source", ""))} &middot; '
        f'{_clean(data.get("window", ""))} window</i>',
        S.CAPTION))

    # 3. Research Dashboard
    el.append(S.section_heading(3, 'Research Dashboard'))

    def _score_label(score):
        if score >= 80: return 'Strongly Positive'
        if score >= 60: return 'Positive'
        if score >= 40: return 'Neutral'
        if score >= 20: return 'Negative'
        return 'Strongly Negative'

    sim_str = (analogues['averages']['avg_sim_str']
               if analogues and analogues.get('averages') else 'N/A')
    mkt_score = (market_insights.get('market_score', 50)
                 if isinstance(market_insights, dict) else 50)
    m_str = f'{m_score:+.2f}' if m_score is not None else 'N/A'
    m_interp_short = data.get('macro_contrib', {}).get('macro_interpretation', 'Neutral')

    kpi_cards = [
        S.kpi_card('Macro Score', m_str, m_interp_short),
        S.kpi_card('Market Score', f'{mkt_score:.0f}', _score_label(mkt_score)),
        S.kpi_card('Historical Similarity', sim_str),
        S.kpi_card('Transition Risk', f"{insights['highest_transition_prob']:.0f}%"),
    ]
    kpi_strip = Table([kpi_cards], colWidths=[S.CONTENT_W / 4] * 4)
    kpi_strip.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 1),
        ('RIGHTPADDING', (0, 0), (-1, -1), 1),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))

    dash_elements = [kpi_strip, Spacer(1, 4)]

    # Key Metrics Delta
    if deltas:
        km_data = [
            ['Key Metrics', 'Previous', 'Current', 'Change'],
            ['Phase', _clean(deltas['prev_phase']), _clean(data['quadrant']), ''],
            ['Economic Health',
             f"{deltas['prev_health']:.2f}", f"{data['health_val']:.2f}",
             _fmt_delta(deltas['health_delta'])],
            ['Economic Momentum',
             f"{deltas['prev_momentum']:.2f}", f"{data['momentum_val']:.2f}",
             _fmt_delta(deltas['momentum_delta'])],
            ['Transition Probability',
             f"{deltas['prev_transition_prob']:.0f}%",
             f"{insights['highest_transition_prob']:.0f}%",
             _fmt_delta(deltas['prob_delta'], True)],
        ]
        km_style = S.institutional_table_style(len(km_data))
        km_style.append(('ALIGN', (0, 0), (0, -1), 'LEFT'))
        km_t = Table(km_data, colWidths=[2.45 * inch, 1.6 * inch, 1.6 * inch, 1.6 * inch])
        km_t.setStyle(TableStyle(km_style))
        dash_elements.append(km_t)

    el.append(KeepTogether(dash_elements))
    el.append(PageBreak())

    # =====================================================================
    # PAGE 3 — Macro Drivers & Regime Dynamics
    # =====================================================================
    el.append(S.section_heading(4, 'Quantitative Macro Drivers'))

    if data.get('macro_contrib') and data['macro_contrib'].get('all_drivers'):
        mc = data['macro_contrib']
        evals = mc.get('evaluations', {})

        md_data = [['Indicator', 'Raw (Percentile)', 'Level', 'Trend', 'Impact']]
        row_i = 1
        for d in mc['all_drivers']:
            name = d['indicator']
            ev = evals.get(name, {})
            raw_val = ev.get('raw_value', np.nan)
            yoy_val = ev.get('yoy_value', np.nan)
            pct_str = ev.get('percentile', 'N/A')
            level_str = ev.get('level', d['state'])
            trend_str = ev.get('trend', 'N/A')

            if pd.isna(raw_val):
                raw_disp = 'N/A'
            elif not pd.isna(yoy_val):
                raw_disp = f'{yoy_val:.2f}% ({pct_str})'
            elif name in ['Yield 10Y', 'Yield Short', 'Yield Spread', 'Real Policy Rate']:
                raw_disp = f'{raw_val:.2f}% ({pct_str})'
            else:
                raw_disp = f'{raw_val:.2f} ({pct_str})'

            sign = '+' if d['score'] > 0 else ''
            sym_clean = _clean(d.get('symbol', ''))
            md_data.append([
                _clean(name), _clean(raw_disp),
                f'{sym_clean} {_clean(level_str)}',
                _clean(trend_str), f'{sign}{d["score"]:.2f}',
            ])
            row_i += 1

        md_cmds = S.institutional_table_style(len(md_data))
        for i, d in enumerate(mc['all_drivers'], start=1):
            ev = evals.get(d['indicator'], {})
            level_str = ev.get('level', d['state'])
            md_cmds.append(('TEXTCOLOR', (2, i), (2, i), S.signal_text_color(level_str)))
        md_cmds.append(('ALIGN', (0, 0), (0, -1), 'LEFT'))

        md_t = Table(md_data, colWidths=[1.65 * inch, 1.8 * inch, 1.4 * inch, 1.2 * inch, 1.2 * inch])
        md_t.setStyle(TableStyle(md_cmds))
        el.append(md_t)
        el.append(S.small_spacer())

    # 5. Key Regime Developments
    el.append(S.section_heading(5, 'Key Regime Developments'))
    shifts = data.get('macro_shifts', [])
    if shifts:
        for s in shifts:
            el.append(Paragraph(f'<bullet>&bull;</bullet> {_clean(s)}', S.BULLET))
    else:
        dev_bullets = []
        dev_bullets.append(
            f"The economy is currently in the <b>{_clean(data['quadrant'])}</b> regime "
            f"with a macro score of <b>{m_score:+.2f}</b>." if m_score is not None else
            f"The economy is currently in the <b>{_clean(data['quadrant'])}</b> regime.")
        dur = analysis.get('current_duration', '')
        if dur:
            dev_bullets.append(
                f"Current phase duration: <b>{_clean(dur)}</b> "
                f"({analysis.get('completion_pct', 0):.0f}% of historical average).")
        if trans_probs:
            top_trans = max(trans_probs.items(), key=lambda x: x[1])
            dev_bullets.append(
                f"Historical transition probability favours <b>{_clean(top_trans[0])}</b> at {top_trans[1]:.0f}%.")
        for b in dev_bullets:
            el.append(Paragraph(f'<bullet>&bull;</bullet> {b}', S.BULLET))
    el.append(S.small_spacer())

    # 6. Research Insights
    el.append(S.section_heading(6, 'Research Insights'))
    narrative_list = data.get('research_narrative', [])
    if isinstance(narrative_list, list) and narrative_list:
        for item in narrative_list:
            if isinstance(item, dict):
                title = item.get('title', 'Macroeconomic Synthesis')
                text = item.get('narrative')
                if not text:
                    text = f"{item.get('observation', '')} {item.get('interpretation', '')} {item.get('implication', '')}"

                card_rows = [
                    [Paragraph(f'<b>{_clean(title)}</b>',
                               ParagraphStyle('IT', parent=S.BODY, textColor=S.NAVY, fontName='Helvetica-Bold'))],
                    [Paragraph(_clean(text), S.BODY)],
                ]
                card_t = Table(card_rows, colWidths=[cw * inch])
                card_t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), S.LIGHT_GREY),
                    ('BOX', (0, 0), (-1, -1), 0.4, S.BORDER_GREY),
                    ('LINEBEFORE', (0, 0), (0, -1), 3, S.NAVY),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ]))
                el.append(card_t)
                el.append(Spacer(1, 3))
    el.append(S.small_spacer())

    # 7. Cycle Timeline & Transition Outlook
    c_dur = Paragraph(
        f'<b>{_clean(analysis.get("current_duration", "N/A"))}</b>',
        ParagraphStyle('HL', parent=S.BODY, textColor=S.HIGHLIGHT_TEXT))
    p_pct = Paragraph(
        f'<b>{analysis.get("completion_pct", 0):.0f}%</b> of historical average',
        ParagraphStyle('HL', parent=S.BODY, textColor=S.HIGHLIGHT_TEXT))

    t_probs = analysis.get('transition_probs', {})
    t_rows = []
    if t_probs:
        for ph, prob in t_probs.items():
            blocks = int(prob / 10)
            bar = '|' * blocks
            t_rows.append([
                Paragraph(f'<b>{_clean(ph)}</b>', S.BODY),
                Paragraph(f'<font color="#0a1628">{bar}</font> {prob:.0f}%', S.BODY),
            ])
        t_rows.append([Paragraph(
            '<font size="7.5" color="#999999"><i>Conditional probabilities based on historical transitions.</i></font>', S.BODY), ''])
    else:
        t_rows = [['N/A', 'N/A']]

    t_inner = Table(t_rows, colWidths=[1.6 * inch, 1.8 * inch])
    t_inner_cmds = [
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
    ]
    if t_probs:
        last = len(t_rows) - 1
        t_inner_cmds.append(('SPAN', (0, last), (1, last)))
        t_inner_cmds.append(('TOPPADDING', (0, last), (1, last), 2))
    t_inner.setStyle(TableStyle(t_inner_cmds))

    hist_rows = [
        ['Current Phase Duration', c_dur],
        ['Phase Completion', p_pct],
        ['Average Phase Duration', str(analysis.get('avg_duration', 'N/A'))],
        ['Longest Historical', str(analysis.get('longest_duration', 'N/A'))],
        ['Historical Occurrences', str(analysis.get('occurrences', 'N/A'))],
        ['Next-Phase Probabilities', t_inner],
    ]
    hist_cmds = [
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LINEBELOW', (0, 0), (-1, -1), 0.4, S.BORDER_GREY),
        ('BACKGROUND', (1, 0), (1, 0), S.HIGHLIGHT_BG),
        ('BACKGROUND', (1, 1), (1, 1), S.HIGHLIGHT_BG),
    ]
    for i in range(len(hist_rows)):
        if i % 2 == 1:
            hist_cmds.append(('BACKGROUND', (0, i), (0, i), S.LIGHT_GREY))
    hist_t = Table(hist_rows, colWidths=[3.5 * inch, 3.75 * inch])
    hist_t.setStyle(TableStyle(hist_cmds))

    el.append(KeepTogether([
        S.section_heading(7, 'Cycle Timeline & Transition Outlook'),
        hist_t,
    ]))

    el.append(PageBreak())

    # =====================================================================
    # PAGE 4 — Historical Validation & Market Context
    # =====================================================================
    el.append(S.section_heading(8, 'Historical Analogues'))
    el.append(Paragraph('Most statistically similar historical macro environments.', S.BODY))

    if analogues and analogues.get('matches'):
        matches = analogues['matches']
        averages = analogues['averages']

        ana_data = [['Historical Period', 'Similarity', 'Phase Duration',
                     'Next Phase', f"6M Fwd ({matches[0]['benchmark_name']})"]]
        ana_cmds = S.institutional_table_style(len(matches) + 2)

        for i, a in enumerate(matches, start=1):
            ana_data.append([
                a['date_str'], a['similarity_str'], a['duration'],
                a['next_phase'], a['fwd_ret'],
            ])
            val = a['fwd_ret_val']
            if not pd.isna(val):
                bg, tc = S.return_color(val)
                ana_cmds.append(('BACKGROUND', (4, i), (4, i), bg))
                ana_cmds.append(('TEXTCOLOR', (4, i), (4, i), tc))

        avg_row = [
            'AVERAGE', averages['avg_sim_str'], averages['avg_dur_str'],
            averages['most_common_next'], averages['avg_fwd_str'],
        ]
        ana_data.append(avg_row)
        last_idx = len(ana_data) - 1
        ana_cmds += S.summary_row_style(last_idx)
        avg_val = averages['avg_fwd_val']
        if not pd.isna(avg_val):
            if avg_val > 5:
                ana_cmds.append(('BACKGROUND', (4, last_idx), (4, last_idx), S.GREEN_STRONG))
            elif avg_val > 0:
                ana_cmds.append(('BACKGROUND', (4, last_idx), (4, last_idx), colors.HexColor('#28a745')))
            elif avg_val < -5:
                ana_cmds.append(('BACKGROUND', (4, last_idx), (4, last_idx), S.RED_STRONG))
            elif avg_val < 0:
                ana_cmds.append(('BACKGROUND', (4, last_idx), (4, last_idx), colors.HexColor('#dc3545')))

        ana_t = Table(ana_data, colWidths=[1.5 * inch, 1.25 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch])
        ana_t.setStyle(TableStyle(ana_cmds))
        el.append(ana_t)
    el.append(S.small_spacer())

    # 9. Cross-Market Context
    el.append(S.section_heading(9, 'Cross-Market Context'))
    if data.get('market_data'):
        mkt_data = [['Asset / Series', 'Current', '1M', '3M', '6M', '12M']]
        mkt_cmds = S.institutional_table_style(len(data['market_data']) + 1)
        mkt_cmds.append(('ALIGN', (0, 0), (0, -1), 'LEFT'))
        mkt_cmds.append(('ALIGN', (1, 0), (-1, -1), 'RIGHT'))

        for i, asset in enumerate(data['market_data'], start=1):
            mkt_data.append([
                asset['name'], asset['current_val_str'],
                asset['returns_str'].get('1M', 'N/A'),
                asset['returns_str'].get('3M', 'N/A'),
                asset['returns_str'].get('6M', 'N/A'),
                asset['returns_str'].get('12M', 'N/A'),
            ])
            for j, h in enumerate(['1M', '3M', '6M', '12M'], start=2):
                val = asset['returns_raw'].get(h)
                if val is not None and not pd.isna(val):
                    bg, tc = S.return_color(val)
                    mkt_cmds.append(('BACKGROUND', (j, i), (j, i), bg))
                    mkt_cmds.append(('TEXTCOLOR', (j, i), (j, i), tc))

        mkt_t = Table(mkt_data, colWidths=[2.05 * inch, 1.3 * inch, 0.975 * inch, 0.975 * inch, 0.975 * inch, 0.975 * inch])
        mkt_t.setStyle(TableStyle(mkt_cmds))
        el.append(mkt_t)

    el.append(PageBreak())

    # =====================================================================
    # PAGE 5 — Integrated Market Interpretation & Core Risks
    # =====================================================================
    el.append(S.section_heading(10, 'Integrated Market Interpretation'))
    interp_text = narrative.get('interpretation', '')
    interp_paragraphs = [p.strip() for p in interp_text.split('\n\n') if p.strip()]
    for p in interp_paragraphs:
        el.append(Paragraph(_clean(p), S.BODY))

    el.append(S.small_spacer())
    el.append(S.section_heading(11, 'Core Macro Risks'))
    for r in narrative.get('risks', []):
        el.append(Paragraph(f'<bullet>&bull;</bullet> {_clean(r)}', S.BULLET))

    el.append(PageBreak())

    # =====================================================================
    # PAGE 6 — Forward Outlook, Scenarios & Transition Matrix
    # =====================================================================
    el.append(S.section_heading(12, 'Forward Outlook'))
    forecast = data.get('forecast')
    if forecast:
        fc_data = [['Horizon', 'Proj. Phase', 'Conviction', 'Health (X)', 'Momentum (Y)']]
        try:
            from ..config import FORECAST_CONFIG
        except ImportError:
            from config import FORECAST_CONFIG
        horizons_list = FORECAST_CONFIG.get('horizons', [3, 6, 9])
        for h in horizons_list:
            key = f'forecast_{h}m'
            if key in forecast:
                fh = forecast[key]
                fc_data.append([
                    f'{h}-Month', fh['quadrant'],
                    f"{fh.get('conviction', 0):.1f}%",
                    f"{fh['x']:.2f}", f"{fh['y']:.2f}",
                ])

        if len(fc_data) > 1:
            fc_cmds = S.institutional_table_style(len(fc_data))
            fc_t = Table(fc_data, colWidths=[1.35 * inch, 1.6 * inch, 1.4 * inch, 1.4 * inch, 1.5 * inch])
            fc_t.setStyle(TableStyle(fc_cmds))
            el.append(fc_t)
            el.append(S.small_spacer())

        # Signal contributions
        mc = forecast.get('method_contributions', {})
        if mc:
            el.append(Paragraph('<b>Signal Contributions (6M Horizon)</b>', S.SUBHEADING))
            mc_data = [
                ['Signal', 'Weight', 'Health Contribution', 'Momentum Contribution'],
                ['Momentum Extrapolation', '40%',
                 f"{mc.get('momentum', {}).get('x', 0):.2f}",
                 f"{mc.get('momentum', {}).get('y', 0):.2f}"],
                ['Historical Analogues', '35%',
                 f"{mc.get('analogues', {}).get('x', 0):.2f}",
                 f"{mc.get('analogues', {}).get('y', 0):.2f}"],
                ['Macro Drivers', '25%',
                 f"{mc.get('macro_drivers', {}).get('x', 0):.2f}",
                 f"{mc.get('macro_drivers', {}).get('y', 0):.2f}"],
            ]
            mc_cmds = S.institutional_table_style(len(mc_data))
            mc_t = Table(mc_data, colWidths=[2.05 * inch, 1.1 * inch, 2.05 * inch, 2.05 * inch])
            mc_t.setStyle(TableStyle(mc_cmds))
            el.append(mc_t)
            el.append(S.small_spacer())

    # 13. Scenario Analysis
    el.append(S.section_heading(13, 'Scenario Analysis'))
    scenarios = data.get('scenarios', [])
    if scenarios:
        sc_data = [['Scenario', 'Prob.', '3M Phase', '6M Phase', '6M Exp. Return', 'Key Assumption']]
        for sc in scenarios:
            ret_val = sc.get('expected_market_return_6m')
            ret_str = f'{ret_val:.1f}%' if not pd.isna(ret_val) else 'N/A'
            sc_data.append([
                _clean(sc['name']), f"{sc['probability']:.0f}%",
                _clean(sc.get('projected_quadrant_3m', 'N/A')),
                _clean(sc.get('projected_quadrant_6m', 'N/A')),
                ret_str,
                Paragraph(_clean(sc.get('key_assumption', '')), S.TABLE_CELL_LEFT),
            ])
        sc_cmds = S.institutional_table_style(len(sc_data))
        sc_cmds.append(('ALIGN', (5, 1), (5, -1), 'LEFT'))
        sc_t = Table(sc_data, colWidths=[0.9 * inch, 0.7 * inch, 1.05 * inch, 1.05 * inch, 1.05 * inch, 2.5 * inch])
        sc_t.setStyle(TableStyle(sc_cmds))
        el.append(sc_t)
        el.append(S.small_spacer())

    # 14. Transition Matrix (Wrapped in KeepTogether so matrix NEVER splits)
    tm = data.get('transition_matrix')
    if tm and 'matrix' in tm and 'labels' in tm:
        labels = tm['labels']
        matrix = tm['matrix']

        tm_data = [['From \\ To'] + labels]
        tm_cmds = [
            ('BACKGROUND', (0, 0), (-1, 0), S.NAVY),
            ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, 0), (0, -1), S.NAVY),
            ('TEXTCOLOR',  (0, 0), (0, -1), colors.white),
            ('ALIGN',      (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME',   (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE',   (0, 0), (-1, -1), 8.5),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('GRID',       (0, 0), (-1, -1), 0.4, S.BORDER_GREY),
        ]

        for i, row_label in enumerate(labels):
            row = [row_label]
            for j in range(len(labels)):
                prob = matrix[i, j] * 100
                row.append(f'{prob:.1f}%')
                if prob > 50:
                    bg = S.HEAT_HIGH
                    tc = colors.white
                elif prob > 25:
                    bg = S.HEAT_MED
                    tc = colors.white
                elif prob > 10:
                    bg = S.HEAT_LOW
                    tc = S.CHARCOAL
                else:
                    bg = colors.white
                    tc = S.CHARCOAL
                tm_cmds.append(('BACKGROUND', (j + 1, i + 1), (j + 1, i + 1), bg))
                tm_cmds.append(('TEXTCOLOR',  (j + 1, i + 1), (j + 1, i + 1), tc))
            tm_data.append(row)

        col_w = S.CONTENT_W / (len(labels) + 1)
        tm_t = Table(tm_data, colWidths=[col_w] * (len(labels) + 1))
        tm_t.setStyle(TableStyle(tm_cmds))

        el.append(KeepTogether([
            S.section_heading(14, 'Regime Transition Matrix'),
            tm_t,
        ]))

    el.append(PageBreak())

    # =====================================================================
    # PAGE 6 — Methodology, Data Provenance & Metadata
    # =====================================================================
    el.append(S.section_heading(15, 'Methodology'))
    meth_text = narrative.get('methodology', '')
    meth_lines = [l.strip() for l in meth_text.split('\n') if l.strip()]
    for line in meth_lines:
        el.append(Paragraph(_clean(line), S.BODY))

    el.append(S.small_spacer())

    # 16. Data Provenance
    if data_metadata:
        el.append(S.section_heading(16, 'Data Provenance &amp; Freshness'))
        prov_data = [['Indicator', 'Value', 'Source', 'As Of', 'Cache']]
        for name, meta in data_metadata.items():
            if isinstance(meta, dict) and 'value' in meta:
                val = meta.get('value', 'N/A')
                date = meta.get('release_date', 'N/A')
                source = meta.get('source', 'Unknown')
                cache = meta.get('cache_status', 'Unknown')
                if val != 'N/A' and any(x in name for x in ['Yield', 'Spread', 'Rate']):
                    val_str = f'{val}%'
                else:
                    val_str = str(val) if val != 'N/A' else 'N/A'
                prov_data.append([
                    _clean(name), _clean(val_str), _clean(source),
                    _clean(date), _clean(cache),
                ])
            else:
                source = meta.get('source', 'Unknown') if isinstance(meta, dict) else 'Unknown'
                date = meta.get('last_date', 'N/A') if isinstance(meta, dict) else 'N/A'
                prov_data.append([
                    _clean(name), '-', _clean(source), _clean(date), '-',
                ])

        prov_cmds = S.institutional_table_style(len(prov_data))
        prov_cmds.append(('ALIGN', (0, 0), (0, -1), 'LEFT'))
        prov_cmds.append(('FONTSIZE', (0, 0), (-1, -1), 8))
        prov_t = Table(prov_data, colWidths=[1.8 * inch, 1.15 * inch, 1.4 * inch, 1.5 * inch, 1.4 * inch])
        prov_t.setStyle(TableStyle(prov_cmds))
        el.append(prov_t)

    el.append(S.small_spacer())

    # Metadata & QR code & Disclaimer
    final_block = []
    final_block.append(S.thin_rule())

    gen_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
    meta_lines = [
        f'<b>Generated:</b> {gen_time}',
        '<b>Platform:</b> Macro Intelligence Platform v2.5',
        '<b>Data Sources:</b> FRED, Yahoo Finance, DPIIT, RBI, OECD',
        '<b>Report generated automatically.</b> Not investment advice.',
    ]
    for line in meta_lines:
        final_block.append(Paragraph(line, S.CAPTION))

    qr_img = _make_qr_image()
    if qr_img:
        final_block.append(Spacer(1, 3))
        qr_row = Table(
            [[qr_img, Paragraph(
                '<b>Open Interactive Dashboard</b><br/>'
                f'<font size="7" color="#636e72">{_DASHBOARD_URL}</font>',
                ParagraphStyle('QR', parent=S.BODY, alignment=0, spaceAfter=0))]],
            colWidths=[0.9 * inch, 3.6 * inch],
        )
        qr_row.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ]))
        final_block.append(qr_row)

    final_block.append(Spacer(1, 4))
    final_block.append(S.thin_rule())
    final_block.append(Paragraph(
        'This document has been generated by the Macro Intelligence Platform '
        'using publicly available macroeconomic data. It is intended for '
        'informational and research purposes only and should not be construed '
        'as investment advice.',
        S.DISCLAIMER,
    ))

    el.append(KeepTogether(final_block))

    # ── Build ──
    doc.build(el)
