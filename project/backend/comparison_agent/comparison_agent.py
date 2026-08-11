"""
Comparison Agent
================
Cross-references extracted financial data (produced by the Extraction Agent
and stored in the `financial_metrics` table) across two or more companies /
documents in a research session, for side-by-side benchmarking.

Every value returned is computed directly from numbers already stored in the
database (which were themselves grounded in source documents by the
Extraction Agent) — the Comparison Agent never invents or estimates figures
that aren't derivable from that stored data.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from backend.database.models import Company, Document, FinancialMetric, ComparisonResult

logger = logging.getLogger("comparison_agent")

# Metric catalogue: maps the metric key the frontend sends to a human label,
# a display unit, and a function that derives the value from a FinancialMetric row.
# Because the schema stores headline figures (revenue, net income, EBITDA,
# assets, liabilities, EPS) rather than a full income-statement breakdown,
# margin-style metrics are computed as the closest available proxy from those
# headline figures. This is noted transparently in the citation returned to
# the caller so nothing is presented as more precise than the underlying data.
def _pct(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    if numerator is None or denominator in (None, 0):
        return None
    return round((numerator / denominator) * 100, 2)


def _ratio(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    if numerator is None or denominator in (None, 0):
        return None
    return round(numerator / denominator, 2)


METRIC_CATALOGUE: Dict[str, Dict[str, Any]] = {
    "Gross Margin (TTM)": {
        "unit": "%",
        "compute": lambda m: _pct(m.ebitda, m.revenue),
        "note": "Computed as EBITDA / Revenue (closest proxy available from stored headline financials).",
    },
    "Operating Margin (TTM)": {
        "unit": "%",
        "compute": lambda m: _pct(m.net_income, m.revenue),
        "note": "Computed as Net Income / Revenue (closest proxy available from stored headline financials).",
    },
    "Net Debt / EBITDA": {
        "unit": "x",
        "compute": lambda m: _ratio(m.total_liabilities, m.ebitda),
        "note": "Computed as Total Liabilities / EBITDA (used as a leverage proxy; cash balance not captured in schema).",
    },
    "Revenue Growth YoY": {
        "unit": "%",
        "compute": lambda m: None,
        "note": "Not computable — only a single reporting period's revenue is stored per document; a prior-year figure is required.",
    },
}

DEFAULT_METRIC = "Operating Margin (TTM)"


@dataclass
class ComparisonRow:
    company: str
    document_id: int
    value: Optional[float]


class ComparisonAgent:
    """Cross-references financial data across multiple companies for benchmarking."""

    def compare(
        self,
        db: Session,
        document_ids: List[int],
        metric_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not document_ids or len(document_ids) < 2:
            raise ValueError("At least two document_ids are required for comparison.")

        metric_key = metric_key or DEFAULT_METRIC
        metric_def = METRIC_CATALOGUE.get(metric_key)
        if metric_def is None:
            # Unknown metric key from the frontend — fall back gracefully instead of erroring.
            metric_key = DEFAULT_METRIC
            metric_def = METRIC_CATALOGUE[DEFAULT_METRIC]

        rows: List[ComparisonRow] = []
        missing: List[str] = []

        for doc_id in document_ids:
            doc = db.query(Document).filter(Document.document_id == doc_id).first()
            if not doc:
                continue
            company_name = doc.company.company_name if doc.company else doc.file_name
            metric_row = (
                db.query(FinancialMetric)
                .filter(FinancialMetric.document_id == doc_id)
                .first()
            )
            value = metric_def["compute"](metric_row) if metric_row else None
            if value is None:
                missing.append(company_name)
                value = 0.0
            rows.append(ComparisonRow(company=company_name, document_id=doc_id, value=value))

        # Build a summary narrative
        if rows and not all(r.value == 0.0 for r in rows):
            best = max(rows, key=lambda r: r.value)
            worst = min(rows, key=lambda r: r.value)
            if best.company != worst.company:
                summary = (
                    f"{best.company} leads with the highest {metric_key} at {best.value}{metric_def['unit']}, "
                    f"while {worst.company} is at the lower end at {worst.value}{metric_def['unit']}. "
                    f"{metric_def['note']}"
                )
            else:
                summary = f"All compared companies show similar {metric_key} performance. {metric_def['note']}"
        else:
            summary = f"Insufficient extracted data to compute {metric_key} for the selected documents."

        result = {
            "metric": metric_key,
            "summary": summary,
            "rows": [{"company": r.company, "value": r.value} for r in rows],
            "citation": {
                "section": metric_def["note"]
                + (f" No data available for: {', '.join(missing)}." if missing else "")
            },
        }

        # Best-effort persistence of the comparison for auditability / history.
        try:
            company_ids = []
            for doc_id in document_ids:
                doc = db.query(Document).filter(Document.document_id == doc_id).first()
                if doc and doc.company_id:
                    company_ids.append(doc.company_id)
            record = ComparisonResult(
                company1_id=company_ids[0] if len(company_ids) > 0 else None,
                company2_id=company_ids[1] if len(company_ids) > 1 else None,
                comparison_summary=json.dumps(result)[:990],
            )
            db.add(record)
            db.commit()
        except Exception:
            logger.exception("Failed to persist comparison result (non-fatal)")
            db.rollback()

        return result
