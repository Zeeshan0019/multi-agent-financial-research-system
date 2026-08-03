from __future__ import annotations

import logging

import httpx

import models
from config import settings
from utils import format_metric_display

logger = logging.getLogger("orchestrator.comparison")


def _company_row(document: models.Document) -> dict:
    financial_data = document.financial_data or {}
    return {
        "document_id": document.id,
        "company_name": document.company_name,
        "revenue": format_metric_display(financial_data, "revenue"),
        "net_profit": format_metric_display(financial_data, "net_profit")
        or format_metric_display(financial_data, "net_income"),
        "debt": format_metric_display(financial_data, "debt")
        or format_metric_display(financial_data, "long_term_debt"),
        "margin": format_metric_display(financial_data, "net_margin")
        or format_metric_display(financial_data, "operating_margin"),
    }


def _rule_based_summary(rows: list[dict]) -> str:
    if len(rows) < 2:
        return "Add at least two ready documents to this comparison for a meaningful summary."
    names = ", ".join(r["company_name"] or "Unknown" for r in rows)
    return (
        f"Comparing {names} across revenue, net profit, debt, and margin as extracted "
        "by the Extraction Agent. Values shown as 'Not found' were not confidently "
        "identified in the source document and are excluded from the comparison."
    )


async def _llm_summary(rows: list[dict]) -> str | None:
    if not settings.groq_api_key:
        return None
    table_lines = [
        f"- {r['company_name']}: revenue={r['revenue']}, net_profit={r['net_profit']}, "
        f"debt={r['debt']}, margin={r['margin']}"
        for r in rows
    ]
    prompt = (
        "You are a financial analyst. Given these extracted figures for a set of "
        "companies, write a concise 3-4 sentence comparative summary highlighting "
        "the most notable differences. Do not invent numbers not shown below.\n\n"
        + "\n".join(table_lines)
    )
    try:
        async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
            resp = await client.post(
                f"{settings.groq_api_base}/chat/completions",
                json={
                    "model": settings.groq_model,
                    "temperature": 0.2,
                    "messages": [{"role": "user", "content": prompt}],
                },
                headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as exc:  # noqa: BLE001
        logger.warning("LLM comparison summary failed, using rule-based summary: %s", exc)
        return None


async def compare_documents(documents: list[models.Document]) -> tuple[list[dict], str]:
    rows = [_company_row(doc) for doc in documents]
    summary = await _llm_summary(rows) or _rule_based_summary(rows)
    return rows, summary
