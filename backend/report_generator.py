"""
PDF report generator for NiveshNetra portfolio analysis.
Uses reportlab only.
"""

import io
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak,
)


W, H = A4
MARGIN = 15 * mm

RED = colors.HexColor("#cc0000")
DARK = colors.HexColor("#111827")
MUTED = colors.HexColor("#6b7280")
LIGHT_BG = colors.HexColor("#f9fafb")
BORDER = colors.HexColor("#e5e7eb")
GREEN = colors.HexColor("#16a34a")
INDIGO = colors.HexColor("#4f46e5")


def _fmt(n: float) -> str:
    if n >= 1e7:
        return f"\u20b9{n/1e7:.2f}Cr"
    if n >= 1e5:
        return f"\u20b9{n/1e5:.2f}L"
    return f"\u20b9{n:,.0f}"


def _pct(v) -> str:
    if v is None:
        return "N/A"
    return f"{v*100:.2f}%"


def generate_report(data: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=MARGIN,
        leftMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", fontSize=18, fontName="Helvetica-Bold", textColor=RED, spaceAfter=2)
    sub_style = ParagraphStyle("sub", fontSize=10, fontName="Helvetica", textColor=MUTED, spaceAfter=8)
    h2_style = ParagraphStyle("h2", fontSize=12, fontName="Helvetica-Bold", textColor=DARK, spaceBefore=10, spaceAfter=4)
    body_style = ParagraphStyle("body", fontSize=9, fontName="Helvetica", textColor=DARK, spaceAfter=4, leading=13)
    small_style = ParagraphStyle("small", fontSize=8, fontName="Helvetica", textColor=MUTED)

    today = date.today().strftime("%d %B %Y")
    funds = data.get("funds", [])
    overlaps = data.get("overlaps", [])
    actions = data.get("rebalancingActions", [])
    plan_text = data.get("rebalancingPlan", "")
    health_score = data.get("moneyHealthScore", 0)
    dimensions = data.get("moneyHealthDimensions", [])
    total_invested = data.get("totalInvested", 0)
    total_current = data.get("totalCurrentValue", 0)
    xirr = data.get("portfolioXirr")
    expense_drag = data.get("totalExpenseDragAnnual", 0)
    avoidable = round(expense_drag * 0.4)

    story = []

    # ── PAGE 1 ──────────────────────────────────────────────────────────────

    # Header
    story.append(Paragraph("NiveshNetra", title_style))
    story.append(Paragraph(f"Portfolio X-Ray · ET Money Mentor · Generated {today}", sub_style))
    story.append(HRFlowable(width="100%", thickness=1, color=RED, spaceAfter=8))

    # Hero metrics table
    story.append(Paragraph("Portfolio Summary", h2_style))
    hero_data = [
        ["Total Invested", "Current Value", "Portfolio XIRR", "Avoidable Fees/yr"],
        [_fmt(total_invested), _fmt(total_current), _pct(xirr), f"\u20b9{avoidable:,}"],
    ]
    hero_table = Table(hero_data, colWidths=[(W - 2*MARGIN) / 4] * 4)
    hero_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BG),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, 1), 13),
        ("TEXTCOLOR", (0, 1), (-1, 1), DARK),
        ("TEXTCOLOR", (3, 1), (3, 1), RED),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [LIGHT_BG, colors.white]),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(hero_table)
    story.append(Spacer(1, 6*mm))

    # Money Health Score
    story.append(Paragraph(f"Money Health Score: {health_score}/100", h2_style))
    dim_data = [["Dimension", "Score", "Insight"]]
    for d in dimensions:
        bar = "█" * (d["score"] // 10) + "░" * (10 - d["score"] // 10)
        dim_data.append([d["label"], f"{d['score']}/100  {bar}", d["insight"]])
    dim_table = Table(dim_data, colWidths=[45*mm, 60*mm, (W - 2*MARGIN - 105*mm)])
    dim_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), INDIGO),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ("GRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(dim_table)
    story.append(Spacer(1, 6*mm))

    # Fund Details table
    story.append(Paragraph("Fund Details", h2_style))
    fund_headers = ["Fund Name", "Invested", "Current Value", "XIRR", "Benchmark", "Alpha", "Exp Ratio"]
    fund_rows = [fund_headers]
    col_w = (W - 2*MARGIN)
    fund_col_widths = [col_w*0.30, col_w*0.12, col_w*0.13, col_w*0.10, col_w*0.12, col_w*0.10, col_w*0.13]
    for f in funds:
        name = f.get("fundName", "")
        # Truncate long names
        if len(name) > 35:
            name = name[:33] + "…"
        xirr_v = f.get("xirr")
        bench_v = f.get("benchmarkXirr")
        alpha = None
        if xirr_v is not None and bench_v is not None:
            alpha = xirr_v - bench_v
        fund_rows.append([
            name,
            _fmt(f.get("totalInvested", 0)),
            _fmt(round(f.get("currentValue", 0))),
            _pct(xirr_v),
            _pct(bench_v),
            _pct(alpha),
            _pct(f.get("expenseRatio")),
        ])
    fund_table = Table(fund_rows, colWidths=fund_col_widths)
    fund_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ("GRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(fund_table)

    # ── PAGE 2 ──────────────────────────────────────────────────────────────
    story.append(PageBreak())

    story.append(Paragraph("NiveshNetra", title_style))
    story.append(Paragraph(f"Rebalancing Plan & Insights · {today}", sub_style))
    story.append(HRFlowable(width="100%", thickness=1, color=RED, spaceAfter=8))

    # Top overlaps
    if overlaps:
        story.append(Paragraph("Top Portfolio Overlaps", h2_style))
        ov_data = [["Fund A", "Fund B", "Overlap %", "Shared Stocks"]]
        for o in overlaps[:3]:
            shared = ", ".join(o.get("sharedStocks", [])[:4])
            ov_data.append([
                " ".join(o.get("fundA", "").split()[:3]),
                " ".join(o.get("fundB", "").split()[:3]),
                f"{round(o.get('overlapPct', 0)*100)}%",
                shared or "—",
            ])
        ov_table = Table(ov_data, colWidths=[50*mm, 50*mm, 25*mm, (W - 2*MARGIN - 125*mm)])
        ov_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), INDIGO),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
            ("GRID", (0, 0), (-1, -1), 0.3, BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(ov_table)
        story.append(Spacer(1, 5*mm))

    # AI Rebalancing Plan
    story.append(Paragraph("AI Rebalancing Plan", h2_style))
    for line in plan_text.split("\n"):
        line = line.strip()
        if line:
            story.append(Paragraph(line, body_style))
    story.append(Spacer(1, 5*mm))

    # Action Items
    if actions:
        story.append(Paragraph("Action Items", h2_style))
        action_data = [["Type", "Fund", "Action", "Impact"]]
        for a in actions:
            action_data.append([
                a.get("type", "").upper(),
                " ".join(a.get("fund", "").split()[:4]),
                a.get("detail", "")[:60],
                a.get("impact", ""),
            ])
        act_col_w = W - 2*MARGIN
        act_table = Table(
            action_data,
            colWidths=[act_col_w*0.10, act_col_w*0.20, act_col_w*0.45, act_col_w*0.25],
        )
        act_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7.5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
            ("GRID", (0, 0), (-1, -1), 0.3, BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(act_table)

    # Footer
    story.append(Spacer(1, 10*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=MUTED))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        "Generated by NiveshNetra · ET AI Hackathon 2026 · Not financial advice",
        ParagraphStyle("footer", fontSize=8, fontName="Helvetica", textColor=MUTED, alignment=1),
    ))

    doc.build(story)
    return buf.getvalue()
