"""
comparison_agent.py

The Comparison Agent from the Multi-Agent Financial Research System.

Position in the pipeline (per the project design doc):
    Extraction Agent --> Red Flag Agent --> [COMPARISON AGENT] --> Research Agent --> Report Agent

Responsibilities (from the design doc, Section 5.4):
    - Compare multiple companies / documents
    - Compare revenue, profit, debt, margins, DSO, FCF/PAT, attrition
    - Benchmark performance side-by-side
    - Output: side-by-side company comparison (ComparisonResult)
"""

from __future__ import annotations
import os
import statistics
from typing import List, Optional

from schemas import CompanyMetrics, MetricComparison, ComparisonResult
from pdf_extractor import extract_company_metrics_from_pdf

# ---------------------------------------------------------------------------
# 1. Metric definitions: which fields to compare, their unit, and whether a
#    higher number is better (DSO and attrition are "lower is better").
# ---------------------------------------------------------------------------
METRIC_DEFINITIONS = [
    ("revenue_cr", "Revenue (Rs cr)", True),
    ("revenue_growth_cc_pct", "CC Revenue Growth (%)", True),
    ("ebit_margin_pct", "EBIT Margin (%)", True),
    ("pat_margin_pct", "PAT Margin (%)", True),
    ("roe_pct", "Return on Equity (%)", True),
    ("roce_pct", "Return on Capital Employed (%)", True),
    ("dso_days", "Days Sales Outstanding (days)", False),
    ("fcf_to_pat_pct", "FCF / PAT (%)", True),
    ("revenue_per_employee_lakh", "Revenue per Employee (Rs lakh)", True),
    ("attrition_rate_pct", "Attrition Rate (%)", False),
]

UNDERPERFORM_THRESHOLD_PCT = 5.0   # >5% worse than peer avg -> underperform
OUTPERFORM_THRESHOLD_PCT = 5.0     # >5% better than peer avg -> outperform


