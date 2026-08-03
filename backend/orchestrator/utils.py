"""
Glue helpers that translate the Extraction Agent's output shape into what the
Red Flag Agent expects, and into the flat, display-friendly shape the
frontend wants for metrics.
"""
from __future__ import annotations

from typing import Any, Optional

from config import settings

# Metric field names the Extraction Agent may populate on `financial_data`.
METRIC_FIELDS = [
    "revenue", "gross_revenue", "gross_profit", "operating_income", "ebit",
    "ebitda", "net_income", "net_profit", "eps", "assets", "current_assets",
    "non_current_assets", "liabilities", "current_liabilities", "long_term_debt",
    "debt", "equity", "cash", "cash_equivalents", "cash_flow",
    "operating_cash_flow", "investing_cash_flow", "financing_cash_flow",
    "free_cash_flow", "capital_expenditure", "inventory", "receivables",
    "payables", "working_capital", "tax_expense", "interest_expense",
    "operating_margin", "gross_margin", "net_margin", "roa", "roe",
    "current_ratio", "quick_ratio", "debt_to_equity", "employees",
]

RATIO_FIELDS = {
    "operating_margin", "gross_margin", "net_margin", "roa", "roe",
    "current_ratio", "quick_ratio", "debt_to_equity",
}


def _metric_dict(financial_data: dict[str, Any], field: str) -> Optional[dict[str, Any]]:
    value = financial_data.get(field)
    if not value:
        return None
    if isinstance(value, dict):
        return value
    return {"value": value}


def _all_metric_items(financial_data: dict[str, Any]) -> list[dict[str, Any]]:
    """
    The Extraction Agent returns two views of the same facts: a handful of
    fixed, canonical fields (financial_data["revenue"], ["ebitda"], ...) AND
    the FULL list of everything it found, under financial_data["metrics"]
    (or the legacy alias "all_financial_values"). The canonical fields only
    cover ~15 well-known labels — anything the LLM extracted under a label
    that doesn't map to one of those (Dividend Payout Ratio, Contingent
    Liabilities, Goodwill, TCV, Revenue Growth, etc.) only exists in this
    full list. Both build_redflag_metrics and build_display_metrics need to
    read from here, not just the named fields, or most of what the
    Extraction Agent actually found never reaches the Red Flag Agent or the
    dashboard.
    """
    items = financial_data.get("metrics") or financial_data.get("all_financial_values") or []
    return [item for item in items if isinstance(item, dict) and item.get("value") not in (None, "")]


def _slugify_label(label: str) -> str:
    """Turn a free-text metric label like 'Dividend Payout Ratio' into a
    stable dict key like 'dividend_payout_ratio', matching the style of the
    canonical METRIC_FIELDS names."""
    import re

    slug = re.sub(r"[^a-z0-9]+", "_", label.strip().lower()).strip("_")
    return slug or "metric"


