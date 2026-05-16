# ============================================================
# app/reports/pdf_generator.py  —  ReportLab PDF Generation
# ============================================================

import os
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles    import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units     import cm
from reportlab.lib            import colors
from reportlab.platypus      import (SimpleDocTemplate, Paragraph, Spacer,
                                      Table, TableStyle, HRFlowable,
                                      KeepTogether, PageBreak)
from reportlab.lib.enums     import TA_CENTER, TA_LEFT, TA_RIGHT


# ── Colour palette ────────────────────────────────────────────
BRAND_BLUE  = colors.HexColor('#0d6efd')
BRAND_DARK  = colors.HexColor('#1a1a2e')
ACCENT_CYAN = colors.HexColor('#00b4d8')
LIGHT_GREY  = colors.HexColor('#f8f9fa')
MID_GREY    = colors.HexColor('#dee2e6')
TEXT_DARK   = colors.HexColor('#212529')


def _build_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        'ReportTitle', fontName='Helvetica-Bold', fontSize=22,
        textColor=BRAND_BLUE, alignment=TA_CENTER, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        'SubTitle', fontName='Helvetica', fontSize=12,
        textColor=colors.grey, alignment=TA_CENTER, spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        'SectionHeader', fontName='Helvetica-Bold', fontSize=13,
        textColor=BRAND_DARK, spaceBefore=14, spaceAfter=6,
        borderPad=4,
    ))
    styles.add(ParagraphStyle(
        'BodyText2', fontName='Helvetica', fontSize=9,
        textColor=TEXT_DARK, leading=13,
    ))
    styles.add(ParagraphStyle(
        'Warning', fontName='Helvetica-Bold', fontSize=9,
        textColor=colors.HexColor('#dc3545'), leading=13,
    ))
    styles.add(ParagraphStyle(
        'StepTitle', fontName='Helvetica-Bold', fontSize=10,
        textColor=BRAND_BLUE, spaceBefore=6, spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        'Formula', fontName='Courier', fontSize=9,
        textColor=colors.HexColor('#495057'),
        backColor=LIGHT_GREY, borderPad=6, spaceAfter=3,
    ))
    return styles


def _header_footer(canvas, doc):
    """Draw page header and footer on every page."""
    canvas.saveState()
    width, height = A4

    # ── Header ────────────────────────────────────────────────
    canvas.setFillColor(BRAND_DARK)
    canvas.rect(0, height - 1.5*cm, width, 1.5*cm, fill=True, stroke=False)
    canvas.setFillColor(colors.white)
    canvas.setFont('Helvetica-Bold', 11)
    canvas.drawString(1*cm, height - 1.1*cm, 'ChemDesignAI')
    canvas.setFont('Helvetica', 9)
    canvas.drawRightString(width - 1*cm, height - 1.1*cm,
                           'Automated Process Equipment Design Report')

    # ── Footer ────────────────────────────────────────────────
    canvas.setFillColor(MID_GREY)
    canvas.rect(0, 0, width, 0.8*cm, fill=True, stroke=False)
    canvas.setFillColor(colors.grey)
    canvas.setFont('Helvetica', 8)
    canvas.drawString(1*cm, 0.25*cm,
                      f'Generated: {datetime.datetime.now().strftime("%d %b %Y %H:%M")}')
    canvas.drawCentredString(width/2, 0.25*cm, 'ChemDesignAI  |  AI-Based Process Design Platform')
    canvas.drawRightString(width - 1*cm, 0.25*cm, f'Page {doc.page}')
    canvas.restoreState()


def _kv_table(data: list, col_widths=None) -> Table:
    """Build a two-column key-value table."""
    col_widths = col_widths or [7*cm, 11*cm]
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), LIGHT_GREY),
        ('FONTNAME',   (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME',   (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE',   (0, 0), (-1, -1), 9),
        ('TEXTCOLOR',  (0, 0), (-1, -1), TEXT_DARK),
        ('GRID',       (0, 0), (-1, -1), 0.5, MID_GREY),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, LIGHT_GREY]),
        ('LEFTPADDING',  (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING',   (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 4),
    ]))
    return t