class ComparisonAgent:
    def __init__(self, use_llm: bool = True):
        """
        use_llm: if True, attempt to use ChatGroq (langchain_groq) for the
        narrative summary, provided GROQ_API_KEY is set in the environment.
        Falls back to a rule-based templated narrative if unavailable.
        """
        self.use_llm = use_llm
        self._llm = None
        if use_llm and os.environ.get("GROQ_API_KEY"):
            try:
                from langchain_groq import ChatGroq
                self._llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2)
            except Exception:
                self._llm = None

    # -----------------------------------------------------------------
    # Public entry points
    # -----------------------------------------------------------------
    def compare(self, companies: List[CompanyMetrics], focus_company: str) -> ComparisonResult:
        if len(companies) < 2:
            raise ValueError("Comparison Agent needs at least 2 companies (focus + peers).")

        focus = next((c for c in companies if c.company_name == focus_company), None)
        if focus is None:
            # Fallback to first company if exact match not found
            focus = companies[0]
            focus_company = focus.company_name

        peers = [c for c in companies if c.company_name != focus_company]

        metric_comparisons: List[MetricComparison] = []
        for field, label, higher_better in METRIC_DEFINITIONS:
            metric_comparisons.append(
                self._compare_metric(field, label, higher_better, focus, peers, companies)
            )

        strengths = [m.metric for m in metric_comparisons if m.flag == "outperform"]
        weaknesses = [m.metric for m in metric_comparisons if m.flag == "underperform"]

        narrative = self._generate_narrative(focus, peers, metric_comparisons, strengths, weaknesses)

        return ComparisonResult(
            focus_company=focus_company,
            fiscal_year=focus.fiscal_year,
            companies_compared=[c.company_name for c in companies],
            metric_comparisons=metric_comparisons,
            narrative_summary=narrative,
            key_strengths=strengths,
            key_weaknesses=weaknesses,
        )

    def compare_documents(self, pdf_paths: List[str], focus_company: Optional[str] = None) -> ComparisonResult:
        """Extracts metrics from multiple PDF documents and runs comparison."""
        companies = [extract_company_metrics_from_pdf(p) for p in pdf_paths]
        if not focus_company:
            focus_company = companies[0].company_name
        return self.compare(companies, focus_company=focus_company)

    def compare_two_documents(self, pdf_path1: str, pdf_path2: str, focus_company: Optional[str] = None) -> ComparisonResult:
        """Convenience method for pairwise document comparison."""
        return self.compare_documents([pdf_path1, pdf_path2], focus_company=focus_company)

    # -----------------------------------------------------------------
    # Internals
    # -----------------------------------------------------------------
    def _compare_metric(self, field, label, higher_better, focus, peers, all_companies) -> MetricComparison:
        focus_val = getattr(focus, field)
        peer_vals = {p.company_name: getattr(p, field) for p in peers if getattr(p, field) is not None}

        if focus_val is None or not peer_vals:
            return MetricComparison(
                metric=label, unit="", higher_is_better=higher_better,
                focus_company_value=focus_val, peer_values=peer_vals,
                peer_average=None, focus_vs_peer_avg_pct=None,
                focus_rank=None, total_ranked=0, flag="no_data",
            )

        peer_avg = statistics.mean(peer_vals.values())
        pct_diff = ((focus_val - peer_avg) / abs(peer_avg)) * 100 if peer_avg != 0 else None

        # Rank across ALL companies (focus + peers) for this metric
        ranked_vals = [(c.company_name, getattr(c, field)) for c in all_companies if getattr(c, field) is not None]
        ranked_vals.sort(key=lambda x: x[1], reverse=higher_better)
        rank = next((i + 1 for i, (name, _) in enumerate(ranked_vals) if name == focus.company_name), None)

        if pct_diff is None:
            flag = "no_data"
        else:
            effective_diff = pct_diff if higher_better else -pct_diff
            if effective_diff >= OUTPERFORM_THRESHOLD_PCT:
                flag = "outperform"
            elif effective_diff <= -UNDERPERFORM_THRESHOLD_PCT:
                flag = "underperform"
            else:
                flag = "inline"

        return MetricComparison(
            metric=label, unit="", higher_is_better=higher_better,
            focus_company_value=focus_val, peer_values=peer_vals,
            peer_average=round(peer_avg, 2), focus_vs_peer_avg_pct=round(pct_diff, 1) if pct_diff is not None else None,
            focus_rank=rank, total_ranked=len(ranked_vals), flag=flag,
        )

    def _generate_narrative(self, focus, peers, metric_comparisons, strengths, weaknesses) -> str:
        if self._llm is not None:
            try:
                return self._generate_narrative_llm(focus, metric_comparisons, strengths, weaknesses)
            except Exception:
                pass  # fall through to templated version
        return self._generate_narrative_template(focus, peers, metric_comparisons, strengths, weaknesses)

    def _generate_narrative_llm(self, focus, metric_comparisons, strengths, weaknesses) -> str:
        lines = [
            f"{m.metric}: {focus.company_name}={m.focus_company_value}, "
            f"peer avg={m.peer_average}, rank={m.focus_rank}/{m.total_ranked}, flag={m.flag}"
            for m in metric_comparisons
        ]
        prompt = (
            "You are a financial analyst. Using ONLY the data below, write a "
            "4-6 sentence, neutral, evidence-based comparison of "
            f"{focus.company_name} against its peer group for {focus.fiscal_year}. "
            "Cite specific figures. Do not invent numbers.\n\n" + "\n".join(lines)
        )
        response = self._llm.invoke(prompt)
        return response.content.strip()

    def _generate_narrative_template(self, focus, peers, metric_comparisons, strengths, weaknesses) -> str:
        peer_names = ", ".join(p.company_name for p in peers)
        if len(peers) == 1:
            parts = [
                f"{focus.company_name} was benchmarked directly against peer {peer_names} for {focus.fiscal_year} across {len(metric_comparisons)} metrics."
            ]
        else:
            parts = [
                f"{focus.company_name} was benchmarked against a peer group of {len(peers)} companies ({peer_names}) for {focus.fiscal_year} across {len(metric_comparisons)} metrics."
            ]

        if strengths:
            parts.append(f"Key areas of outperformance vs peer average include {', '.join(strengths)}.")
        if weaknesses:
            parts.append(f"Key areas of underperformance vs peer average include {', '.join(weaknesses)}.")
        if not strengths and not weaknesses:
            parts.append("Overall financial performance remains closely in line with peer benchmarks across most metrics.")

        no_data = [m.metric for m in metric_comparisons if m.flag == "no_data"]
        if no_data:
            parts.append("Insufficient data for metrics: " + ", ".join(no_data) + ".")

        return " ".join(parts)


# ---------------------------------------------------------------------------
# 2. LangGraph node wrapper
# ---------------------------------------------------------------------------
def comparison_agent_node(state: dict) -> dict:
    companies = [CompanyMetrics(**c) for c in state["extracted_metrics"]]
    agent = ComparisonAgent(use_llm=True)
    result = agent.compare(companies, focus_company=state["focus_company"])
    return {**state, "comparison_result": result.model_dump()}
