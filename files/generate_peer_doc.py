"""
generate_peer_doc.py

Generates infoedge_financial_document.pdf, a realistic FY2025 financial document
for InfoEdge Systems Limited to use as the peer comparison document against NexaCore.
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak


def generate_infoedge_pdf(out_path: str):
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleX", parent=styles["Title"], fontSize=18, leading=22, textColor=colors.HexColor("#0f172a"))
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13, leading=16, spaceBefore=12, spaceAfter=6, textColor=colors.HexColor("#1e293b"))
    body = ParagraphStyle("BodyX", parent=styles["Normal"], fontSize=9.5, leading=13.5, textColor=colors.HexColor("#334155"))
    meta_style = ParagraphStyle("MetaX", parent=styles["Normal"], fontSize=8.5, leading=12, textColor=colors.HexColor("#64748b"))

    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm
    )
    story = []

    story.append(Paragraph("INFOEDGE SYSTEMS LIMITED", title_style))
    story.append(Paragraph("Annual Report and Financial Statements — FY2025", ParagraphStyle("SubTitle", parent=title_style, fontSize=12, leading=15, textColor=colors.HexColor("#475569"))))
    story.append(Spacer(1, 6))
    story.append(Paragraph("CIN: L72200MH1995PLC089412 | BSE: 532540 | NSE: INFOEDGE", meta_style))
    story.append(Paragraph("Registered Office: InfoEdge Towers, Bandra-Kurla Complex, Mumbai – 400 051", meta_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("SECTION 1: FINANCIAL HIGHLIGHTS & OPERATING PERFORMANCE", h2))
    story.append(Paragraph(
        "InfoEdge Systems Limited today announced its audited consolidated financial results for the full fiscal year ended March 31, 2025 (FY2025). "
        "The Company delivered strong financial performance driven by expanded cloud transformation contracts, enterprise AI adoption, and disciplined execution.",
        body
    ))
    story.append(Spacer(1, 8))

    # Highlights table
    table_data = [
        ["Key Financial Indicator", "FY2025 (Rs cr)", "FY2024 (Rs cr)", "YoY Growth (%)"],
        ["Revenue from Operations", "1,42,840", "1,31,520", "+8.6% (CC: +6.8%)"],
        ["Operating Profit (EBIT)", "32,567", "29,460", "+10.5%"],
        ["EBIT Margin (%)", "22.8%", "22.4%", "+40 bps"],
        ["Profit After Tax (PAT)", "24,568", "21,980", "+11.8%"],
        ["PAT Margin (%)", "17.2%", "16.7%", "+50 bps"],
        ["Return on Equity (ROE)", "28.4%", "27.2%", "+120 bps"],
        ["Return on Capital Employed (ROCE)", "32.4%", "31.0%", "+140 bps"],
        ["Days Sales Outstanding (DSO)", "62.4 days", "64.8 days", "-2.4 days"],
        ["Free Cash Flow (FCF) / PAT", "89.6%", "87.2%", "+240 bps"],
        ["Revenue per Employee", "Rs 58.4 lakh", "Rs 55.2 lakh", "+5.8%"],
        ["Attrition Rate (LTM)", "13.8%", "15.4%", "-160 bps"],
    ]

    t = Table(table_data, colWidths=[6.5 * cm, 3.2 * cm, 3.2 * cm, 4.1 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    story.append(Paragraph("SECTION 2: MANAGEMENT DISCUSSION AND ANALYSIS", h2))
    story.append(Paragraph(
        "Consolidated revenue for FY2025 reached ₹1,42,840 crore, representing constant currency growth of 6.8%. "
        "EBIT margin expanded to 22.8% due to high-value digital service mix and operational automation. "
        "Days Sales Outstanding (DSO) stood at 62.4 days, demonstrating strong working capital management. "
        "Cash conversion remained robust with Free Cash Flow to PAT at 89.6%. Total workforce stood at 2,44,589 employees, "
        "yielding revenue per employee of ₹58.4 lakh, while voluntary attrition reduced to 13.8%.",
        body
    ))
    story.append(Spacer(1, 14))
    story.append(Paragraph("Report Source: InfoEdge Systems Statutory Filings FY2025.", meta_style))

    doc.build(story)
    print(f"Generated {out_path}")


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "infoedge_financial_document.pdf")
    generate_infoedge_pdf(out)
