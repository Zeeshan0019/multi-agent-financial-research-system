"""
Report Agent
============
Compiles agent outputs into a structured, analyst-style PDF with full
prose paragraphs — not bullet points. Every section reads like a professional
equity research note grounded strictly in the extracted data.
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
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether,
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

SEV_COLORS = {
    "high":   colors.HexColor("#DC2626"),
    "medium": colors.HexColor("#D97706"),
    "low":    colors.HexColor("#16A34A"),
}

ACCENT  = colors.HexColor("#7C3AED")
TEAL    = colors.HexColor("#0D9488")
SLATE   = colors.HexColor("#F8FAFC")
BORDER  = colors.HexColor("#E2E8F0")
INK     = colors.HexColor("#1E293B")
MUTED   = colors.HexColor("#475569")


def _c(t): return (t or "").replace("\u20b9","Rs. ").replace("\u2019","'").replace("\u2018","'").replace("\u201c",'"').replace("\u201d",'"').replace("\u2013","-").replace("\u2014","-") if t else ""
def _f(v, sfx=""): return f"{v:,.2f}{sfx}" if v is not None else "—"
def _pct(n, d): return f"{n/d*100:.1f}%" if n and d else "—"


class ReportAgent:

    def __init__(self):
        self.comparison_agent = ComparisonAgent()
        ss = getSampleStyleSheet()

        def _sty(name, **kw):
            ss.add(ParagraphStyle(name=name, **kw))

        _sty("Cover1",    fontName="Helvetica-Bold",    fontSize=26, leading=32, textColor=INK,   spaceAfter=6)
        _sty("Cover2",    fontName="Helvetica",         fontSize=12, leading=16, textColor=ACCENT, spaceAfter=4)
        _sty("Cover3",    fontName="Helvetica",         fontSize=9,  leading=13, textColor=MUTED,  spaceAfter=2)
        _sty("Eyebrow",   fontName="Helvetica-Bold",    fontSize=7.5,leading=10, textColor=ACCENT, spaceAfter=4,  letterSpacing=1.4)
        _sty("SecHead",   fontName="Helvetica-Bold",    fontSize=14, leading=18, textColor=INK,   spaceBefore=16,spaceAfter=8)
        _sty("SubHead",   fontName="Helvetica-Bold",    fontSize=10, leading=14, textColor=INK,   spaceBefore=8, spaceAfter=4)
        _sty("Body",      fontName="Helvetica",         fontSize=9.5,leading=15, textColor=MUTED, spaceAfter=8,  alignment=4)   # justified
        _sty("BodyBold",  fontName="Helvetica-Bold",    fontSize=9.5,leading=15, textColor=INK,   spaceAfter=6)
        _sty("Note",      fontName="Helvetica-Oblique", fontSize=7.5,leading=11, textColor=colors.HexColor("#94A3B8"), spaceAfter=6)
        _sty("FlagCell",  fontName="Helvetica",         fontSize=8,  leading=11, textColor=MUTED, spaceAfter=0)
        self.S = ss

    # ── helpers ─────────────────────────────────────────────────────────────
    def _hr(self):         return HRFlowable(width="100%", color=BORDER, thickness=0.5, spaceAfter=8, spaceBefore=8)
    def _sp(self, n=6):   return Spacer(1, n)
    def _h(self, t):       return Paragraph(t.upper(), self.S["Eyebrow"])
    def _sec(self, t):     return Paragraph(t, self.S["SecHead"])
    def _sub(self, t):     return Paragraph(_c(t), self.S["SubHead"])
    def _body(self, t):    return Paragraph(_c(t), self.S["Body"])
    def _bold(self, t):    return Paragraph(_c(t), self.S["BodyBold"])
    def _note(self, t):    return Paragraph(_c(t), self.S["Note"])

    def _kv_table(self, rows):
        data = [[Paragraph(f"<b>{k}</b>", self.S["FlagCell"]),
                 Paragraph(str(v), self.S["FlagCell"])] for k,v in rows]
        t = Table(data, colWidths=[1.7*inch, 4.9*inch])
        t.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(0,-1), SLATE),
            ("GRID",(0,0),(-1,-1),0.4,BORDER),
            ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
            ("LEFTPADDING",(0,0),(-1,-1),7),("VALIGN",(0,0),(-1,-1),"TOP"),
            ("ROWBACKGROUNDS",(0,0),(-1,-1),[colors.white, SLATE]),
        ]))
        return t

    # ── data gathering ───────────────────────────────────────────────────────
    def _gather(self, db, document_ids):
        bundle = []
        for doc_id in document_ids:
            doc = db.query(Document).filter(Document.document_id == doc_id).first()
            if not doc: continue
            metric = db.query(FinancialMetric).filter(FinancialMetric.document_id == doc_id).first()
            flags  = db.query(RedFlag).filter(RedFlag.document_id == doc_id).all()
            bundle.append({"document": doc, "company": doc.company, "metric": metric, "red_flags": flags})
        return bundle

    # ── COVER ────────────────────────────────────────────────────────────────
    def _cover(self, story, username, bundle, sections):
        banner = Table([[Paragraph(
            "<b>MULTI-AGENT FINANCIAL RESEARCH SYSTEM</b>",
            ParagraphStyle("BT", fontName="Helvetica-Bold", fontSize=7,
                           textColor=colors.HexColor("#C4B5FD"), letterSpacing=2))
        ]], colWidths=[6.6*inch])
        banner.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1), colors.HexColor("#1E1B3C")),
            ("TOPPADDING",(0,0),(-1,-1),10), ("BOTTOMPADDING",(0,0),(-1,-1),10),
            ("LEFTPADDING",(0,0),(-1,-1),14), ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ]))
        story += [banner, self._sp(30),
                  Paragraph("Financial Research &amp; Analyst Brief", self.S["Cover1"]),
                  Paragraph(
                      ", ".join(_c(b["company"].company_name if b["company"] else b["document"].file_name) for b in bundle),
                      self.S["Cover2"]),
                  self._sp(10),
                  self._hr(), self._sp(4)]

        meta = [
            ["Prepared for",  username or "Research Workspace"],
            ["Release Date",  datetime.now().strftime("%B %d, %Y")],
            ["Sections",      ", ".join(sections)],
            ["Agents used",   "Document, Extraction, Red Flag, Comparison, Report"],
            ["Grounding",     "Strictly source-document — no synthetic projections"],
        ]
        story += [self._kv_table(meta), PageBreak()]

    # ── EXECUTIVE SUMMARY ────────────────────────────────────────────────────
    def _exec_summary(self, story, bundle):
        story += [self._h("Section 1"), self._sec("Executive Summary"), self._hr()]

        story.append(self._body(
            "This research brief has been compiled by the Multi-Agent Financial Research System. "
            "The pipeline executed the following sequence: a Document Agent parsed and indexed each "
            "filing into a FAISS vector store; an Extraction Agent retrieved key financial metrics "
            "using a large-language-model pipeline; a Red Flag Agent scanned disclosures for "
            "anomalies; a Comparison Agent benchmarked performance across entities; and this Report "
            "Agent synthesised all outputs into the document you are reading. Every figure and "
            "finding is grounded in the source filings — no external projections have been introduced."
        ))

        for b in bundle:
            co   = b["company"]
            doc  = b["document"]
            m    = b["metric"]
            name = _c(co.company_name if co else doc.file_name)
            sec  = _c(co.industry if co else "—")
            fy   = _c(co.fiscal_year if co else "—")
            n_rf = len(b["red_flags"])

            story += [self._sp(4), self._sub(name)]

            # Build a rich prose paragraph from the metrics
            if m and m.revenue:
                rev_line  = f"Revenue stands at {_f(m.revenue)} with net income of {_f(m.net_income)}."
                ebitda_ln = f"EBITDA is recorded at {_f(m.ebitda)}." if m.ebitda else ""
                margin_ln = ""
                if m.revenue and m.net_income:
                    margin = m.net_income / m.revenue * 100
                    margin_ln = (
                        f"The net profit margin is {margin:.1f}%, which is "
                        + ("healthy and above the 8% threshold." if margin >= 8
                           else "below the 8% threshold, indicating margin pressure.")
                    )
                bal_ln = ""
                if m.total_assets and m.total_liabilities:
                    d2e = m.debt_to_equity or m.total_liabilities / max(m.total_assets - m.total_liabilities, 1)
                    bal_ln = (
                        f"The balance sheet shows total assets of {_f(m.total_assets)} against "
                        f"liabilities of {_f(m.total_liabilities)}, giving a debt-to-equity ratio of "
                        f"{d2e:.2f}x. "
                        + ("This leverage level warrants monitoring." if d2e > 1.5 else
                           "Leverage appears manageable at this level.")
                    )
                prose = " ".join(filter(None, [rev_line, ebitda_ln, margin_ln, bal_ln]))
            else:
                prose = "Financial metrics for this entity are being processed by the Extraction Agent."

            story.append(self._body(
                f"Sector: {sec} | Fiscal Year: {fy} | Source: {_c(doc.file_name)} | "
                f"Red flags identified: {n_rf}. {prose}"
            ))

        story.append(self._sp(8))

    # ── KEY FINANCIALS ───────────────────────────────────────────────────────
    def _key_financials(self, story, bundle):
        story += [self._h("Section 2"), self._sec("Key Financials"), self._hr()]

        story.append(self._body(
            "The Extraction Agent retrieved the following headline financial figures directly from "
            "each filing's income statement and balance sheet. All values are expressed in the "
            "currency and unit reported in the source document. Where a metric could not be "
            "located in the filing, the field is shown as a dash."
        ))

        # Metrics comparison table
        headers = ["Metric"] + [
            _c((b["company"].company_name if b["company"] else b["document"].file_name)[:18])
            for b in bundle
        ]
        rows_def = [
            ("Revenue",           lambda m: _f(m.revenue if m else None)),
            ("Net Income",        lambda m: _f(m.net_income if m else None)),
            ("EBITDA",            lambda m: _f(m.ebitda if m else None)),
            ("Total Assets",      lambda m: _f(m.total_assets if m else None)),
            ("Total Liabilities", lambda m: _f(m.total_liabilities if m else None)),
            ("EPS",               lambda m: _f(m.eps if m else None)),
            ("Debt / Equity",     lambda m: f"{m.debt_to_equity:.2f}x" if m and m.debt_to_equity else "—"),
            ("Net Margin",        lambda m: _pct(m.net_income, m.revenue) if m else "—"),
        ]
        data = [headers]
        for label, fn in rows_def:
            data.append([label] + [fn(b["metric"]) for b in bundle])

        n = max(len(bundle), 1)
        cw = [1.9*inch] + [round(4.7/n, 2)*inch]*n
        tbl = Table(data, colWidths=cw)
        tbl.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0), colors.HexColor("#1E1B3C")),
            ("TEXTCOLOR",(0,0),(-1,0), colors.white),
            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
            ("FONTNAME",(0,1),(0,-1),"Helvetica-Bold"),
            ("FONTNAME",(1,1),(-1,-1),"Helvetica"),
            ("FONTSIZE",(0,0),(-1,-1),8.5),
            ("TEXTCOLOR",(0,1),(-1,-1), MUTED),
            ("GRID",(0,0),(-1,-1),0.4,BORDER),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, SLATE]),
            ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
            ("LEFTPADDING",(0,0),(-1,-1),8),("ALIGN",(1,1),(-1,-1),"RIGHT"),
        ]))
        story += [tbl, self._sp(8)]

        # Prose interpretation per entity
        for b in bundle:
            m    = b["metric"]
            co   = b["company"]
            doc  = b["document"]
            name = _c(co.company_name if co else doc.file_name)
            if not m or not m.revenue: continue

            story.append(self._sub(f"{name} — Financial Commentary"))

            rev    = m.revenue
            ni     = m.net_income or 0
            eb     = m.ebitda or 0
            ta     = m.total_assets or 0
            tl     = m.total_liabilities or 0
            ep     = m.eps or 0
            d2e    = m.debt_to_equity or (tl / max(ta - tl, 1))
            margin = ni / rev * 100 if rev else 0

            para1 = (
                f"{name} reported revenue of {_f(rev)}, reflecting the company's top-line "
                f"performance for the reporting period. Net income came in at {_f(ni)}, translating "
                f"to a net profit margin of {margin:.1f}%. "
                + ("This margin is above the 8% benchmark, indicating solid profitability. "
                   if margin >= 8 else
                   "This margin is below the 8% benchmark, suggesting profitability headwinds that management should address. ")
            )
            story.append(self._body(para1))

            if eb:
                ebitda_margin = eb / rev * 100 if rev else 0
                para2 = (
                    f"EBITDA stands at {_f(eb)}, representing an EBITDA margin of {ebitda_margin:.1f}%. "
                    "EBITDA is a proxy for operating cash generation before financing costs and non-cash "
                    "charges, and provides a cleaner picture of operational performance than reported "
                    "net income alone. "
                )
                story.append(self._body(para2))

            if ta:
                para3 = (
                    f"On the balance sheet, total assets are reported at {_f(ta)} against total "
                    f"liabilities of {_f(tl)}. The resulting debt-to-equity ratio of {d2e:.2f}x "
                    + ("is above 1.5x, signalling elevated financial leverage and potential solvency risk "
                       "under adverse conditions. "
                       if d2e > 1.5 else
                       "remains at a manageable level, suggesting the company is not over-leveraged "
                       "at this stage. ")
                )
                story.append(self._body(para3))

            if ep:
                story.append(self._body(
                    f"Earnings per share (EPS) is reported at {_f(ep)}, which provides the per-share "
                    "earnings attributable to common shareholders. This figure is a key input for "
                    "valuation multiples and shareholder return analysis."
                ))
        story.append(self._sp(8))

    # ── RED FLAGS & RISKS ────────────────────────────────────────────────────
    def _red_flags(self, story, bundle):
        story += [self._h("Section 3"), self._sec("Red Flags & Risks"), self._hr()]

        story.append(self._body(
            "The Red Flag Agent conducted an automated scan of each filing's financial disclosures, "
            "balance sheet ratios, and management commentary. The agent applies a deterministic rule "
            "engine across eight risk categories — leverage, margin compression, going concern "
            "qualifications, material weakness disclosures, litigation exposure, working capital "
            "deterioration, dividend sustainability, and client concentration — supplemented by a "
            "qualitative LLM scan for nuanced risk language. Each finding is graded HIGH, MEDIUM, "
            "or LOW based on severity thresholds."
        ))

        any_flags = False
        for b in bundle:
            co    = b["company"]
            doc   = b["document"]
            name  = _c(co.company_name if co else doc.file_name)
            flags = b["red_flags"]
            if not flags: continue
            any_flags = True

            story += [self._sp(4), self._sub(f"{name} — Risk Findings")]

            # Prose introduction
            high_count   = sum(1 for f in flags if f.severity.lower() == "high")
            medium_count = sum(1 for f in flags if f.severity.lower() == "medium")
            low_count    = sum(1 for f in flags if f.severity.lower() == "low")

            intro = (
                f"The Red Flag Agent identified {len(flags)} risk indicator{'s' if len(flags)!=1 else ''} "
                f"for {name}: {high_count} high-severity, {medium_count} medium-severity, "
                f"and {low_count} low-severity. "
            )
            if high_count > 0:
                intro += (
                    "The presence of high-severity findings warrants immediate attention from "
                    "management and investors. These indicators may affect the entity's "
                    "creditworthiness, operational continuity, or regulatory standing."
                )
            elif medium_count > 0:
                intro += (
                    "While no high-severity risks were detected, the medium-severity indicators "
                    "should be monitored closely over the coming reporting periods."
                )
            else:
                intro += (
                    "All identified risks are low-severity, which is a positive signal for the "
                    "financial health and disclosure quality of the entity."
                )
            story.append(self._body(intro))

            # Detail each flag as a prose paragraph
            for f in flags:
                sev_color = SEV_COLORS.get(f.severity.lower(), MUTED)
                sev_label = f.severity.upper()
                story.append(KeepTogether([
                    Paragraph(
                        f'<font color="#{sev_color.hexval().replace("0x", "").replace("0X", "") if hasattr(sev_color,"hexval") else "475569"}"><b>[{sev_label}] {_c(f.risk_type)}</b></font>',
                        self.S["BodyBold"]
                    ),
                    self._body(
                        _c(f.description) + " This finding was detected programmatically from "
                        "the extracted financial data and filing disclosures, and should be "
                        "cross-referenced with the original source document for full context."
                    ),
                ]))

        if not any_flags:
            story.append(self._body(
                "The Red Flag Agent did not surface any material risk indicators across the "
                "selected documents. This outcome suggests that the reported financial metrics "
                "fall within acceptable thresholds and no unusual disclosure language was detected. "
                "Note that automated scanning cannot replace a thorough manual review by a "
                "qualified financial analyst."
            ))
        story.append(self._sp(8))

    # ── COMPANY COMPARISON ───────────────────────────────────────────────────
    def _comparison(self, story, db, document_ids, bundle):
        story += [self._h("Section 4"), self._sec("Company Comparison"), self._hr()]

        if len(document_ids) < 2:
            story.append(self._body(
                "A comparative analysis requires at least two documents. This report was generated "
                "from a single filing; therefore, the benchmarking section is not applicable. To "
                "enable peer comparison, generate a new report with two or more filings selected."
            ))
            return

        try:
            result = self.comparison_agent.compare(db, document_ids, DEFAULT_METRIC)
        except Exception:
            story.append(self._body("Comparison could not be computed for the selected documents."))
            return

        metric_name = result["metric"]
        story.append(self._body(
            f"The Comparison Agent benchmarked {len(document_ids)} entities across the '{metric_name}' "
            "metric. This metric was selected as the primary comparator because it provides a "
            "standardised view of operational profitability and efficiency across different company "
            "structures and reporting styles. The values below are computed directly from the "
            "financial metrics extracted by the Extraction Agent — no external data sources were "
            "consulted."
        ))

        # Comparison table
        data = [["Company / Entity", metric_name, "Relative Position"]]
        rows = result["rows"]
        if rows:
            max_val = max((r["value"] or 0) for r in rows)
            for row in rows:
                val    = row["value"]
                pos    = "Leader" if val and val == max_val else ("Lagging" if val and val < max_val * 0.7 else "In range")
                data.append([_c(row["company"]), f"{val:.2f}" if val else "—", pos])

        tbl = Table(data, colWidths=[2.8*inch, 2.2*inch, 1.6*inch])
        tbl.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0), colors.HexColor("#1E1B3C")),
            ("TEXTCOLOR",(0,0),(-1,0), colors.white),
            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
            ("FONTNAME",(0,1),(-1,-1),"Helvetica"),
            ("FONTSIZE",(0,0),(-1,-1),9),
            ("GRID",(0,0),(-1,-1),0.4,BORDER),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,SLATE]),
            ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
            ("LEFTPADDING",(0,0),(-1,-1),8),("ALIGN",(1,1),(-1,-1),"CENTER"),
        ]))
        story += [tbl, self._sp(6)]

        # Prose narrative
        if rows and len(rows) >= 2:
            best  = max(rows, key=lambda r: r["value"] or 0)
            worst = min(rows, key=lambda r: r["value"] or 0)
            spread = (best["value"] or 0) - (worst["value"] or 0)
            story.append(self._body(
                f"{_c(best['company'])} leads the peer group on {metric_name} with a value of "
                f"{best['value']:.2f}, while {_c(worst['company'])} records the lowest figure at "
                f"{worst['value']:.2f}. The spread of {spread:.2f} percentage points across the "
                "peer group indicates "
                + ("a significant variance in operational efficiency, which may reflect differences "
                   "in business mix, pricing power, or cost structure. "
                   if spread > 5 else
                   "a relatively tight clustering of performance, suggesting comparable operational "
                   "profiles across the entities reviewed. ")
                + "Investors and analysts should investigate the underlying drivers of divergence, "
                "including sector dynamics, capital allocation decisions, and management commentary "
                "from each respective filing."
            ))
        story.append(self._note(result["citation"]["section"]))
        story.append(self._sp(8))

    # ── OUTLOOK ──────────────────────────────────────────────────────────────
    def _outlook(self, story, bundle):
        story += [self._h("Section 5"), self._sec("Outlook"), self._hr()]

        story.append(self._body(
            "The following forward-looking assessment is synthesised exclusively from the metrics, "
            "red flag findings, and financial ratios already extracted above. No external market "
            "data, analyst forecasts, or generative projections have been introduced. The outlook "
            "reflects the current state of disclosures as captured in the indexed filings."
        ))

        for b in bundle:
            co    = b["company"]
            doc   = b["document"]
            m     = b["metric"]
            flags = b["red_flags"]
            name  = _c(co.company_name if co else doc.file_name)

            story += [self._sp(4), self._sub(f"{name} — Forward Assessment")]

            high_flags   = [f for f in flags if f.severity.lower() == "high"]
            medium_flags = [f for f in flags if f.severity.lower() == "medium"]

            # Financial health assessment
            if m and m.revenue:
                margin = (m.net_income or 0) / m.revenue * 100 if m.revenue else 0
                d2e    = m.debt_to_equity or ((m.total_liabilities or 0) / max((m.total_assets or 1) - (m.total_liabilities or 0), 1))

                health = "strong" if margin >= 8 and d2e < 1.5 else ("mixed" if margin >= 5 or d2e < 2.0 else "weak")
                story.append(self._body(
                    f"Based on the extracted financials, {name}'s overall financial health appears "
                    f"{health}. The entity's net margin of {margin:.1f}% and debt-to-equity ratio "
                    f"of {d2e:.2f}x are the primary determinants of this assessment. "
                    + ("Sustaining current margin levels while managing leverage will be critical "
                       "to preserving financial flexibility in the near term. "
                       if health == "strong" else
                       "Management's ability to expand margins and reduce leverage exposure will be "
                       "key to improving the financial profile in subsequent periods. ")
                ))

            # Risk-driven narrative
            if high_flags:
                watch_items = "; ".join(_c(f.risk_type) for f in high_flags[:3])
                story.append(self._body(
                    f"The primary watch items for {name} are: {watch_items}. These high-severity "
                    "findings represent material risks that require proactive management response. "
                    "Failure to address these indicators could adversely impact the entity's credit "
                    "profile, operational continuity, or investor confidence."
                ))
            elif medium_flags:
                story.append(self._body(
                    f"While no high-severity risks were identified for {name}, the medium-severity "
                    f"indicators — including {_c(medium_flags[0].risk_type)} — merit ongoing "
                    "monitoring. These items, if left unaddressed, could escalate to higher-severity "
                    "concerns in future reporting periods."
                ))
            else:
                story.append(self._body(
                    f"No material risk flags were raised for {name} during the automated scan. "
                    "This is a positive indicator of disclosure quality and financial stability, "
                    "though it should be interpreted alongside a full manual review of the filing."
                ))

        # Disclaimer
        story += [self._sp(8)]
        disc_box = Table([[Paragraph(
            "<b>Citation Grounding Disclaimer</b><br/><br/>"
            "All statements, figures, and assessments in this report are derived exclusively from "
            "data extracted by the Document Agent, Extraction Agent, and Red Flag Agent from the "
            "source filings. No generative projections, external market data, or analyst estimates "
            "have been incorporated. This report is intended for research and educational purposes "
            "and does not constitute investment advice. Readers should perform independent due "
            "diligence and consult a qualified financial professional before making any investment "
            "or credit decisions based on this document.",
            self.S["Body"]
        )]], colWidths=[6.3*inch])
        disc_box.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1), colors.HexColor("#FFFBEB")),
            ("BOX",(0,0),(-1,-1),0.8, colors.HexColor("#FDE68A")),
            ("TOPPADDING",(0,0),(-1,-1),12),("BOTTOMPADDING",(0,0),(-1,-1),12),
            ("LEFTPADDING",(0,0),(-1,-1),14),("RIGHTPADDING",(0,0),(-1,-1),14),
        ]))
        story.append(disc_box)

    # ── PUBLIC ENTRY POINT ───────────────────────────────────────────────────
    def generate(self, db: Session, user_id: int, username: str,
                 document_ids: List[int], sections: Optional[List[str]] = None,
                 title: Optional[str] = None) -> Report:

        sections = [s for s in (sections or ALL_SECTIONS) if s in ALL_SECTIONS] or ALL_SECTIONS
        bundle   = self._gather(db, document_ids)
        if not bundle:
            raise ValueError("None of the requested document_ids were found.")

        out_dir  = REPORTS_ROOT / f"user_{user_id}"
        out_dir.mkdir(parents=True, exist_ok=True)
        fname    = f"report_{int(datetime.now().timestamp())}.pdf"
        out_path = out_dir / fname

        names        = [b["company"].company_name if b["company"] else b["document"].file_name for b in bundle]
        report_title = title or (" vs ".join(n.split(" ")[0] for n in names) + " — Research Brief")

        pdf_doc = SimpleDocTemplate(
            str(out_path), pagesize=LETTER,
            leftMargin=0.9*inch, rightMargin=0.9*inch,
            topMargin=0.9*inch,  bottomMargin=0.9*inch,
            title=report_title,
        )

        story = []
        self._cover(story, username, bundle, sections)

        builders = {
            "Executive Summary":  lambda: self._exec_summary(story, bundle),
            "Key Financials":     lambda: self._key_financials(story, bundle),
            "Red Flags & Risks":  lambda: self._red_flags(story, bundle),
            "Company Comparison": lambda: self._comparison(story, db, document_ids, bundle),
            "Outlook":            lambda: self._outlook(story, bundle),
        }
        for i, sec in enumerate(sections):
            builders[sec]()
            if i < len(sections) - 1:
                story.append(PageBreak())

        pdf_doc.build(story)

        report = Report(user_id=user_id, report_title=report_title, report_path=str(out_path))
        for attr, val in [
            ("document_ids", ",".join(str(d) for d in document_ids)),
            ("status",  "ready"),
            ("pages",   len(sections)),
            ("sections",",".join(sections)),
        ]:
            if hasattr(Report, attr): setattr(report, attr, val)

        db.add(report)
        db.commit()
        db.refresh(report)
        return report
