"""
Report Agent
============
Compiles the outputs of the Document, Extraction, Red Flag and Comparison
agents into a structured, analyst-style PDF research report.

Every figure and finding placed into the report is read directly from the
database (i.e. from what the other agents already grounded in the source
filings) — the Report Agent performs formatting and light synthesis only,
never introduces new facts.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    HRFlowable,
)
from sqlalchemy.orm import Session

from backend.database.models import Company, Document, FinancialMetric, RedFlag, Report
from backend.comparison_agent.comparison_agent import ComparisonAgent, DEFAULT_METRIC

logger = logging.getLogger("report_agent")

REPORTS_ROOT = Path("reports")

ALL_SECTIONS = [
    "Executive Summary",
    "Key Financials",
    "Red Flags & Risks",
    "Company Comparison",
    "Outlook",
]

SEVERITY_COLORS = {
    "high": colors.HexColor("#DC2626"),
    "medium": colors.HexColor("#D97706"),
    "low": colors.HexColor("#65A30D"),
}


def _fmt(value: Optional[float], suffix: str = "") -> str:
    if value is None:
        return "—"
    return f"{value:,.2f}{suffix}"


def _clean(text: Optional[str]) -> str:
    """Strip characters not present in ReportLab's base-14 fonts (e.g. the
    rupee sign renders as a black box) so PDF text never shows glyph boxes."""
    if not text:
        return ""
    return (
        text.replace("\u20b9", "Rs. ")
        .replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2013", "-")
        .replace("\u2014", "-")
    )


class ReportAgent:
    """Compiles a structured, analyst-style PDF research report."""

    def __init__(self):
        self.comparison_agent = ComparisonAgent()
        self.styles = getSampleStyleSheet()
        self.styles.add(
            ParagraphStyle(
                name="ReportTitle",
                fontName="Helvetica-Bold",
                fontSize=22,
                leading=26,
                textColor=colors.HexColor("#0B1220"),
                spaceAfter=8,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="Eyebrow",
                fontName="Helvetica-Bold",
                fontSize=9,
                textColor=colors.HexColor("#7C3AED"),
                spaceAfter=14,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="SectionHeading",
                fontName="Helvetica-Bold",
                fontSize=15,
                textColor=colors.HexColor("#0B1220"),
                spaceBefore=6,
                spaceAfter=10,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="Body",
                fontName="Helvetica",
                fontSize=9.5,
                leading=14,
                textColor=colors.HexColor("#334155"),
                spaceAfter=8,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="CompanyHeading",
                fontName="Helvetica-Bold",
                fontSize=10.5,
                textColor=colors.HexColor("#0B1220"),
                spaceBefore=6,
                spaceAfter=3,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="Footnote",
                fontName="Helvetica-Oblique",
                fontSize=7.5,
                textColor=colors.HexColor("#94A3B8"),
            )
        )

    # ------------------------------------------------------------------ #
    # Data gathering
    # ------------------------------------------------------------------ #
    def _gather(self, db: Session, document_ids: List[int]) -> List[Dict[str, Any]]:
        bundle = []
        for doc_id in document_ids:
            doc = db.query(Document).filter(Document.document_id == doc_id).first()
            if not doc:
                continue
            metric = db.query(FinancialMetric).filter(FinancialMetric.document_id == doc_id).first()
            flags = db.query(RedFlag).filter(RedFlag.document_id == doc_id).all()
            bundle.append(
                {
                    "document": doc,
                    "company": doc.company,
                    "metric": metric,
                    "red_flags": flags,
                }
            )
        return bundle

    # ------------------------------------------------------------------ #
    # Section builders
    # ------------------------------------------------------------------ #
    def _cover(self, story, session_name: str, bundle: List[Dict[str, Any]], sections: List[str]):
        story.append(Spacer(1, 1.4 * inch))
        story.append(Paragraph("MULTI-AGENT FINANCIAL RESEARCH SYSTEM", self.styles["Eyebrow"]))
        story.append(Paragraph("Multi-Agent Financial Research &amp; Comparative Brief", self.styles["ReportTitle"]))
        story.append(
            Paragraph(
                "Comprehensive equity summary, financial metrics, and risk anomalies compiled "
                "from indexed filings by the Document, Extraction, Red Flag, and Comparison agents.",
                self.styles["Body"],
            )
        )
        story.append(Spacer(1, 0.6 * inch))
        story.append(HRFlowable(width="100%", color=colors.HexColor("#E2E8F0")))
        story.append(Spacer(1, 0.2 * inch))

        companies = ", ".join(
            _clean(b["company"].company_name if b["company"] else b["document"].file_name) for b in bundle
        ) or "-"
        meta_table = Table(
            [
                ["Session", session_name or "Active Workspace"],
                ["Release Date", datetime.now().strftime("%B %d, %Y")],
                ["Parsed Entities", companies],
                ["Assigned Agents", "Document, Extraction, Red Flag, Comparison, Report"],
                ["Sections Included", ", ".join(sections)],
            ],
            colWidths=[1.6 * inch, 4.7 * inch],
        )
        meta_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#94A3B8")),
                    ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#334155")),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        story.append(meta_table)
        story.append(PageBreak())

    def _page_header(self, story, index: int, name: str):
        story.append(Paragraph(f"PAGE {index} &middot; {name.upper()}", self.styles["Eyebrow"]))
        story.append(Paragraph(name, self.styles["SectionHeading"]))

    def _section_executive_summary(self, story, bundle: List[Dict[str, Any]]):
        story.append(
            Paragraph(
                "This research brief compiles financial metrics, margin indicators, and risk "
                "anomalies extracted from the indexed filings. The multi-agent pipeline completed "
                "ingestion, extraction, and risk-scanning for each document listed below.",
                self.styles["Body"],
            )
        )
        for b in bundle:
            company = b["company"]
            doc = b["document"]
            name = _clean(company.company_name if company else doc.file_name)
            sector = _clean(company.industry if company else "Unknown sector")
            fy = _clean(company.fiscal_year if company else "-")
            n_flags = len(b["red_flags"])
            story.append(Paragraph(name, self.styles["CompanyHeading"]))
            story.append(
                Paragraph(
                    f"Sector: {sector} &nbsp;|&nbsp; Fiscal Year: {fy} &nbsp;|&nbsp; "
                    f"Source file: {_clean(doc.file_name)} &nbsp;|&nbsp; Red flags identified: {n_flags}",
                    self.styles["Body"],
                )
            )

    def _section_key_financials(self, story, bundle: List[Dict[str, Any]]):
        story.append(
            Paragraph(
                "The Extraction Agent pulled the following headline figures directly from each "
                "filing. All values are grounded in the source document.",
                self.styles["Body"],
            )
        )
        header = ["Metric"] + [
            _clean(b["company"].company_name if b["company"] else b["document"].file_name).split(" ")[0]
            for b in bundle
        ]
        rows_def = [
            ("Revenue (cr)", lambda m: _fmt(m.revenue if m else None)),
            ("Net Income (cr)", lambda m: _fmt(m.net_income if m else None)),
            ("EBITDA (cr)", lambda m: _fmt(m.ebitda if m else None)),
            ("Total Assets (cr)", lambda m: _fmt(m.total_assets if m else None)),
            ("Total Liabilities (cr)", lambda m: _fmt(m.total_liabilities if m else None)),
            ("EPS", lambda m: _fmt(m.eps if m else None)),
        ]
        data = [header]
        for label, fn in rows_def:
            row = [label] + [fn(b["metric"]) for b in bundle]
            data.append(row)

        table = Table(data, colWidths=[1.7 * inch] + [4.6 / max(len(bundle), 1) * inch] * len(bundle))
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F8FAFC")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#334155")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(table)

    def _section_red_flags(self, story, bundle: List[Dict[str, Any]]):
        story.append(
            Paragraph(
                "The Red Flag Agent scanned disclosures for anomalies, rising debt, falling margins, "
                "auditor qualifications, and unusual financial patterns.",
                self.styles["Body"],
            )
        )
        any_flags = False
        for b in bundle:
            company = b["company"]
            name = company.company_name if company else b["document"].file_name
            flags = b["red_flags"]
            if not flags:
                continue
            any_flags = True
            story.append(Paragraph(_clean(name), self.styles["CompanyHeading"]))
            cell_style = ParagraphStyle(
                "FlagCell", parent=self.styles["Body"], fontSize=7.6, leading=10, spaceAfter=0
            )
            data = [["Severity", "Risk", "Detail"]]
            for f in flags:
                data.append(
                    [
                        f.severity.upper(),
                        Paragraph(_clean(f.risk_type), cell_style),
                        Paragraph(_clean(f.description), cell_style),
                    ]
                )
            table = Table(data, colWidths=[0.65 * inch, 1.55 * inch, 4.1 * inch])
            style_cmds = [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F8FAFC")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7.6),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#334155")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
            for i, f in enumerate(flags, start=1):
                color = SEVERITY_COLORS.get(f.severity.lower(), colors.grey)
                style_cmds.append(("TEXTCOLOR", (0, i), (0, i), color))
                style_cmds.append(("FONTNAME", (0, i), (0, i), "Helvetica-Bold"))
            table.setStyle(TableStyle(style_cmds))
            story.append(table)
            story.append(Spacer(1, 8))
        if not any_flags:
            story.append(Paragraph("No red flags were surfaced for the selected documents.", self.styles["Body"]))

    def _section_comparison(self, story, db: Session, document_ids: List[int], bundle: List[Dict[str, Any]]):
        if len(document_ids) < 2:
            story.append(
                Paragraph(
                    "Comparison requires two or more documents. Only one document was included in "
                    "this report, so no benchmarking table is shown.",
                    self.styles["Body"],
                )
            )
            return
        try:
            result = self.comparison_agent.compare(db, document_ids, DEFAULT_METRIC)
        except Exception:
            logger.exception("Comparison section failed")
            story.append(Paragraph("Comparison could not be computed for the selected documents.", self.styles["Body"]))
            return

        story.append(Paragraph(f"Benchmark of {result['metric']} across included coverage entities.", self.styles["Body"]))
        data = [["Company", result["metric"]]]
        for row in result["rows"]:
            val = "-" if row["value"] is None else f"{row['value']:.2f}"
            data.append([_clean(row["company"]), val])
        table = Table(data, colWidths=[3.5 * inch, 2.8 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F8FAFC")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#334155")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(table)
        story.append(Spacer(1, 6))
        story.append(Paragraph(result["citation"]["section"], self.styles["Footnote"]))

    def _section_outlook(self, story, bundle: List[Dict[str, Any]]):
        story.append(
            Paragraph(
                "The outlook below is synthesized strictly from the metrics and red flags already "
                "extracted above — no external projections or generative estimates are introduced.",
                self.styles["Body"],
            )
        )
        for b in bundle:
            company = b["company"]
            name = _clean(company.company_name if company else b["document"].file_name)
            flags = b["red_flags"]
            high = [f for f in flags if f.severity.lower() == "high"]
            if high:
                watch = "; ".join(_clean(f.risk_type) for f in high[:3])
                text = f"Primary watch items for {name}: {watch}."
            elif flags:
                text = f"{name} shows only medium/low-severity items; no high-severity risks were flagged in this filing."
            else:
                text = f"No red flags were surfaced for {name} in the scanned sections of this filing."
            story.append(Paragraph(text, self.styles["Body"]))

        story.append(Spacer(1, 10))
        disclaimer = Table(
            [[Paragraph(
                "<b>Citation Grounding Disclaimer</b><br/>All statements in this document are "
                "matched to source material already extracted by upstream agents. No synthetic "
                "projections or generative hallucinations were permitted during report assembly.",
                self.styles["Body"],
            )]],
            colWidths=[6.3 * inch],
        )
        disclaimer.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFFBEB")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#FDE68A")),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )
        story.append(disclaimer)

    # ------------------------------------------------------------------ #
    # Public entry point
    # ------------------------------------------------------------------ #
    def generate(
        self,
        db: Session,
        user_id: int,
        username: str,
        document_ids: List[int],
        sections: Optional[List[str]] = None,
        title: Optional[str] = None,
    ) -> Report:
        sections = [s for s in (sections or ALL_SECTIONS) if s in ALL_SECTIONS] or ALL_SECTIONS
        bundle = self._gather(db, document_ids)
        if not bundle:
            raise ValueError("None of the requested document_ids were found.")

        out_dir = REPORTS_ROOT / f"user_{user_id}"
        out_dir.mkdir(parents=True, exist_ok=True)
        filename = f"report_{int(datetime.now().timestamp())}.pdf"
        out_path = out_dir / filename

        names = [(b["company"].company_name if b["company"] else b["document"].file_name) for b in bundle]
        report_title = title or (" vs ".join(n.split(" ")[0] for n in names) + " — Research Brief")

        doc = SimpleDocTemplate(
            str(out_path),
            pagesize=LETTER,
            leftMargin=0.85 * inch,
            rightMargin=0.85 * inch,
            topMargin=0.85 * inch,
            bottomMargin=0.85 * inch,
            title=report_title,
        )

        story = []
        self._cover(story, username, bundle, sections)

        section_builders = {
            "Executive Summary": lambda s: self._section_executive_summary(s, bundle),
            "Key Financials": lambda s: self._section_key_financials(s, bundle),
            "Red Flags & Risks": lambda s: self._section_red_flags(s, bundle),
            "Company Comparison": lambda s: self._section_comparison(s, db, document_ids, bundle),
            "Outlook": lambda s: self._section_outlook(s, bundle),
        }
        for i, name in enumerate(sections, start=2):
            self._page_header(story, i, name)
            section_builders[name](story)
            if i - 1 < len(sections):
                story.append(PageBreak())

        doc.build(story)

        report = Report(
            user_id=user_id,
            report_title=report_title,
            report_path=str(out_path),
        )
        if hasattr(Report, "document_ids"):
            report.document_ids = ",".join(str(d) for d in document_ids)
        if hasattr(Report, "status"):
            report.status = "ready"
        if hasattr(Report, "pages"):
            report.pages = len(sections)
        if hasattr(Report, "sections"):
            report.sections = ",".join(sections)

        db.add(report)
        db.commit()
        db.refresh(report)
        return report
