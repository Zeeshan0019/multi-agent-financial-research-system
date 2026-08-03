"""
Report Agent.

No standalone "Report Agent" service exists in this repo yet, so the
orchestrator generates the analyst-style PDF itself, using the metrics and
red flags already produced by the Extraction Agent and Red Flag Agent and
stored on each `Document` row. Built with reportlab (pure Python, no external
binary dependency).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

import models
from config import settings
from utils import build_display_metrics

logger = logging.getLogger("orchestrator.reports")

SEVERITY_COLORS = {
    "low": colors.HexColor("#2f7d4f"),
    "medium": colors.HexColor("#b8860b"),
    "high": colors.HexColor("#c0392b"),
    "critical": colors.HexColor("#7b1113"),
}


def _metrics_table(document: models.Document, styles) -> Table:
    display = build_display_metrics(document.financial_data)
    rows = [["Metric", "Value"]]
    for label, key in [
        ("Revenue", "revenue"),
        ("Net profit", "net_profit"),
        ("EBITDA", "ebitda"),
        ("EPS", "eps"),
        ("Assets", "assets"),
        ("Liabilities", "liabilities"),
        ("Cash flow", "cash_flow"),
    ]:
        rows.append([label, display.get(key) or "Not found"])
    for ratio_name, ratio_value in (display.get("ratios") or {}).items():
        rows.append([ratio_name.replace("_", " ").title(), ratio_value])

    table = Table(rows, colWidths=[2.4 * inch, 3.6 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d2430")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d9dee7")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f7f9")]),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def _red_flags_table(document: models.Document, styles) -> Table | None:
    flags = document.red_flags or []
    if not flags:
        return None

    rows = [["Severity", "Category", "Title", "Description"]]
    for flag in flags:
        severity = str(flag.get("severity", "")).strip()
        rows.append(
            [
                severity or "-",
                flag.get("category", "-"),
                flag.get("title", "-"),
                Paragraph(flag.get("description", "-"), styles["BodySmall"]),
            ]
        )

    table = Table(rows, colWidths=[0.8 * inch, 1.3 * inch, 1.5 * inch, 2.4 * inch])
    style_commands = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d2430")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d9dee7")),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for row_index, flag in enumerate(flags, start=1):
        severity_key = str(flag.get("severity", "")).lower()
        color = SEVERITY_COLORS.get(severity_key, colors.HexColor("#3f4a5c"))
        style_commands.append(("TEXTCOLOR", (0, row_index), (0, row_index), color))
        style_commands.append(("FONTNAME", (0, row_index), (0, row_index), "Helvetica-Bold"))
    table.setStyle(TableStyle(style_commands))
    return table


def build_report_pdf(
    session_name: str, documents: list[models.Document], output_path: Path
) -> None:
    """Render one PDF covering all given (already-processed) documents."""
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="BodySmall", parent=styles["BodyText"], fontSize=8, leading=10
        )
    )

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=LETTER,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        title=f"Financial Research Report — {session_name}",
    )

    story = []
    story.append(Paragraph("Financial Research Report", styles["Title"]))
    story.append(Paragraph(f"Session: {session_name}", styles["Normal"]))
    story.append(
        Paragraph(
            f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.3 * inch))

    for i, document in enumerate(documents):
        if i > 0:
            story.append(PageBreak())

        story.append(Paragraph(document.company_name or "Unknown Company", styles["Heading1"]))
        story.append(
            Paragraph(
                f"Source file: {document.file_name} &nbsp;|&nbsp; "
                f"Financial year: {document.financial_year or 'Unspecified'} &nbsp;|&nbsp; "
                f"Extraction confidence: {document.confidence_score * 100:.0f}%",
                styles["Normal"],
            )
        )
        story.append(Spacer(1, 0.15 * inch))

        if document.status != "ready":
            story.append(
                Paragraph(
                    f"This document has not finished processing (status: {document.status}). "
                    "Metrics and red flags below may be incomplete.",
                    styles["Italic"],
                )
            )
            story.append(Spacer(1, 0.1 * inch))

        story.append(Paragraph("Key Financial Metrics", styles["Heading2"]))
        story.append(_metrics_table(document, styles))
        story.append(Spacer(1, 0.25 * inch))

        story.append(Paragraph("Risk Assessment", styles["Heading2"]))
        if document.overall_risk:
            story.append(Paragraph(f"Overall risk rating: <b>{document.overall_risk}</b>", styles["Normal"]))
        if document.risk_summary:
            story.append(Spacer(1, 0.05 * inch))
            story.append(Paragraph(document.risk_summary, styles["BodyText"]))
        story.append(Spacer(1, 0.1 * inch))

        flags_table = _red_flags_table(document, styles)
        if flags_table is not None:
            story.append(flags_table)
        else:
            story.append(Paragraph("No red flags were identified for this document.", styles["Normal"]))

    doc.build(story)


def generate_report_sync(
    report_id: str, session_id: str, session_name: str, documents: list[models.Document]
) -> Path:
    """Synchronous PDF build; call from a background task/thread."""
    output_dir = Path(settings.reports_dir) / session_id
    output_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"report_{report_id}.pdf"
    output_path = output_dir / file_name
    build_report_pdf(session_name, documents, output_path)
    return output_path
