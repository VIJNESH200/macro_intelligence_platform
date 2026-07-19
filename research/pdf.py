from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, BaseDocTemplate, PageTemplate, Frame
from reportlab.lib.units import inch
import pandas as pd
import numpy as np

# Colors
navy = colors.HexColor('#002b5e')
charcoal = colors.HexColor('#333333')
light_grey = colors.HexColor('#f8f9fa')
border_grey = colors.HexColor('#e9ecef')
highlight_bg = colors.HexColor('#e6f2ff')
highlight_text = colors.HexColor('#004085')

def header_footer(canvas, doc, data):
    canvas.saveState()
    canvas.setStrokeColor(navy)
    canvas.setLineWidth(1)
    canvas.line(45, letter[1] - 35, letter[0] - 45, letter[1] - 35)
    canvas.setStrokeColor(border_grey)
    canvas.line(45, 45, letter[0] - 45, 45)
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(charcoal)
    canvas.drawString(45, 30, "Macro Intelligence Platform | Institutional Strategy Note")
    page_num = canvas.getPageNumber()
    canvas.drawRightString(letter[0] - 45, 30, f"Page {page_num}")
    canvas.restoreState()

class InstitutionalDocTemplate(BaseDocTemplate):
    def __init__(self, filename, data, **kwargs):
        super().__init__(filename, **kwargs)
        self.data = data
        frame = Frame(45, 60, letter[0] - 90, letter[1] - 110, id='normal')
        template = PageTemplate(id='all_pages', frames=frame, onPage=self.on_page)
        self.addPageTemplates([template])
        
    def on_page(self, canvas, doc):
        header_footer(canvas, doc, self.data)

def format_delta(val, is_pct=False):
    if pd.isna(val): return "N/A"
    sign = "+" if val > 0 else ("" if val == 0 else "")
    fmt = f"{sign}{val:.1f}%" if is_pct else f"{sign}{val:.2f}"
    
    if val > 0:
        return Paragraph(f"<font color='#155724'>{fmt}</font>", ParagraphStyle('g', fontName='Helvetica', fontSize=9, alignment=1))
    elif val < 0:
        return Paragraph(f"<font color='#721c24'>{fmt}</font>", ParagraphStyle('r', fontName='Helvetica', fontSize=9, alignment=1))
    else:
        return Paragraph(fmt, ParagraphStyle('n', fontName='Helvetica', fontSize=9, alignment=1))

