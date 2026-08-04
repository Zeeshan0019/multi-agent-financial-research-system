"""
schemas.py
Pydantic models shared by the Extraction Agent -> Comparison Agent -> Report Agent
pipeline. These mirror the "Financial Metrics" collection described in the
project design doc (Section 6: MongoDB Usage).
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class CompanyMetrics(BaseModel):
    """One company's extracted financial profile for one fiscal year.
    This is exactly the shape the Extraction Agent is expected to write into
    MongoDB's `financial_metrics` collection.
    """
    company_name: str
    fiscal_year: str
    source_document: str = Field(..., description="File name / report the figures came from")
    source_page: Optional[str] = None

    revenue_cr: float
    revenue_growth_cc_pct: Optional[float] = None
    ebit_margin_pct: Optional[float] = None
    pat_margin_pct: Optional[float] = None
    roe_pct: Optional[float] = None
    roce_pct: Optional[float] = None
    dso_days: Optional[float] = None
    fcf_to_pat_pct: Optional[float] = None
    revenue_per_employee_lakh: Optional[float] = None
    attrition_rate_pct: Optional[float] = None
    net_debt_cr: Optional[float] = None  # negative value = net cash


class MetricComparison(BaseModel):
    metric: str
    unit: str
    higher_is_better: bool
    focus_company_value: Optional[float]
    peer_values: dict  # {company_name: value}
    peer_average: Optional[float]
    focus_vs_peer_avg_pct: Optional[float]  # % difference vs peer average
    focus_rank: Optional[int]  # 1 = best among all companies compared
    total_ranked: int
    flag: str  # "outperform" | "inline" | "underperform" | "no_data"


class ComparisonResult(BaseModel):
    focus_company: str
    fiscal_year: str
    companies_compared: List[str]
    metric_comparisons: List[MetricComparison]
    narrative_summary: str
    key_strengths: List[str]
    key_weaknesses: List[str]