def build_redflag_metrics(financial_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """
    Convert Extraction Agent `financial_data` (dict of FinancialMetricValue-shaped
    objects) into the flexible `metrics` mapping the Red Flag Agent's
    `RedFlagRequest.metrics: dict[str, FinancialMetric]` accepts.
    """
    metrics: dict[str, dict[str, Any]] = {}
    for field in METRIC_FIELDS:
        raw = _metric_dict(financial_data, field)
        if raw is None:
            continue

        value = raw.get("normalized_value")
        if value is None:
            value = raw.get("value")
        if value is None:
            value = raw.get("raw_value")
        if value is None:
            continue

        entry: dict[str, Any] = {"value": value}
        if raw.get("unit") or raw.get("scale"):
            entry["unit"] = raw.get("unit") or raw.get("scale")
        if raw.get("period"):
            entry["source"] = raw.get("period")
        elif raw.get("source_text"):
            entry["source"] = raw.get("source_text")
        metrics[field] = entry

    # The named fields above only cover ~15 canonical labels. Everything
    # else the Extraction Agent found (payout ratios, contingent
    # liabilities, goodwill, TCV, revenue growth, ad hoc margins, ...) only
    # exists in the full metrics array — without this, the Red Flag Agent
    # never sees the majority of what was actually extracted from the
    # document, and under-flags as a result.
    for item in _all_metric_items(financial_data):
        label = item.get("metric")
        if not label:
            continue
        key = _slugify_label(label)
        if key in metrics:
            continue  # a canonical field already covers this metric
        entry = {"value": item.get("value")}
        if item.get("unit"):
            entry["unit"] = item.get("unit")
        if item.get("period"):
            entry["source"] = item.get("period")
        if item.get("page_number") is not None:
            entry["page_number"] = item.get("page_number")
        metrics[key] = entry

    return metrics


def format_metric_display(financial_data: dict[str, Any], field: str) -> Optional[str]:
    """Render a single metric as a short human-readable string for the UI."""
    raw = _metric_dict(financial_data, field)
    if raw is None:
        return None

    value = raw.get("raw_value") or raw.get("value")
    if value is None and raw.get("normalized_value") is not None:
        value = raw.get("normalized_value")
    if value is None:
        return None

    text = str(value)
    suffix_parts = []
    if raw.get("currency"):
        suffix_parts.append(str(raw["currency"]))
    if raw.get("scale"):
        suffix_parts.append(str(raw["scale"]))
    if suffix_parts:
        text = f"{text} ({', '.join(suffix_parts)})"
    return text


def build_display_metrics(financial_data: dict[str, Any] | None) -> dict[str, Any]:
    """Build the flat {revenue, net_profit, ebitda, eps, assets, liabilities,
    cash_flow, ratios, other_metrics} shape the frontend's DocumentMetrics
    expects."""
    if not financial_data:
        return {"ratios": {}, "other_metrics": []}

    net_profit = format_metric_display(financial_data, "net_profit") or format_metric_display(
        financial_data, "net_income"
    )

    ratios: dict[str, str] = {}
    for field in RATIO_FIELDS:
        display = format_metric_display(financial_data, field)
        if display:
            ratios[field] = display

    # Named fields above only cover ~15 canonical labels. Surface everything
    # else the Extraction Agent found (payout ratios, contingent
    # liabilities, goodwill, capex, dividends, TCV, ad hoc margins, ...) so
    # the dashboard shows what was actually extracted, not a fixed subset.
    covered_labels = {"revenue", "net_profit", "net_income", "ebitda", "eps", "assets", "liabilities", "cash_flow"} | RATIO_FIELDS
    seen_keys: set[str] = set()
    other_metrics: list[dict[str, str]] = []
    for item in _all_metric_items(financial_data):
        label = item.get("metric")
        if not label:
            continue
        key = _slugify_label(label)
        if key in covered_labels or key in seen_keys:
            continue
        seen_keys.add(key)
        value = str(item.get("value"))
        if item.get("unit"):
            value = f"{value} {item['unit']}"
        other_metrics.append({"label": label, "value": value})

    return {
        "revenue": format_metric_display(financial_data, "revenue"),
        "net_profit": net_profit,
        "ebitda": format_metric_display(financial_data, "ebitda"),
        "eps": format_metric_display(financial_data, "eps"),
        "assets": format_metric_display(financial_data, "assets"),
        "liabilities": format_metric_display(financial_data, "liabilities"),
        "cash_flow": format_metric_display(financial_data, "cash_flow"),
        "ratios": ratios,
        "other_metrics": other_metrics,
    }


# --------------------------------------------------------------------------- #
# Document sections for qualitative red-flag analysis
# --------------------------------------------------------------------------- #

# Representative queries used to pull qualitative context (auditor notes, risk
# factors, litigation, etc.) out of the Document Agent's vector index for the
# freshly uploaded document, since the Red Flag Agent's LLM analyzer wants
# `document_sections` in addition to numeric `metrics`.
SECTION_QUERIES = [
    "risk factors and litigation",
    "auditor opinion and going concern",
    "management discussion of risks and uncertainties",
    "debt covenants and borrowing arrangements",
    "related party transactions",
]


def build_document_sections(
    document_agent,
    session_id: str,
    document_id: str,
    company_name: str,
    max_sections: int = 8,
    max_chars_per_section: int = 1500,
) -> list[dict[str, str]]:
    """Pull a handful of qualitative chunks scoped to one document for the
    Red Flag Agent's `document_sections` field."""
    sections: list[dict[str, str]] = []
    seen_chunks: set[tuple[Any, Any]] = set()

    for query in SECTION_QUERIES:
        hits = document_agent.search(
            session_id=session_id,
            query=query,
            k=2,
            document_id_filter=document_id,
        )
        for hit in hits:
            key = (hit.get("page_number"), hit.get("chunk_index"))
            if key in seen_chunks:
                continue
            seen_chunks.add(key)
            text = (hit.get("text") or "").strip()
            if not text:
                continue
            label = f"{company_name} — p.{hit.get('page_number', '?')}"
            sections.append({"section": label[:160], "content": text[:max_chars_per_section]})
            if len(sections) >= max_sections:
                return sections
    return sections


def resolve_company_and_year(financial_data: dict[str, Any] | None) -> tuple[str, str]:
    financial_data = financial_data or {}
    company = (financial_data.get("company_name") or "").strip() or settings.default_company_name
    year = (
        financial_data.get("financial_year") or financial_data.get("fiscal_period") or ""
    ).strip() or settings.default_financial_year
    return company, year