def build_pdf_report(data, analysis, insights, market_insights, narrative, analogues, deltas, 
                     chart_path, output_path, data_metadata=None):
    doc = InstitutionalDocTemplate(
        output_path,
        data,
        pagesize=letter,
        rightMargin=45, leftMargin=45,
        topMargin=55, bottomMargin=60
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('TitleStyle', fontName='Helvetica-Bold', fontSize=22, spaceAfter=14, textColor=navy)
    subtitle_style = ParagraphStyle('SubtitleStyle', fontName='Helvetica', fontSize=11, spaceAfter=28, textColor=colors.HexColor('#555555'))
    h1_style = ParagraphStyle('H1Style', fontName='Helvetica-Bold', fontSize=12, spaceBefore=24, spaceAfter=12, textColor=navy, borderPadding=(0, 0, 4, 0), borderColor=navy, borderWidth=1)
    body_style = ParagraphStyle('BodyStyle', fontName='Helvetica', fontSize=9.5, leading=14, spaceAfter=8, textColor=charcoal, alignment=4)
    bullet_style = ParagraphStyle('BulletStyle', fontName='Helvetica', fontSize=9.5, leading=14, spaceAfter=8, leftIndent=20, bulletIndent=10, textColor=charcoal)
    disclaimer_style = ParagraphStyle('DisclaimerStyle', fontName='Helvetica', fontSize=8, leading=10, spaceBefore=24, textColor=colors.HexColor('#888888'), alignment=1)
    
    elements = []
    
    # =========================================================================
    # PAGE 1: The Macro Thesis (The "Now")
    # =========================================================================
    elements.append(Paragraph("Macroeconomic Strategy Note", title_style))
    elements.append(Paragraph(f"Macro Intelligence Platform | {data['indicator']}", subtitle_style))
    
    meta_data = [
        [Paragraph("<b>Report Date:</b>", body_style), Paragraph(data['date'], body_style),
         Paragraph("<b>Source:</b>", body_style), Paragraph(data['source'], body_style)],
        [Paragraph("<b>Generated:</b>", body_style), Paragraph(data['timestamp'], body_style),
         Paragraph("<b>Window:</b>", body_style), Paragraph(data['window'], body_style)]
    ]
    meta_table = Table(meta_data, colWidths=[1.1*inch, 2.4*inch, 1.1*inch, 2.4*inch])
    meta_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LINEBELOW', (0,-1), (-1,-1), 1, border_grey),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 0.15*inch))
    
    # MACRO SNAPSHOT
    conf_score = data.get('macro_contrib', {}).get('confidence_score', 0)
    primary_risk = "None identified"
    if data.get('macro_contrib', {}).get('all_drivers'):
        drivers = data['macro_contrib']['all_drivers']
        worst_driver = min(drivers, key=lambda x: x['score'])
        if worst_driver['score'] < -0.5:
            primary_risk = f"{worst_driver['indicator']} {worst_driver['state'].lower()}"
            
    m_score = data.get('macro_contrib', {}).get('macro_score', 0)
    highest_prob_phase = max(analysis.get('transition_probs', {'Unknown': 0}).items(), key=lambda x: x[1])[0]
    
    conf_label = "Confidence:" if conf_score > 0 else "Data Coverage:"
    valid_count = len([d for d in data.get('macro_contrib', {}).get('all_drivers', []) if d.get('state') != 'Unknown'])
    conf_disp = f"{conf_score:.0f}%" if conf_score > 0 else f"{valid_count} of 5 indicators"
    
    snap_data = [
        [Paragraph("<b>Current Regime:</b>", body_style), Paragraph(data['quadrant'], body_style), Paragraph(f"<b>{conf_label}</b>", body_style), Paragraph(f"{conf_disp}<br/><font size=7 color='#666666'><i>{data.get('macro_contrib', {}).get('confidence_rationale', '')}</i></font>", body_style)],
        [Paragraph("<b>Macro Score:</b>", body_style), Paragraph(f"{m_score:+.2f}" if m_score is not None else "N/A", body_style), Paragraph("<b>Primary Risk:</b>", body_style), Paragraph(primary_risk, body_style)],
        [Paragraph("<b>Research View:</b>", body_style), Paragraph(data.get('macro_contrib', {}).get('macro_interpretation', 'Neutral'), body_style), Paragraph("<b>Next Likely Phase:</b><br/><font size=7 color='#666666'><i>(Historical Matrix)</i></font>", body_style), Paragraph(highest_prob_phase, body_style)]
    ]
    snap_table = Table(snap_data, colWidths=[1.5*inch, 2.0*inch, 1.5*inch, 2.0*inch])
    snap_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), light_grey), ('BOX', (0,0), (-1,-1), 1, navy),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(snap_table)
    elements.append(Spacer(1, 0.2*inch))

    
    # 1. Executive Summary & Takeaways
    elements.append(Paragraph("<font color='#888888'>1.</font> Executive Summary", h1_style))
    elements.append(Paragraph(narrative['executive_summary'], body_style))
    
    takeaways_data = [[Paragraph("<b>Key Takeaways</b>", ParagraphStyle('TK', parent=body_style, textColor=navy, fontSize=10.5))]]
    for tk in narrative['takeaways']:
        takeaways_data.append([Paragraph(f"<bullet>&bull;</bullet> {tk}", bullet_style)])
        
    tk_table = Table(takeaways_data, colWidths=[7.0*inch])
    tk_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), light_grey), ('BOX', (0,0), (-1,-1), 0.5, border_grey),
        ('TOPPADDING', (0,0), (-1,-1), 12), ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('LEFTPADDING', (0,0), (-1,-1), 12), ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    elements.append(tk_table)
    
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("<font size=7.5 color='#888888'><i>Immediate transition probabilities refer to the next business cycle phase. Historical analogues describe longer-term six-month outcomes.</i></font>", body_style))
    
    # 2. Business Cycle Visualization
    elements.append(Paragraph("<font color='#888888'>2.</font> Macroeconomic Positioning", h1_style))
    img = Image(chart_path)
    avail_width = 7.0 * inch
    aspect = img.imageHeight / float(img.imageWidth)
    img.drawWidth = avail_width
    img.drawHeight = avail_width * aspect
    elements.append(img)
    
    # 3. Research Dashboard
    elements.append(Paragraph("<font color='#888888'>3.</font> Research Dashboard", h1_style))
    
    def get_score_label(score):
        if score >= 80: return "Strongly Positive"
        if score >= 60: return "Positive"
        if score >= 40: return "Neutral"
        if score >= 20: return "Negative"
        return "Strongly Negative"

    sim_str = analogues['averages']['avg_sim_str'] if analogues and analogues.get('averages') else "N/A"
    m_score = data.get('macro_contrib', {}).get('macro_score')
    
    if m_score is not None:
        m_score_str = f"{m_score:+.2f}"
        m_interp = data.get('macro_contrib', {}).get('macro_interpretation', 'Neutral')
    else:
        m_score_str = "Unavailable"
        m_interp = "Insufficient Data"
        
    market_score = market_insights.get('market_score', 50)
    
    dash_data = [
        ['Macro Score', 'Market Score', 'Historical Similarity', 'Transition Risk'],
        [
            Paragraph(f"<b>{m_score_str}</b><br/><font size=8>{m_interp}</font>", ParagraphStyle('c', fontName='Helvetica-Bold', fontSize=14, alignment=1)),
            Paragraph(f"<b>{market_score:.0f}</b><br/><font size=8>{get_score_label(market_score)}</font>", ParagraphStyle('c', fontName='Helvetica-Bold', fontSize=14, alignment=1)),
            Paragraph(f"<b>{sim_str}</b>", ParagraphStyle('c', fontName='Helvetica-Bold', fontSize=14, alignment=1)),
            Paragraph(f"<b>{insights['highest_transition_prob']:.0f}%</b>", ParagraphStyle('c', fontName='Helvetica-Bold', fontSize=14, alignment=1))
        ]
    ]
    
    dash_table = Table(dash_data, colWidths=[1.75*inch, 1.75*inch, 1.75*inch, 1.75*inch])
    dash_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,0), (-1,0), navy), ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('FONTSIZE', (0,0), (-1,0), 9.5),
        ('BACKGROUND', (0,1), (-1,1), light_grey),
        ('TOPPADDING', (0,0), (-1,-1), 12), ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('LINEBELOW', (0,1), (-1,1), 1, border_grey)
    ]))
    elements.append(dash_table)
    
    elements.append(Spacer(1, 0.1*inch))
    
    # Key Metrics Delta Sub-table
    if deltas:
        km_data = [
            ['Key Metrics', 'Previous', 'Current', 'Change'],
            ['Phase', deltas['prev_phase'], data['quadrant'], ""],
            ['Economic Health', f"{deltas['prev_health']:.2f}", f"{data['health_val']:.2f}", format_delta(deltas['health_delta'])],
            ['Economic Momentum', f"{deltas['prev_momentum']:.2f}", f"{data['momentum_val']:.2f}", format_delta(deltas['momentum_delta'])],
            ['Transition Probability', f"{deltas['prev_transition_prob']:.0f}%", f"{insights['highest_transition_prob']:.0f}%", format_delta(deltas['prob_delta'], True)]
        ]
        km_table = Table(km_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        km_style = [
            ('ALIGN', (0,0), (0,-1), 'LEFT'), ('ALIGN', (1,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('FONTSIZE', (0,0), (-1,-1), 9),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8), ('TOPPADDING', (0,0), (-1,-1), 8),
            ('LINEBELOW', (0,0), (-1,-1), 0.5, border_grey)
        ]
        for i in range(1, len(km_data)):
            if i % 2 == 1: km_style.append(('BACKGROUND', (0,i), (-1,i), light_grey))
        km_table.setStyle(TableStyle(km_style))
        elements.append(km_table)
        
    elements.append(PageBreak())
    
    # =========================================================================
    # PAGE 2: Macro Drivers & What Changed
    # =========================================================================
    elements.append(Paragraph("<font color='#888888'>4.</font> Quantitative Macro Drivers", h1_style))
    
    if data.get('macro_contrib') and data['macro_contrib'].get('all_drivers'):
        mc = data['macro_contrib']
        evals = mc.get('evaluations', {})
        
        md_data = [['Indicator', 'Raw (Percentile)', 'Level', 'Trend', 'Impact']]
        md_style = [
            ('BACKGROUND', (0,0), (-1,0), navy), ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (0,-1), 'LEFT'), ('ALIGN', (1,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 9), ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 8), ('LINEBELOW', (0,0), (-1,-1), 0.5, border_grey),
        ]
        
        row_idx = 1
        for d in mc['all_drivers']:
            name = d['indicator']
            ev = evals.get(name, {})
            
            raw_val = ev.get('raw_value', np.nan)
            yoy_val = ev.get('yoy_value', np.nan)
            pct_str = ev.get('percentile', 'N/A')
            level_str = ev.get('level', d['state'])
            trend_str = ev.get('trend', 'N/A')
            
            signal_color = colors.HexColor('#155724') if level_str == 'Positive' else (colors.HexColor('#721c24') if level_str == 'Negative' else colors.HexColor('#856404'))
            
            if pd.isna(raw_val):
                raw_disp = "N/A"
            elif not pd.isna(yoy_val):
                raw_disp = f"{yoy_val:.2f}%\n({pct_str})"
            elif name in ['Yield 10Y', 'Yield Short', 'Yield Spread', 'Real Policy Rate']:
                raw_disp = f"{raw_val:.2f}%\n({pct_str})"
            else:
                raw_disp = f"{raw_val:.2f}\n({pct_str})"
                
            sign = "+" if d['score'] > 0 else ""
            
            md_data.append([name, raw_disp, f"{d['symbol']} {level_str}", trend_str, f"{sign}{d['score']:.2f}"])
            md_style.append(('TEXTCOLOR', (2,row_idx), (2,row_idx), signal_color))
            if row_idx % 2 == 1: md_style.append(('BACKGROUND', (0,row_idx), (-1,row_idx), light_grey))
            row_idx += 1
            
        md_table = Table(md_data, colWidths=[1.6*inch, 1.4*inch, 1.2*inch, 1.2*inch, 1.0*inch])
        md_table.setStyle(TableStyle(md_style))
        elements.append(md_table)
        elements.append(Spacer(1, 0.2*inch))
    else:
        elements.append(Paragraph("Macro Driver data unavailable.", body_style))
        elements.append(Spacer(1, 0.2*inch))

    # 5. Key Regime Developments
    elements.append(Paragraph("<font color='#888888'>5.</font> Key Regime Developments", h1_style))
    shifts = data.get('macro_shifts', [])
    if shifts:
        for s in shifts:
            elements.append(Paragraph(f"<bullet>&bull;</bullet> {s}", bullet_style))
    else:
        elements.append(Paragraph("No major structural regime shifts detected this month.", body_style))
    elements.append(Spacer(1, 0.15*inch))
        
    # 6. Research Insights
    elements.append(Paragraph("<font color='#888888'>6.</font> Research Insights", h1_style))
    narrative_list = data.get('research_narrative', [])
    if isinstance(narrative_list, list) and narrative_list:
        for item in narrative_list:
            elements.append(Paragraph(f"<b>Observation:</b> {item.get('observation', '')}", body_style))
            elements.append(Paragraph(f"<b>Evidence:</b> {item.get('evidence', '')}", body_style))
            elements.append(Paragraph(f"<b>Interpretation:</b> {item.get('interpretation', '')}", body_style))
            elements.append(Paragraph(f"<b>Implication:</b> {item.get('implication', '')}", body_style))
            elements.append(Spacer(1, 0.1*inch))
    else:
        elements.append(Paragraph(str(narrative_list), body_style))
        
    elements.append(Spacer(1, 0.2*inch))
    
    # 7. Cycle Timeline & Transition Outlook
    elements.append(Paragraph("<font color='#888888'>7.</font> Cycle Timeline & Transition Outlook", h1_style))
    c_d = Paragraph(f"<b>{analysis.get('current_duration', 'N/A')}</b>", ParagraphStyle('HI', parent=body_style, textColor=highlight_text))
    p_pct = Paragraph(f"<b>{analysis.get('completion_pct', 0):.0f}%</b> of historical average", ParagraphStyle('HI', parent=body_style, textColor=highlight_text))
    
    t_probs = analysis.get('transition_probs', {})
    t_dash_data = []
    if t_probs:
        for ph, prob in t_probs.items():
            blocks = int(prob / 10)
            bar = '█' * blocks
            t_dash_data.append([
                Paragraph(f"<b>{ph}</b>", body_style),
                Paragraph(f"<font color='#002b5e'>{bar}</font> {prob:.0f}%", body_style)
            ])
        t_dash_data.append([Paragraph("<font size=8 color='#888888'><i>Conditional probabilities based on historical transitions from the current phase.</i></font>", body_style), ""])
    else:
        t_dash_data = [["N/A", "N/A"]]
        
    t_table = Table(t_dash_data, colWidths=[1.8*inch, 1.7*inch])
    t_style = [('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('TOPPADDING', (0,0), (-1,-1), 1), ('BOTTOMPADDING', (0,0), (-1,-1), 1)]
    if t_probs:
        last_row = len(t_dash_data) - 1
        t_style.append(('SPAN', (0,last_row), (1,last_row)))
        t_style.append(('TOPPADDING', (0,last_row), (1,last_row), 6))
    t_table.setStyle(TableStyle(t_style))
    
    hist_data = [
        ['Current Phase Duration', c_d],
        ['Phase Completion', p_pct],
        ['Average Phase Duration', f"{analysis.get('avg_duration', 'N/A')}"],
        ['Longest Historical Duration', f"{analysis.get('longest_duration', 'N/A')}"],
        ['Total Historical Occurrences', str(analysis.get('occurrences', 'N/A'))],
        ['Historical Next-Phase Probabilities', t_table],
    ]
    hist_table = Table(hist_data, colWidths=[3.5*inch, 3.5*inch])
    hist_style = [
        ('TEXTCOLOR', (0,0), (-1,-1), charcoal), ('ALIGN', (0,0), (-1,-1), 'LEFT'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'), ('FONTSIZE', (0,0), (-1,-1), 9),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8), ('TOPPADDING', (0,0), (-1,-1), 8),
        ('LINEABOVE', (0,0), (-1,0), 0.5, border_grey), ('LINEBELOW', (0,0), (-1,-1), 0.5, border_grey),
        ('BACKGROUND', (1,0), (1,0), highlight_bg), ('BACKGROUND', (1,1), (1,1), highlight_bg),
    ]
    for i in range(1, len(hist_data)):
        if i % 2 == 1:
            hist_style.append(('BACKGROUND', (0,i), (0,i), light_grey))
            if i != 5: 
                hist_style.append(('BACKGROUND', (1,i), (1,i), light_grey))
    hist_table.setStyle(TableStyle(hist_style))
    elements.append(hist_table)
    
    elements.append(PageBreak())
    
    # =========================================================================
    # PAGE 3: Historical Validation
    # =========================================================================
    # 8. Historical Analogues
    elements.append(Paragraph("<font color='#888888'>8.</font> Historical Analogues", h1_style))
    elements.append(Paragraph("Most statistically similar historical macro environments.", body_style))
    elements.append(Spacer(1, 0.1*inch))
    
    if analogues and analogues.get('matches'):
        matches = analogues['matches']
        averages = analogues['averages']
        
        ana_data = [['Historical Period', 'Similarity', 'Phase Duration', 'Next Phase', f"6M Fwd ({matches[0]['benchmark_name']})"]]
        ana_style = [
            ('BACKGROUND', (0,0), (-1,0), navy), ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('FONTSIZE', (0,0), (-1,-1), 9),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8), ('TOPPADDING', (0,0), (-1,-1), 8),
            ('LINEBELOW', (0,0), (-1,-1), 0.5, border_grey),
        ]
        
        for i, a in enumerate(matches, start=1):
            row = [a['date_str'], a['similarity_str'], a['duration'], a['next_phase'], a['fwd_ret']]
            ana_data.append(row)
            if i % 2 == 1:
                ana_style.append(('BACKGROUND', (0,i), (-1,i), light_grey))
                
            val = a['fwd_ret_val']
            if not pd.isna(val):
                if val > 5:
                    ana_style.append(('BACKGROUND', (4,i), (4,i), colors.HexColor('#d4edda')))
                    ana_style.append(('TEXTCOLOR', (4,i), (4,i), colors.HexColor('#155724')))
                elif val > 0:
                    ana_style.append(('BACKGROUND', (4,i), (4,i), colors.HexColor('#e8f5e9')))
                    ana_style.append(('TEXTCOLOR', (4,i), (4,i), colors.HexColor('#155724')))
                elif val < -5:
                    ana_style.append(('BACKGROUND', (4,i), (4,i), colors.HexColor('#f8d7da')))
                    ana_style.append(('TEXTCOLOR', (4,i), (4,i), colors.HexColor('#721c24')))
                elif val < 0:
                    ana_style.append(('BACKGROUND', (4,i), (4,i), colors.HexColor('#ffebee')))
                    ana_style.append(('TEXTCOLOR', (4,i), (4,i), colors.HexColor('#721c24')))
                    
        # Add Averages Row
        avg_row = [
            "AVERAGE",
            averages['avg_sim_str'],
            averages['avg_dur_str'],
            averages['most_common_next'],
            averages['avg_fwd_str']
        ]
        ana_data.append(avg_row)
        last_idx = len(ana_data) - 1
        ana_style.append(('BACKGROUND', (0,last_idx), (-1,last_idx), colors.HexColor('#001b3e')))
        ana_style.append(('TEXTCOLOR', (0,last_idx), (-1,last_idx), colors.white))
        ana_style.append(('FONTNAME', (0,last_idx), (-1,last_idx), 'Helvetica-Bold'))
        ana_style.append(('TOPPADDING', (0,last_idx), (-1,last_idx), 12))
        ana_style.append(('BOTTOMPADDING', (0,last_idx), (-1,last_idx), 12))
        
        avg_val = averages['avg_fwd_val']
        if not pd.isna(avg_val):
            if avg_val > 5:
                ana_style.append(('BACKGROUND', (4,last_idx), (4,last_idx), colors.HexColor('#155724'))) # Dark Green
            elif avg_val > 0:
                ana_style.append(('BACKGROUND', (4,last_idx), (4,last_idx), colors.HexColor('#28a745'))) # Green
            elif avg_val < -5:
                ana_style.append(('BACKGROUND', (4,last_idx), (4,last_idx), colors.HexColor('#721c24'))) # Dark Red
            elif avg_val < 0:
                ana_style.append(('BACKGROUND', (4,last_idx), (4,last_idx), colors.HexColor('#dc3545'))) # Red
        
        ana_table = Table(ana_data, colWidths=[1.5*inch, 1.2*inch, 1.4*inch, 1.4*inch, 1.5*inch])
        ana_table.setStyle(TableStyle(ana_style))
        elements.append(ana_table)
    else:
        elements.append(Paragraph("Insufficient historical data to compute mathematical analogues.", body_style))
        
    # =========================================================================
    # PAGE 4: Investment Implications (The "So What")
    # =========================================================================
    
    # 9. Cross-Market Context
    elements.append(Paragraph("<font color='#888888'>9.</font> Cross-Market Context", h1_style))
    if data['market_data']:
        mkt_table_data = [['Asset / Series', 'Current Value', '1M', '3M', '6M', '12M']]
        mkt_style = [
            ('BACKGROUND', (0,0), (-1,0), navy), ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (0,-1), 'LEFT'), ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 9), ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 8), ('LINEBELOW', (0,0), (-1,-1), 0.5, border_grey),
        ]
        
        for i, asset in enumerate(data['market_data'], start=1):
            row = [
                asset['name'], asset['current_val_str'],
                asset['returns_str'].get('1M', 'N/A'), asset['returns_str'].get('3M', 'N/A'),
                asset['returns_str'].get('6M', 'N/A'), asset['returns_str'].get('12M', 'N/A')
            ]
            mkt_table_data.append(row)
            if i % 2 == 1:
                mkt_style.append(('BACKGROUND', (0,i), (1,i), light_grey))
                
            horizons = ['1M', '3M', '6M', '12M']
            for j, h in enumerate(horizons, start=2):
                val = asset['returns_raw'].get(h)
                if val is None or pd.isna(val): continue
                if val > 5:
                    bg_color, txt_color = colors.HexColor('#d4edda'), colors.HexColor('#155724')
                elif val > 0:
                    bg_color, txt_color = colors.HexColor('#e8f5e9'), colors.HexColor('#155724')
                elif val < -5:
                    bg_color, txt_color = colors.HexColor('#f8d7da'), colors.HexColor('#721c24')
                elif val < 0:
                    bg_color, txt_color = colors.HexColor('#ffebee'), colors.HexColor('#721c24')
                else:
                    bg_color, txt_color = colors.white, charcoal
                mkt_style.append(('BACKGROUND', (j,i), (j,i), bg_color))
                mkt_style.append(('TEXTCOLOR', (j,i), (j,i), txt_color))
                
        mkt_table = Table(mkt_table_data, colWidths=[2.0*inch, 1.3*inch, 0.925*inch, 0.925*inch, 0.925*inch, 0.925*inch])
        mkt_table.setStyle(TableStyle(mkt_style))
        elements.append(mkt_table)
            
    elements.append(PageBreak())
    
    # 10. Integrated Market Interpretation
    elements.append(Paragraph("<font color='#888888'>10.</font> Integrated Market Interpretation", h1_style))
    elements.append(Paragraph(narrative['interpretation'], body_style))
    
    # 11. Core Macro Risks
    elements.append(Paragraph("<font color='#888888'>11.</font> Core Macro Risks", h1_style))
    for r in narrative['risks']:
        elements.append(Paragraph(f"<bullet>&bull;</bullet> {r}", bullet_style))
        
    # =========================================================================
    # PAGE 5: Forward Projections & Scenarios
    # =========================================================================
    elements.append(PageBreak())

    # 12. Forward Outlook
    elements.append(Paragraph("<font color='#888888'>12.</font> Forward Outlook", h1_style))
    forecast = data.get('forecast')
    if forecast and 'forecast_3m' in forecast and 'forecast_6m' in forecast:
        f3m = forecast['forecast_3m']
        f6m = forecast['forecast_6m']
        
        fc_data = [
            ['Horizon', 'Proj. Phase', 'Conviction', 'Health (X)', 'Momentum (Y)'],
            ['3-Month', f3m['quadrant'], f"{f3m.get('conviction', 0):.1f}%", f"{f3m['x']:.2f}", f"{f3m['y']:.2f}"],
            ['6-Month', f6m['quadrant'], f"{f6m.get('conviction', 0):.1f}%", f"{f6m['x']:.2f}", f"{f6m['y']:.2f}"]
        ]
        fc_table = Table(fc_data, colWidths=[1.2*inch, 1.5*inch, 1.3*inch, 1.2*inch, 1.2*inch])
        fc_style = [
            ('BACKGROUND', (0,0), (-1,0), navy), ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('FONTSIZE', (0,0), (-1,-1), 9),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8), ('TOPPADDING', (0,0), (-1,-1), 8),
            ('LINEBELOW', (0,0), (-1,-1), 0.5, border_grey),
            ('BACKGROUND', (0,1), (-1,1), light_grey),
        ]
        fc_table.setStyle(TableStyle(fc_style))
        elements.append(fc_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Method Contributions
        elements.append(Paragraph("<b>Signal Contributions (6M Horizon)</b>", body_style))
        mc = forecast.get('method_contributions', {})
        if mc:
            mc_data = [
                ['Signal', 'Weight', 'Health Contribution', 'Momentum Contribution'],
                ['Momentum Extrapolation', '40%', f"{mc.get('momentum', {}).get('x', 0):.2f}", f"{mc.get('momentum', {}).get('y', 0):.2f}"],
                ['Historical Analogues', '35%', f"{mc.get('analogues', {}).get('x', 0):.2f}", f"{mc.get('analogues', {}).get('y', 0):.2f}"],
                ['Macro Drivers', '25%', f"{mc.get('macro_drivers', {}).get('x', 0):.2f}", f"{mc.get('macro_drivers', {}).get('y', 0):.2f}"]
            ]
            mc_table = Table(mc_data, colWidths=[1.8*inch, 1.0*inch, 1.6*inch, 1.6*inch])
            mc_table.setStyle(TableStyle([
                ('TEXTCOLOR', (0,0), (-1,0), charcoal), ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('FONTSIZE', (0,0), (-1,-1), 8),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6), ('TOPPADDING', (0,0), (-1,-1), 6),
                ('LINEABOVE', (0,0), (-1,0), 0.5, border_grey), ('LINEBELOW', (0,0), (-1,-1), 0.5, border_grey),
            ]))
            elements.append(mc_table)
            elements.append(Spacer(1, 0.2*inch))
    else:
        elements.append(Paragraph("Forecasting data unavailable.", body_style))
        elements.append(Spacer(1, 0.2*inch))

    # 13. Scenario Analysis
    elements.append(Paragraph("<font color='#888888'>13.</font> Scenario Analysis", h1_style))
    scenarios = data.get('scenarios', [])
    if scenarios:
        sc_data = [['Scenario', 'Prob.', '3M Phase', '6M Phase', '6M Exp. Return', 'Key Assumption']]
        sc_style = [
            ('BACKGROUND', (0,0), (-1,0), navy), ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('FONTSIZE', (0,0), (-1,-1), 9),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8), ('TOPPADDING', (0,0), (-1,-1), 8),
            ('LINEBELOW', (0,0), (-1,-1), 0.5, border_grey),
            ('ALIGN', (5,1), (5,-1), 'LEFT'), # Key assumption left-aligned
        ]
        
        for i, sc in enumerate(scenarios, start=1):
            ret_val = sc.get('expected_market_return_6m')
            ret_str = f"{ret_val:.1f}%" if not pd.isna(ret_val) else "N/A"
            row = [
                sc['name'],
                f"{sc['probability']:.0f}%",
                sc.get('projected_quadrant_3m', 'N/A'),
                sc.get('projected_quadrant_6m', 'N/A'),
                ret_str,
                Paragraph(sc.get('key_assumption', ''), body_style)
            ]
            sc_data.append(row)
            if i % 2 == 1:
                sc_style.append(('BACKGROUND', (0,i), (-1,i), light_grey))
                
        sc_table = Table(sc_data, colWidths=[0.8*inch, 0.7*inch, 1.0*inch, 1.0*inch, 1.0*inch, 2.5*inch])
        sc_table.setStyle(TableStyle(sc_style))
        elements.append(sc_table)
        elements.append(Spacer(1, 0.2*inch))
    else:
        elements.append(Paragraph("Scenario analysis data unavailable.", body_style))
        elements.append(Spacer(1, 0.2*inch))

    # 14. Regime Transition Matrix
    elements.append(Paragraph("<font color='#888888'>14.</font> Regime Transition Matrix", h1_style))
    tm = data.get('transition_matrix')
    if tm and 'matrix' in tm and 'labels' in tm:
        labels = tm['labels']
        matrix = tm['matrix']
        
        tm_data = [['From \\ To'] + labels]
        tm_style = [
            ('BACKGROUND', (0,0), (-1,0), navy), ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('BACKGROUND', (0,0), (0,-1), navy), ('TEXTCOLOR', (0,0), (0,-1), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'), ('FONTSIZE', (0,0), (-1,-1), 9),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8), ('TOPPADDING', (0,0), (-1,-1), 8),
            ('GRID', (0,0), (-1,-1), 0.5, border_grey),
        ]
        
        for i, row_label in enumerate(labels):
            row_data = [row_label]
            for j, col_label in enumerate(labels):
                prob = matrix[i, j] * 100
                row_data.append(f"{prob:.1f}%")
                
                # Color code cells based on probability
                if prob > 50: bg = colors.HexColor('#28a745')
                elif prob > 25: bg = colors.HexColor('#d4edda')
                elif prob > 10: bg = colors.HexColor('#fff3cd')
                else: bg = colors.white
                
                tm_style.append(('BACKGROUND', (j+1, i+1), (j+1, i+1), bg))
                if prob > 50:
                    tm_style.append(('TEXTCOLOR', (j+1, i+1), (j+1, i+1), colors.white))
                else:
                    tm_style.append(('TEXTCOLOR', (j+1, i+1), (j+1, i+1), charcoal))
                    
            tm_data.append(row_data)
            
        tm_table = Table(tm_data, colWidths=[1.4*inch, 1.4*inch, 1.4*inch, 1.4*inch, 1.4*inch])
        tm_table.setStyle(TableStyle(tm_style))
        elements.append(tm_table)
    else:
        elements.append(Paragraph("Transition matrix data unavailable.", body_style))
        
    elements.append(PageBreak())
        
    # 15. Methodology & Disclaimers
    elements.append(Paragraph("<font color='#888888'>15.</font> Methodology", h1_style))
    elements.append(Paragraph(narrative['methodology'], body_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # 16. Data Provenance & Freshness
    if data_metadata:
        elements.append(Paragraph("<font color='#888888'>16.</font> Data Provenance & Freshness", h1_style))
        prov_text = ""
        for name, meta in data_metadata.items():
            if isinstance(meta, dict) and 'value' in meta:
                val = meta.get('value', 'N/A')
                date = meta.get('release_date', 'N/A')
                source = meta.get('source', 'Unknown')
                cache = meta.get('cache_status', 'Unknown')
                
                # Format value string depending on indicator
                if val != 'N/A':
                    val_str = f"{val}%" if any(x in name for x in ['Yield', 'Spread', 'Rate']) else str(val)
                else:
                    val_str = 'N/A'
                    
                prov_text += f"<b>{name}</b>: {val_str} | {source} (As of {date}) [{cache}]<br/>"
            else:
                # Fallback for old cache structure just in case
                source = meta.get('source', 'Unknown') if isinstance(meta, dict) else 'Unknown'
                date = meta.get('last_date', 'N/A') if isinstance(meta, dict) else 'N/A'
                prov_text += f"<b>{name}</b>: {source} (As of {date})<br/>"
        elements.append(Paragraph(prov_text, body_style))
    
    disclaimer_text = (
        "This document has been generated by the Macro Intelligence Platform using publicly available "
        "macroeconomic data. It is intended for informational and research purposes only and should not be construed "
        "as investment advice."
    )
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph(disclaimer_text, disclaimer_style))
    
    doc.build(elements)
