from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# Sessions
# --------------------------------------------------------------------------- #
class SessionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class SessionSummary(BaseModel):
    id: str
    name: str
    created_at: datetime
    document_count: int


class SessionDetail(SessionSummary):
    documents: list["DocumentSummary"] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Documents
# --------------------------------------------------------------------------- #
class DocumentSummary(BaseModel):
    id: str
    file_name: str
    company_name: Optional[str] = None
    status: str
    uploaded_at: datetime
    page_count: Optional[int] = None
    overall_risk: Optional[str] = None


class RedFlagOut(BaseModel):
    id: str
    category: Optional[str] = None
    title: Optional[str] = None
    severity: str
    description: str
    recommendation: Optional[str] = None
    source_page: Optional[int] = None


class DocumentMetrics(BaseModel):
    revenue: Optional[str] = None
    net_profit: Optional[str] = None
    ebitda: Optional[str] = None
    eps: Optional[str] = None
    assets: Optional[str] = None
    liabilities: Optional[str] = None
    cash_flow: Optional[str] = None
    ratios: dict[str, str] = Field(default_factory=dict)
    other_metrics: list[dict[str, str]] = Field(default_factory=list)


class DocumentDetail(BaseModel):
    id: str
    file_name: str
    company_name: Optional[str] = None
    financial_year: Optional[str] = None
    status: str
    error: Optional[str] = None
    confidence_score: float = 0.0
    page_count: Optional[int] = None
    warnings: list[str] = Field(default_factory=list)
    metrics: DocumentMetrics
    red_flags: list[RedFlagOut] = Field(default_factory=list)
    overall_risk: Optional[str] = None
    risk_summary: Optional[str] = None
    uploaded_at: datetime


# --------------------------------------------------------------------------- #
# Chat (Research Agent)
# --------------------------------------------------------------------------- #
class ChatQuery(BaseModel):
    query: str = Field(..., min_length=1)
    document_id: Optional[str] = None  # optional: scope the question to one document


class Citation(BaseModel):
    document_id: Optional[str] = None
    page: Optional[int] = None
    snippet: str


class ChatMessageOut(BaseModel):
    id: str
    role: str
    content: str
    citations: list[Citation] = Field(default_factory=list)
    created_at: datetime


# --------------------------------------------------------------------------- #
# Comparison
# --------------------------------------------------------------------------- #
class CompareRequest(BaseModel):
    document_ids: list[str] = Field(..., min_length=1)


class CompanyComparison(BaseModel):
    document_id: str
    company_name: Optional[str] = None
    revenue: Optional[str] = None
    net_profit: Optional[str] = None
    debt: Optional[str] = None
    margin: Optional[str] = None


class CompareResponse(BaseModel):
    companies: list[CompanyComparison]
    summary: str


# --------------------------------------------------------------------------- #
# Reports
# --------------------------------------------------------------------------- #
class ReportRequest(BaseModel):
    document_ids: list[str] = Field(..., min_length=1)


class ReportSummary(BaseModel):
    id: str
    file_name: Optional[str] = None
    generated_at: datetime
    download_url: Optional[str] = None


class ReportStatus(BaseModel):
    id: str
    status: str
    download_url: Optional[str] = None
    error: Optional[str] = None


SessionDetail.model_rebuild()
