"""
Institutional PDF Design System
===============================
Centralised colors, typography, table presets, and layout constants for
the Macro Intelligence Platform's publication-quality PDF reports.

All visual tokens live here so ``pdf.py`` never contains ad-hoc colours
or font sizes. Change one value and every page updates.
"""
from __future__ import annotations

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph, Spacer, Table, TableStyle, HRFlowable,
)

# ─── Page geometry ────────────────────────────────────────────────────────────
PAGE_W, PAGE_H = letter                          # 612 × 792 pt
MARGIN_L   = 45
MARGIN_R   = 45
MARGIN_T   = 45
MARGIN_B   = 50
CONTENT_W  = PAGE_W - MARGIN_L - MARGIN_R        # 522 pt ≈ 7.25 in
CONTENT_H  = PAGE_H - MARGIN_T - MARGIN_B        # 697 pt
FOOTER_Y   = 28                                   # baseline for running footer

# ─── Colour palette ──────────────────────────────────────────────────────────
# Primary
NAVY           = colors.HexColor('#0a1628')
NAVY_ACCENT    = colors.HexColor('#1a3a5c')
CHARCOAL       = colors.HexColor('#2d3436')
MID_GREY       = colors.HexColor('#636e72')

# Surfaces
LIGHT_GREY     = colors.HexColor('#f5f6fa')
SURFACE_ALT    = colors.HexColor('#fafbfc')
BORDER_GREY    = colors.HexColor('#dfe6e9')
RULE_LIGHT     = colors.HexColor('#e8eaed')

# Highlights
HIGHLIGHT_BG   = colors.HexColor('#edf2f7')
HIGHLIGHT_TEXT = colors.HexColor('#1a365d')
CALLOUT_BG     = colors.HexColor('#f0f4f8')

# Signal colours
GREEN_STRONG   = colors.HexColor('#155724')
GREEN_LIGHT_BG = colors.HexColor('#e8f5e9')
GREEN_MED_BG   = colors.HexColor('#d4edda')
RED_STRONG     = colors.HexColor('#721c24')
RED_LIGHT_BG   = colors.HexColor('#ffebee')
RED_MED_BG     = colors.HexColor('#f8d7da')
AMBER_TEXT     = colors.HexColor('#856404')
AMBER_BG       = colors.HexColor('#fff3cd')

# Deep highlight for average / summary rows
DEEP_NAVY      = colors.HexColor('#001b3e')

# Transition-matrix heat-map tones
HEAT_HIGH      = colors.HexColor('#1a5276')
HEAT_MED       = colors.HexColor('#5dade2')
HEAT_LOW       = colors.HexColor('#d6eaf8')

# ─── Spacing tokens ──────────────────────────────────────────────────────────
SECTION_GAP       = 12       # vertical space before section headings
SUBSECTION_GAP    = 6
TABLE_GAP         = 6
PARAGRAPH_GAP     = 4
CARD_PAD_H        = 8        # horizontal padding inside cards
CARD_PAD_V        = 5        # vertical padding inside cards
TABLE_CELL_PAD_V  = 4        # vertical padding in table cells
TABLE_CELL_PAD_H  = 5

# ─── Typography hierarchy ────────────────────────────────────────────────────
REPORT_TITLE = ParagraphStyle(
    'ReportTitle',
    fontName='Helvetica-Bold', fontSize=22, leading=26,
    textColor=NAVY, spaceAfter=2,
)

SECTION_HEADING = ParagraphStyle(
    'SectionHeading',
    fontName='Helvetica-Bold', fontSize=11.5, leading=14,
    textColor=NAVY, spaceBefore=SECTION_GAP, spaceAfter=6,
)

SUBHEADING = ParagraphStyle(
    'Subheading',
    fontName='Helvetica-Bold', fontSize=9.5, leading=12,
    textColor=NAVY_ACCENT, spaceBefore=6, spaceAfter=4,
)

BODY = ParagraphStyle(
    'Body',
    fontName='Helvetica', fontSize=9, leading=13,
    textColor=CHARCOAL, spaceAfter=PARAGRAPH_GAP, alignment=4,  # justified
)

BODY_CENTER = ParagraphStyle(
    'BodyCenter',
    fontName='Helvetica', fontSize=9, leading=13,
    textColor=CHARCOAL, spaceAfter=PARAGRAPH_GAP, alignment=1,
)

BULLET = ParagraphStyle(
    'Bullet',
    fontName='Helvetica', fontSize=8.5, leading=12,
    textColor=CHARCOAL, spaceAfter=3,
    leftIndent=14, bulletIndent=6,
)

CAPTION = ParagraphStyle(
    'Caption',
    fontName='Helvetica', fontSize=8, leading=10,
    textColor=MID_GREY, spaceBefore=2, spaceAfter=4, alignment=1,
)

FOOTER_STYLE = ParagraphStyle(
    'Footer',
    fontName='Helvetica', fontSize=7.5, leading=10,
    textColor=MID_GREY,
)

DISCLAIMER = ParagraphStyle(
    'Disclaimer',
    fontName='Helvetica-Oblique', fontSize=7.5, leading=10,
    textColor=MID_GREY, spaceBefore=6, alignment=1,
)

TABLE_HEADER_TEXT = ParagraphStyle(
    'TableHeaderText',
    fontName='Helvetica-Bold', fontSize=8.5, leading=11,
    textColor=colors.white, alignment=1,
)

TABLE_CELL_TEXT = ParagraphStyle(
    'TableCellText',
    fontName='Helvetica', fontSize=8.5, leading=11,
    textColor=CHARCOAL, alignment=1,
)

TABLE_CELL_LEFT = ParagraphStyle(
    'TableCellLeft',
    fontName='Helvetica', fontSize=8.5, leading=11,
    textColor=CHARCOAL, alignment=0,
)