def generate_pdf_report(design, app) -> str:
    """
    Generate a detailed PDF report for an EquipmentDesign.

    Args:
        design: EquipmentDesign ORM object
        app:    Flask application (for config paths)

    Returns:
        Absolute path to the saved PDF file.
    """
    reports_dir = app.config['REPORTS_FOLDER']
    os.makedirs(reports_dir, exist_ok=True)

    filename = f'{design.equipment_type}_report_{design.id}_{int(datetime.datetime.now().timestamp())}.pdf'
    filepath = os.path.join(reports_dir, filename)

    doc = SimpleDocTemplate(
        filepath, pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=2.2*cm,  bottomMargin=1.5*cm,
    )

    styles  = _build_styles()
    story   = []
    inputs  = design.get_inputs()
    results = design.get_results()
    steps   = results.get('calculation_steps', [])
    errors  = results.get('errors', [])
    safety  = results.get('safety_notes', [])

    eq_name = design.equipment_type.replace('_', ' ').title()

    # ── Cover ─────────────────────────────────────────────────
    story.append(Spacer(1, 1.5*cm))
    story.append(Paragraph('AI-Based Chemical Process Equipment Design', styles['SubTitle']))
    story.append(Paragraph(f'{eq_name} Design Report', styles['ReportTitle']))
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width='100%', thickness=2, color=BRAND_BLUE))
    story.append(Spacer(1, 0.5*cm))

    # Meta info
    meta_data = [
        ['Design Name',    design.design_name or '—'],
        ['Equipment Type', eq_name],
        ['Design ID',      str(design.id)],
        ['Status',         design.status.title()],
        ['Generated By',   'ChemDesignAI Platform'],
        ['Date',           datetime.datetime.now().strftime('%d %B %Y, %H:%M')],
    ]
    story.append(_kv_table(meta_data))
    story.append(PageBreak())

    # ── 1. User Inputs ────────────────────────────────────────
    story.append(Paragraph('1. Design Inputs', styles['SectionHeader']))
    story.append(HRFlowable(width='100%', thickness=1, color=MID_GREY))
    story.append(Spacer(1, 0.2*cm))

    input_rows = [['Parameter', 'Value']]
    for k, v in inputs.items():
        label = k.replace('_', ' ').title()
        input_rows.append([label, str(v)])

    inp_table = Table(input_rows, colWidths=[9*cm, 9*cm])
    inp_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BRAND_BLUE),
        ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
        ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0, 0), (-1, -1), 9),
        ('GRID',       (0, 0), (-1, -1), 0.5, MID_GREY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
        ('LEFTPADDING',  (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 4),
    ]))
    story.append(inp_table)
    story.append(Spacer(1, 0.5*cm))

    # ── 2. Calculation Steps ──────────────────────────────────
    story.append(Paragraph('2. Step-by-Step Calculations', styles['SectionHeader']))
    story.append(HRFlowable(width='100%', thickness=1, color=MID_GREY))

    for step in steps:
        block = []
        block.append(Paragraph(
            f"Step {step.get('step', '?')}: {step.get('title', '')}",
            styles['StepTitle']
        ))
        if step.get('formula'):
            block.append(Paragraph(f"Formula: {step['formula']}", styles['Formula']))
        if step.get('calc'):
            block.append(Paragraph(f"Working: {step['calc']}", styles['BodyText2']))
        if step.get('result'):
            block.append(Paragraph(f"Result: {step['result']}", styles['BodyText2']))
        block.append(Spacer(1, 0.2*cm))
        story.append(KeepTogether(block))

    # ── 3. Final Results Summary ──────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph('3. Final Results Summary', styles['SectionHeader']))
    story.append(HRFlowable(width='100%', thickness=1, color=MID_GREY))
    story.append(Spacer(1, 0.2*cm))

    # Filter out non-scalar result keys
    skip_keys = {'calculation_steps', 'errors', 'safety_notes', 'ai_suggestions'}
    result_rows = [['Parameter', 'Value']]
    for k, v in results.items():
        if k in skip_keys:
            continue
        if isinstance(v, (list, dict)):
            continue
        label = k.replace('_', ' ').title()
        if isinstance(v, float):
            val_str = f'{v:,.4f}' if abs(v) < 1000 else f'{v:,.2f}'
        else:
            val_str = str(v)
        result_rows.append([label, val_str])

    res_table = Table(result_rows, colWidths=[9*cm, 9*cm])
    res_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT_CYAN),
        ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
        ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0, 0), (-1, -1), 9),
        ('GRID',       (0, 0), (-1, -1), 0.5, MID_GREY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
        ('LEFTPADDING',  (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 4),
    ]))
    story.append(res_table)
    story.append(Spacer(1, 0.5*cm))

    # ── 4. Cost Estimation ────────────────────────────────────
    story.append(Paragraph('4. Cost Estimation', styles['SectionHeader']))
    story.append(HRFlowable(width='100%', thickness=1, color=MID_GREY))
    cost_data = [
        ['Purchased Equipment Cost', f"${results.get('purchased_cost_USD', 0):,.0f}"],
        ['Installed Equipment Cost', f"${results.get('installed_cost_USD', 0):,.0f}"],
        ['Construction Material',    results.get('material', '—')],
        ['Note', 'Costs based on 2024 CEPCI index. Actual costs may vary ±30%.'],
    ]
    story.append(_kv_table(cost_data))
    story.append(Spacer(1, 0.5*cm))

    # ── 5. Safety Recommendations ─────────────────────────────
    story.append(Paragraph('5. Industrial Safety Recommendations', styles['SectionHeader']))
    story.append(HRFlowable(width='100%', thickness=1, color=MID_GREY))
    story.append(Spacer(1, 0.2*cm))
    for note in safety:
        story.append(Paragraph(f'• {note}', styles['Warning']))
        story.append(Spacer(1, 0.1*cm))

    # ── 6. Calculation Errors / Warnings ─────────────────────
    if errors:
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph('6. Warnings & Errors', styles['SectionHeader']))
        story.append(HRFlowable(width='100%', thickness=1, color=colors.red))
        for err in errors:
            story.append(Paragraph(f'⚠ {err}', styles['Warning']))

    # ── 7. AI Suggestions ─────────────────────────────────────
    if design.ai_suggestions:
        story.append(PageBreak())
        story.append(Paragraph('7. AI Optimization Suggestions', styles['SectionHeader']))
        story.append(HRFlowable(width='100%', thickness=1, color=ACCENT_CYAN))
        story.append(Spacer(1, 0.2*cm))
        for line in design.ai_suggestions.split('\n'):
            if line.strip():
                story.append(Paragraph(line.strip(), styles['BodyText2']))
                story.append(Spacer(1, 0.1*cm))

    # ── Disclaimer ────────────────────────────────────────────
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width='100%', thickness=1, color=MID_GREY))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        'DISCLAIMER: This report is generated by an automated AI-assisted design tool '
        'for educational and preliminary engineering purposes. All designs must be '
        'verified by a licensed professional engineer before implementation. '
        'The platform authors accept no liability for any design decisions made '
        'based on this report.',
        styles['BodyText2']
    ))

    # ── Build PDF ─────────────────────────────────────────────
    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return filepath