KPI_VALUE = ParagraphStyle(
    'KPIValue',
    fontName='Helvetica-Bold', fontSize=15, leading=18,
    textColor=NAVY, alignment=1,
)

KPI_LABEL = ParagraphStyle(
    'KPILabel',
    fontName='Helvetica', fontSize=8, leading=10,
    textColor=MID_GREY, alignment=1, spaceAfter=2,
)

KPI_SUBLABEL = ParagraphStyle(
    'KPISublabel',
    fontName='Helvetica', fontSize=7.5, leading=9,
    textColor=MID_GREY, alignment=1,
)

METADATA_LABEL = ParagraphStyle(
    'MetadataLabel',
    fontName='Helvetica-Bold', fontSize=8, leading=11,
    textColor=MID_GREY,
)

METADATA_VALUE = ParagraphStyle(
    'MetadataValue',
    fontName='Helvetica', fontSize=8, leading=11,
    textColor=CHARCOAL,
)

# ─── Reusable table style factories ──────────────────────────────────────────

def institutional_table_style(n_rows: int, *, has_header: bool = True) -> list:
    """Base style commands for a clean institutional table.

    Returns a *list* of commands suitable for ``TableStyle(commands)``.
    """
    cmds = [
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME',      (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE',      (0, 0), (-1, -1), 8.5),
        ('TOPPADDING',    (0, 0), (-1, -1), TABLE_CELL_PAD_V),
        ('BOTTOMPADDING', (0, 0), (-1, -1), TABLE_CELL_PAD_V),
        ('LEFTPADDING',   (0, 0), (-1, -1), TABLE_CELL_PAD_H),
        ('RIGHTPADDING',  (0, 0), (-1, -1), TABLE_CELL_PAD_H),
        ('LINEBELOW',     (0, 0), (-1, -1), 0.4, BORDER_GREY),
    ]
    if has_header:
        cmds += [
            ('BACKGROUND',    (0, 0), (-1, 0), NAVY),
            ('TEXTCOLOR',     (0, 0), (-1, 0), colors.white),
            ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, 0), 8.5),
            ('TOPPADDING',    (0, 0), (-1, 0), 6),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ]
    # Alternating row shading (skip header row)
    start = 1 if has_header else 0
    for i in range(start, n_rows):
        if (i - start) % 2 == 1:
            cmds.append(('BACKGROUND', (0, i), (-1, i), LIGHT_GREY))
    return cmds


def summary_row_style(row_idx: int) -> list:
    """Style commands for a dark summary / average row."""
    return [
        ('BACKGROUND', (0, row_idx), (-1, row_idx), DEEP_NAVY),
        ('TEXTCOLOR',  (0, row_idx), (-1, row_idx), colors.white),
        ('FONTNAME',   (0, row_idx), (-1, row_idx), 'Helvetica-Bold'),
        ('TOPPADDING', (0, row_idx), (-1, row_idx), 6),
        ('BOTTOMPADDING', (0, row_idx), (-1, row_idx), 6),
    ]


# ─── Reusable flowable helpers ───────────────────────────────────────────────

def section_heading(number: int | str, title: str) -> Paragraph:
    """Numbered section heading with muted number prefix."""
    return Paragraph(
        f'<font color="#9eaab5" size="10">{number}.</font>&nbsp;&nbsp;{title}',
        SECTION_HEADING,
    )


def thin_rule() -> HRFlowable:
    """Thin horizontal divider line."""
    return HRFlowable(
        width='100%', thickness=0.5,
        color=RULE_LIGHT, spaceBefore=4, spaceAfter=4,
    )


def section_spacer() -> Spacer:
    """Standard gap between major sections."""
    return Spacer(1, SECTION_GAP)


def small_spacer() -> Spacer:
    """Small gap within a section."""
    return Spacer(1, SUBSECTION_GAP)


def kpi_card(label: str, value: str, sublabel: str = '') -> Table:
    """Single KPI metric in a bordered card suitable for a horizontal strip."""
    cell_data = [
        [Paragraph(label, KPI_LABEL)],
        [Paragraph(value, KPI_VALUE)],
    ]
    if sublabel:
        cell_data.append([Paragraph(sublabel, KPI_SUBLABEL)])
    card = Table(cell_data, colWidths=[CONTENT_W / 4 - 5])
    card.setStyle(TableStyle([
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), CARD_PAD_V),
        ('BOTTOMPADDING', (0, 0), (-1, -1), CARD_PAD_V),
        ('BOX',           (0, 0), (-1, -1), 0.5, BORDER_GREY),
        ('BACKGROUND',    (0, 0), (-1, -1), SURFACE_ALT),
    ]))
    return card


def return_color(val: float | None) -> tuple:
    """(bg_color, text_color) for a return value cell."""
    if val is None:
        return (colors.white, CHARCOAL)
    try:
        from math import isnan
        if isnan(val):
            return (colors.white, CHARCOAL)
    except (TypeError, ValueError):
        return (colors.white, CHARCOAL)

    if val > 5:
        return (GREEN_MED_BG, GREEN_STRONG)
    if val > 0:
        return (GREEN_LIGHT_BG, GREEN_STRONG)
    if val < -5:
        return (RED_MED_BG, RED_STRONG)
    if val < 0:
        return (RED_LIGHT_BG, RED_STRONG)
    return (colors.white, CHARCOAL)


def signal_text_color(level: str) -> colors.HexColor:
    """Text color for a macro-driver signal level."""
    level_lower = (level or '').lower()
    if level_lower == 'positive':
        return GREEN_STRONG
    if level_lower == 'negative':
        return RED_STRONG
    return AMBER_TEXT
