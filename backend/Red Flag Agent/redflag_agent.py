"""FastAPI Red Flag Agent for multi-agent financial research systems.

This module intentionally keeps the implementation in one file while
separating the service into testable classes:

Config -> PromptBuilder -> GroqService -> RuleEngine -> LLMRiskAnalyzer
-> RedFlagAgent -> APIController.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import socket
import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, TypedDict

import uvicorn
from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSequence
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

load_dotenv()

LOGGER_NAME = "redflag_agent"
logger = logging.getLogger(LOGGER_NAME)

MetricScalar = str | int | float


def _env_str(name: str, default: str | None = None) -> str | None:
    """Return a stripped environment variable or a default value."""

    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return value.strip()


# Groq deprecated several chat models (announced 2026-06-17); a stale .env may
# still point at one, which now returns HTTP 404. Remap to a working model.
_DEPRECATED_GROQ_MODELS = {
    "llama-3.3-70b-versatile": "openai/gpt-oss-120b",
    "llama-3.1-70b-versatile": "openai/gpt-oss-120b",
    "llama3-70b-8192": "openai/gpt-oss-120b",
    "llama-3.1-8b-instant": "openai/gpt-oss-20b",
    "llama3-8b-8192": "openai/gpt-oss-20b",
    "mixtral-8x7b-32768": "openai/gpt-oss-120b",
    "gemma2-9b-it": "openai/gpt-oss-20b",
    "qwen/qwen3-32b": "openai/gpt-oss-120b",
    "meta-llama/llama-4-scout-17b-16e-instruct": "openai/gpt-oss-120b",
}


def _resolve_redflag_groq_model() -> str:
    """Return a currently-valid Groq model, remapping deprecated names."""
    model = _env_str("GROQ_MODEL", "openai/gpt-oss-120b") or "openai/gpt-oss-120b"
    return _DEPRECATED_GROQ_MODELS.get(model, model)


def _env_float(name: str, default: float) -> float:
    """Return an environment float with a safe default."""

    value = _env_str(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        logger.warning("Invalid float for %s=%r; using %s", name, value, default)
        return default


def _env_int(name: str, default: int) -> int:
    """Return an environment integer with a safe default."""

    value = _env_str(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        logger.warning("Invalid integer for %s=%r; using %s", name, value, default)
        return default


def _env_bool(name: str, default: bool) -> bool:
    """Return an environment boolean with a safe default."""

    value = _env_str(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "y", "on"}


def _normalize_text(value: str) -> str:
    """Normalize text for lookups and deduplication."""

    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _compact_whitespace(value: str) -> str:
    """Collapse repeated whitespace to a single space."""

    return re.sub(r"\s+", " ", value).strip()


@dataclass(frozen=True)
class Config:
    """Runtime configuration loaded from environment variables."""

    groq_api_key: str | None = field(default_factory=lambda: _env_str("GROQ_API_KEY"))
    groq_model: str = field(
        default_factory=lambda: _resolve_redflag_groq_model()
    )
    llm_temperature: float = field(
        default_factory=lambda: _env_float("LLM_TEMPERATURE", 0.0)
    )
    llm_timeout_seconds: int = field(
        default_factory=lambda: _env_int("LLM_TIMEOUT_SECONDS", 45)
    )
    llm_max_retries: int = field(default_factory=lambda: _env_int("LLM_MAX_RETRIES", 2))
    llm_required: bool = field(
        default_factory=lambda: _env_bool("REDFLAG_REQUIRE_LLM", False)
    )
    debt_to_equity_high_threshold: float = field(
        default_factory=lambda: _env_float("DEBT_TO_EQUITY_HIGH_THRESHOLD", 2.0)
    )
    debt_to_equity_warning_threshold: float = field(
        default_factory=lambda: _env_float("DEBT_TO_EQUITY_WARNING_THRESHOLD", 1.5)
    )
    current_ratio_min_threshold: float = field(
        default_factory=lambda: _env_float("CURRENT_RATIO_MIN_THRESHOLD", 1.0)
    )
    current_ratio_warning_threshold: float = field(
        default_factory=lambda: _env_float("CURRENT_RATIO_WARNING_THRESHOLD", 1.2)
    )
    decline_high_threshold_pct: float = field(
        default_factory=lambda: _env_float("DECLINE_HIGH_THRESHOLD_PCT", -10.0)
    )
    decline_medium_threshold_pct: float = field(
        default_factory=lambda: _env_float("DECLINE_MEDIUM_THRESHOLD_PCT", -5.0)
    )
    revenue_slowdown_pp_threshold: float = field(
        default_factory=lambda: _env_float("REVENUE_SLOWDOWN_PP_THRESHOLD", 5.0)
    )
    margin_compression_pp_threshold: float = field(
        default_factory=lambda: _env_float("MARGIN_COMPRESSION_PP_THRESHOLD", 2.0)
    )
    liability_growth_warning_pct: float = field(
        default_factory=lambda: _env_float("LIABILITY_GROWTH_WARNING_PCT", 10.0)
    )
    liability_growth_high_pct: float = field(
        default_factory=lambda: _env_float("LIABILITY_GROWTH_HIGH_PCT", 25.0)
    )
    liabilities_to_assets_warning: float = field(
        default_factory=lambda: _env_float("LIABILITIES_TO_ASSETS_WARNING", 0.8)
    )
    interest_coverage_min_threshold: float = field(
        default_factory=lambda: _env_float("INTEREST_COVERAGE_MIN_THRESHOLD", 1.5)
    )
    interest_burden_warning_ratio: float = field(
        default_factory=lambda: _env_float("INTEREST_BURDEN_WARNING_RATIO", 0.10)
    )
    cash_conversion_warning_ratio: float = field(
        default_factory=lambda: _env_float("CASH_CONVERSION_WARNING_RATIO", 0.50)
    )
    max_context_chars: int = field(
        default_factory=lambda: _env_int("MAX_CONTEXT_CHARS", 12000)
    )
    host: str = field(default_factory=lambda: _env_str("HOST", "127.0.0.1") or "127.0.0.1")
    port: int = field(default_factory=lambda: _env_int("PORT", 8000))
    log_level: str = field(
        default_factory=lambda: (_env_str("LOG_LEVEL", "INFO") or "INFO").upper()
    )

    @property
    def llm_configured(self) -> bool:
        """Return whether Groq can be called."""

        return bool(self.groq_api_key)


class RiskCategory(StrEnum):
    """Supported red flag categories."""

    REVENUE = "Revenue Risks"
    PROFITABILITY = "Profitability Risks"
    LIQUIDITY = "Liquidity Risks"
    DEBT = "Debt Risks"
    BALANCE_SHEET = "Balance Sheet Risks"
    AUDITOR = "Auditor Risks"
    GOVERNANCE = "Governance Risks"
    OTHER = "Other Risks"


class RiskSeverity(StrEnum):
    """Risk severity levels."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class FinancialMetric(BaseModel):
    """A flexible metric shape that accepts scalar and period-aware values."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    value: MetricScalar | None = None
    current: MetricScalar | None = None
    previous: MetricScalar | None = None
    prior: MetricScalar | None = None
    current_year: MetricScalar | None = None
    prior_year: MetricScalar | None = None
    unit: str | None = None
    source: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_metric_shape(cls, data: Any) -> dict[str, Any]:
        """Allow metrics to be supplied as scalars or dictionaries."""

        if isinstance(data, bool):
            raise ValueError("metric values must be strings or numbers, not booleans")
        if isinstance(data, str | int | float) or data is None:
            return {"value": data}
        if not isinstance(data, dict):
            raise ValueError("metric values must be scalars or objects")

        normalized = dict(data)
        alias_map = {
            "current_value": "current",
            "current_period": "current",
            "current_year_value": "current_year",
            "previous_value": "previous",
            "previous_period": "previous",
            "prior_value": "prior",
            "prior_period": "prior",
            "last_year": "prior_year",
            "last_year_value": "prior_year",
        }
        for source_key, target_key in alias_map.items():
            if source_key in normalized and target_key not in normalized:
                normalized[target_key] = normalized[source_key]
        return normalized

    @model_validator(mode="after")
    def require_at_least_one_value(self) -> "FinancialMetric":
        """Require each metric object to carry at least one usable value."""

        values = (
            self.value,
            self.current,
            self.previous,
            self.prior,
            self.current_year,
            self.prior_year,
        )
        if all(value is None for value in values):
            raise ValueError("metric must include at least one value")
        return self

    def current_raw(self) -> MetricScalar | None:
        """Return the best available current-period value."""

        for value in (self.current, self.current_year, self.value):
            if value is not None:
                return value
        return None

    def prior_raw(self) -> MetricScalar | None:
        """Return the best available prior-period value."""

        for value in (self.previous, self.prior, self.prior_year):
            if value is not None:
                return value
        return None


class DocumentSection(BaseModel):
    """Qualitative document section from filings or annual reports."""

    section: str = Field(..., min_length=1, max_length=160)
    content: str = Field(..., min_length=1)

    @field_validator("section", "content", mode="before")
    @classmethod
    def strip_text(cls, value: Any) -> str:
        """Normalize incoming text fields."""

        if not isinstance(value, str):
            raise ValueError("section fields must be strings")
        stripped = value.strip()
        if not stripped:
            raise ValueError("section fields must not be empty")
        return stripped


class RedFlag(BaseModel):
    """A single financial, auditor, governance, or balance-sheet risk."""

    model_config = ConfigDict(use_enum_values=True)

    category: RiskCategory
    title: str = Field(..., min_length=3, max_length=140)
    severity: RiskSeverity
    description: str = Field(..., min_length=1)
    evidence: str = Field(..., min_length=1)
    recommendation: str = Field(..., min_length=1)

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category(cls, value: Any) -> Any:
        """Map common category variants to canonical values."""

        if isinstance(value, RiskCategory):
            return value
        if not isinstance(value, str):
            return value

        text = _normalize_text(value)
        exact_map = {
            "revenue": RiskCategory.REVENUE,
            "revenue risk": RiskCategory.REVENUE,
            "revenue risks": RiskCategory.REVENUE,
            "profitability": RiskCategory.PROFITABILITY,
            "profitability risk": RiskCategory.PROFITABILITY,
            "profitability risks": RiskCategory.PROFITABILITY,
            "liquidity": RiskCategory.LIQUIDITY,
            "liquidity risk": RiskCategory.LIQUIDITY,
            "liquidity risks": RiskCategory.LIQUIDITY,
            "debt": RiskCategory.DEBT,
            "debt risk": RiskCategory.DEBT,
            "debt risks": RiskCategory.DEBT,
            "balance sheet": RiskCategory.BALANCE_SHEET,
            "balance sheet risk": RiskCategory.BALANCE_SHEET,
            "balance sheet risks": RiskCategory.BALANCE_SHEET,
            "auditor": RiskCategory.AUDITOR,
            "auditor risk": RiskCategory.AUDITOR,
            "auditor risks": RiskCategory.AUDITOR,
            "audit": RiskCategory.AUDITOR,
            "governance": RiskCategory.GOVERNANCE,
            "governance risk": RiskCategory.GOVERNANCE,
            "governance risks": RiskCategory.GOVERNANCE,
        }
        if text in exact_map:
            return exact_map[text]
        if "revenue" in text or "sales" in text:
            return RiskCategory.REVENUE
        if "profit" in text or "margin" in text or "eps" in text:
            return RiskCategory.PROFITABILITY
        if "liquidity" in text or "cash flow" in text or "current ratio" in text:
            return RiskCategory.LIQUIDITY
        if "debt" in text or "interest" in text or "leverage" in text:
            return RiskCategory.DEBT
        if "asset" in text or "liabilit" in text or "equity" in text:
            return RiskCategory.BALANCE_SHEET
        if "audit" in text or "going concern" in text:
            return RiskCategory.AUDITOR
        if "governance" in text or "litigation" in text or "regulatory" in text:
            return RiskCategory.GOVERNANCE
        return RiskCategory.OTHER

    @field_validator("severity", mode="before")
    @classmethod
    def normalize_severity(cls, value: Any) -> Any:
        """Map severity variants to canonical values."""

        if isinstance(value, RiskSeverity):
            return value
        if not isinstance(value, str):
            return value

        text = _normalize_text(value)
        severity_map = {
            "low": RiskSeverity.LOW,
            "minor": RiskSeverity.LOW,
            "medium": RiskSeverity.MEDIUM,
            "moderate": RiskSeverity.MEDIUM,
            "high": RiskSeverity.HIGH,
            "severe": RiskSeverity.HIGH,
            "critical": RiskSeverity.CRITICAL,
            "very high": RiskSeverity.CRITICAL,
        }
        return severity_map.get(text, value)

    @field_validator("title", "description", "evidence", "recommendation", mode="before")
    @classmethod
    def normalize_required_string(cls, value: Any) -> str:
        """Ensure output text fields are non-empty strings."""

        if isinstance(value, list):
            value = "; ".join(str(item) for item in value)
        if value is None:
            raise ValueError("field must not be empty")
        stripped = str(value).strip()
        if not stripped:
            raise ValueError("field must not be empty")
        return stripped


class RedFlagRequest(BaseModel):
    """Request body accepted from the upstream Extraction Agent."""

    model_config = ConfigDict(extra="allow")

    company: str = Field(..., min_length=1, max_length=240)
    financial_year: str = Field(..., min_length=1, max_length=40)
    metrics: dict[str, FinancialMetric] = Field(..., min_length=1)
    document_sections: list[DocumentSection] = Field(default_factory=list)

    @field_validator("company", "financial_year", mode="before")
    @classmethod
    def strip_identifier(cls, value: Any) -> str:
        """Normalize request identifiers."""

        if not isinstance(value, str):
            raise ValueError("field must be a string")
        stripped = value.strip()
        if not stripped:
            raise ValueError("field must not be empty")
        return stripped

    @field_validator("metrics", mode="before")
    @classmethod
    def validate_metrics(cls, value: Any) -> Any:
        """Reject missing or empty metrics before model coercion."""

        if value is None:
            raise ValueError("metrics are required")
        if not isinstance(value, dict):
            raise ValueError("metrics must be an object")
        if not value:
            raise ValueError("metrics must not be empty")
        return value


class LLMRiskAnalysis(BaseModel):
    """Structured output expected from the LLM qualitative analyzer."""

    red_flags: list[RedFlag] = Field(default_factory=list)
    summary: str = Field(default="")

    @field_validator("summary", mode="before")
    @classmethod
    def normalize_summary(cls, value: Any) -> str:
        """Convert missing or non-string summaries safely."""

        if value is None:
            return ""
        return str(value).strip()


class RedFlagResponse(BaseModel):
    """API response returned to downstream agents."""

    model_config = ConfigDict(use_enum_values=True)

    company: str
    financial_year: str
    red_flags: list[RedFlag]
    overall_risk: RiskSeverity
    summary: str


class HealthResponse(BaseModel):
    """Health check payload."""

    status: str
    service: str
    llm_configured: bool
    model: str


class RedFlagAgentError(Exception):
    """Base exception for expected service-level errors."""


class LLMAnalysisError(RedFlagAgentError):
    """Raised when LLM qualitative analysis fails in required mode."""


class LLMOutputParsingError(LLMAnalysisError):
    """Raised when the LLM response cannot be parsed as structured JSON."""


class LLMServiceUnavailableError(LLMAnalysisError):
    """Raised when Groq or LangChain fails to complete a request."""


class LLMTimeoutError(LLMAnalysisError):
    """Raised when LLM analysis exceeds the configured timeout."""


class PromptBuilder:
    """Build LangChain prompts for qualitative red flag analysis."""

    def __init__(self, parser: PydanticOutputParser) -> None:
        self.parser = parser

    def build(self) -> ChatPromptTemplate:
        """Create the structured chat prompt used by the Groq model."""

        return ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    (
                        "You are a financial red flag analyst inside a multi-agent "
                        "research system. Identify only risks that are explicitly "
                        "supported by the supplied financial metrics, preliminary "
                        "rule flags, or document section text. Never invent facts, "
                        "amounts, trends, legal matters, audit concerns, or causes "
                        "that are not present in the input. Return JSON only."
                    ),
                ),
                (
                    "human",
                    (
                        "Company: {company}\n"
                        "Financial year: {financial_year}\n\n"
                        "Financial metrics JSON:\n{metrics_json}\n\n"
                        "Preliminary rule flags JSON:\n{rule_flags_json}\n\n"
                        "Document sections JSON:\n{document_sections_json}\n\n"
                        "Analyze these qualitative sections when present: Risk "
                        "Factors, Auditor Report, Notes to Financial Statements, "
                        "Management Discussion & Analysis. Use exact supplied text "
                        "or metric values as evidence. If no supported red flags are "
                        "present, return an empty red_flags array.\n\n"
                        "{format_instructions}"
                    ),
                ),
            ]
        )


class GroqService:
    """Thin wrapper around LangChain's ChatGroq client."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.client: ChatGroq | None = None

        if not config.llm_configured:
            logger.warning("GROQ_API_KEY is not configured; LLM analysis is disabled")
            return

        self.client = ChatGroq(
            model=config.groq_model,
            temperature=config.llm_temperature,
            api_key=config.groq_api_key,
            max_retries=config.llm_max_retries,
            timeout=config.llm_timeout_seconds,
        )

    def is_available(self) -> bool:
        """Return whether the Groq client is ready."""

        return self.client is not None


class RuleEngine:
    """Deterministic financial and keyword-based risk detector."""

    REVENUE_METRICS = ("revenue", "total_revenue", "sales", "net_sales")
    NET_PROFIT_METRICS = (
        "net_profit",
        "profit_after_tax",
        "pat",
        "profit_attributable_to_owners",
    )
    EBITDA_METRICS = ("ebitda", "operating_ebitda")
    EPS_METRICS = ("eps", "earnings_per_share", "basic_eps", "diluted_eps")
    OCF_METRICS = (
        "operating_cash_flow",
        "cash_flow_from_operations",
        "net_cash_from_operating_activities",
    )
    CURRENT_RATIO_METRICS = ("current_ratio", "current_ratio_times")
    DEBT_TO_EQUITY_METRICS = (
        "debt_to_equity_ratio",
        "debt_equity_ratio",
        "de_ratio",
        "debt_to_equity",
    )
    INTEREST_COVERAGE_METRICS = (
        "interest_coverage_ratio",
        "interest_coverage",
        "ebit_interest_coverage",
    )
    INTEREST_EXPENSE_METRICS = (
        "interest_expense",
        "finance_cost",
        "finance_costs",
        "borrowing_costs",
    )
    ASSET_METRICS = ("total_assets", "assets")
    LIABILITY_METRICS = ("total_liabilities", "liabilities")
    EQUITY_METRICS = (
        "total_equity",
        "shareholders_equity",
        "shareholder_equity",
        "net_worth",
    )
    REVENUE_GROWTH_METRICS = (
        "revenue_growth",
        "revenue_growth_rate",
        "sales_growth",
        "sales_growth_rate",
    )

    def __init__(self, config: Config) -> None:
        self.config = config

    def analyze(self, request: RedFlagRequest) -> list[RedFlag]:
        """Run all deterministic checks and return preliminary red flags."""

        flags: list[RedFlag] = []
        flags.extend(self._analyze_revenue(request))
        flags.extend(self._analyze_profitability(request))
        flags.extend(self._analyze_liquidity(request))
        flags.extend(self._analyze_debt(request))
        flags.extend(self._analyze_balance_sheet(request))
        flags.extend(self._analyze_document_keywords(request))
        return self.deduplicate(flags)

    @staticmethod
    def deduplicate(flags: list[RedFlag]) -> list[RedFlag]:
        """Remove exact duplicate flags while preserving severity."""

        by_key: dict[tuple[str, str, str], RedFlag] = {}
        for flag in flags:
            key = (
                str(flag.category),
                _normalize_text(flag.title),
                _normalize_text(flag.evidence)[:140],
            )
            existing = by_key.get(key)
            if existing is None:
                by_key[key] = flag
                continue
            if RedFlagAgent.severity_rank(flag.severity) > RedFlagAgent.severity_rank(
                existing.severity
            ):
                by_key[key] = flag
        return list(by_key.values())

    def _analyze_revenue(self, request: RedFlagRequest) -> list[RedFlag]:
        flags = []
        flags.extend(
            self._decline_flag(
                request=request,
                candidates=self.REVENUE_METRICS,
                display_name="Revenue",
                category=RiskCategory.REVENUE,
                title="Revenue decline",
                recommendation=(
                    "Review revenue drivers, segment performance, and customer "
                    "concentration before relying on growth assumptions."
                ),
            )
        )

        current_growth = self._metric_current_number(
            request.metrics, self.REVENUE_GROWTH_METRICS
        )
        prior_growth = self._metric_prior_number(
            request.metrics, self.REVENUE_GROWTH_METRICS
        )
        growth_metric = self._find_metric(request.metrics, self.REVENUE_GROWTH_METRICS)
        if (
            current_growth is not None
            and prior_growth is not None
            and current_growth < prior_growth - self.config.revenue_slowdown_pp_threshold
        ):
            decline_pp = prior_growth - current_growth
            flags.append(
                self._flag(
                    category=RiskCategory.REVENUE,
                    title="Revenue slowdown",
                    severity=RiskSeverity.MEDIUM
                    if decline_pp < 10
                    else RiskSeverity.HIGH,
                    description=(
                        "Revenue growth slowed by "
                        f"{decline_pp:.2f} percentage points versus the prior period."
                    ),
                    evidence=self._metric_evidence(
                        "Revenue growth",
                        growth_metric.current_raw() if growth_metric else current_growth,
                        growth_metric.prior_raw() if growth_metric else prior_growth,
                        current_growth - prior_growth,
                        percentage_points=True,
                    ),
                    recommendation=(
                        "Compare management commentary with segment-level and "
                        "customer-level revenue trends."
                    ),
                )
            )
        return flags

    def _analyze_profitability(self, request: RedFlagRequest) -> list[RedFlag]:
        flags: list[RedFlag] = []
        flags.extend(
            self._decline_flag(
                request=request,
                candidates=self.NET_PROFIT_METRICS,
                display_name="Net profit",
                category=RiskCategory.PROFITABILITY,
                title="Net profit decline",
                recommendation=(
                    "Investigate whether the decline is recurring, margin-related, "
                    "or driven by one-time items."
                ),
            )
        )
        flags.extend(
            self._decline_flag(
                request=request,
                candidates=self.EBITDA_METRICS,
                display_name="EBITDA",
                category=RiskCategory.PROFITABILITY,
                title="EBITDA decline",
                recommendation=(
                    "Review operating cost growth, pricing pressure, and segment "
                    "profitability."
                ),
            )
        )
        flags.extend(
            self._decline_flag(
                request=request,
                candidates=self.EPS_METRICS,
                display_name="EPS",
                category=RiskCategory.PROFITABILITY,
                title="EPS decline",
                recommendation=(
                    "Assess earnings quality, share count changes, and recurring "
                    "profitability."
                ),
            )
        )
        margin_flag = self._margin_compression_flag(request)
        if margin_flag:
            flags.append(margin_flag)
        return flags

    def _analyze_liquidity(self, request: RedFlagRequest) -> list[RedFlag]:
        flags: list[RedFlag] = []
        current_ratio = self._metric_current_number(
            request.metrics, self.CURRENT_RATIO_METRICS
        )
        current_ratio_metric = self._find_metric(
            request.metrics, self.CURRENT_RATIO_METRICS
        )
        if current_ratio is not None:
            if current_ratio < self.config.current_ratio_min_threshold:
                flags.append(
                    self._flag(
                        category=RiskCategory.LIQUIDITY,
                        title="Low current ratio",
                        severity=RiskSeverity.HIGH if current_ratio < 0.8 else RiskSeverity.MEDIUM,
                        description=(
                            "Current ratio is below the configured minimum "
                            f"threshold of {self.config.current_ratio_min_threshold:.2f}."
                        ),
                        evidence=self._metric_evidence(
                            "Current ratio",
                            current_ratio_metric.current_raw()
                            if current_ratio_metric
                            else current_ratio,
                        ),
                        recommendation=(
                            "Review working capital, near-term obligations, and "
                            "available credit facilities."
                        ),
                    )
                )
            elif current_ratio < self.config.current_ratio_warning_threshold:
                flags.append(
                    self._flag(
                        category=RiskCategory.LIQUIDITY,
                        title="Weak liquidity cushion",
                        severity=RiskSeverity.LOW,
                        description=(
                            "Current ratio is above the minimum but below the "
                            "configured warning threshold."
                        ),
                        evidence=self._metric_evidence(
                            "Current ratio",
                            current_ratio_metric.current_raw()
                            if current_ratio_metric
                            else current_ratio,
                        ),
                        recommendation=(
                            "Monitor working-capital movements and short-term debt "
                            "maturities."
                        ),
                    )
                )

        ocf = self._metric_current_number(request.metrics, self.OCF_METRICS)
        ocf_metric = self._find_metric(request.metrics, self.OCF_METRICS)
        if ocf is not None and ocf < 0:
            flags.append(
                self._flag(
                    category=RiskCategory.LIQUIDITY,
                    title="Negative operating cash flow",
                    severity=RiskSeverity.HIGH,
                    description="Operating cash flow is negative for the period.",
                    evidence=self._metric_evidence(
                        "Operating cash flow",
                        ocf_metric.current_raw() if ocf_metric else ocf,
                    ),
                    recommendation=(
                        "Reconcile cash flow with earnings and review working-capital "
                        "or collection issues."
                    ),
                )
            )

        net_profit = self._metric_current_number(request.metrics, self.NET_PROFIT_METRICS)
        if (
            ocf is not None
            and net_profit is not None
            and net_profit > 0
            and 0 <= ocf / net_profit < self.config.cash_conversion_warning_ratio
        ):
            flags.append(
                self._flag(
                    category=RiskCategory.LIQUIDITY,
                    title="Weak operating cash conversion",
                    severity=RiskSeverity.MEDIUM,
                    description=(
                        "Operating cash flow is materially lower than reported net "
                        "profit."
                    ),
                    evidence=(
                        self._metric_evidence(
                            "Operating cash flow",
                            ocf_metric.current_raw() if ocf_metric else ocf,
                        )
                        + " "
                        + self._metric_evidence("Net profit", net_profit)
                    ),
                    recommendation=(
                        "Review receivables, inventory, payables, and non-cash "
                        "earnings components."
                    ),
                )
            )
        return flags

    def _analyze_debt(self, request: RedFlagRequest) -> list[RedFlag]:
        flags: list[RedFlag] = []
        debt_to_equity = self._metric_current_number(
            request.metrics, self.DEBT_TO_EQUITY_METRICS
        )
        debt_metric = self._find_metric(request.metrics, self.DEBT_TO_EQUITY_METRICS)
        if debt_to_equity is not None:
            if debt_to_equity > self.config.debt_to_equity_high_threshold:
                flags.append(
                    self._flag(
                        category=RiskCategory.DEBT,
                        title="High debt-to-equity ratio",
                        severity=RiskSeverity.CRITICAL
                        if debt_to_equity >= 3.0
                        else RiskSeverity.HIGH,
                        description=(
                            "Debt-to-equity ratio exceeds the configured high-risk "
                            f"threshold of {self.config.debt_to_equity_high_threshold:.2f}."
                        ),
                        evidence=self._metric_evidence(
                            "Debt-to-equity ratio",
                            debt_metric.current_raw() if debt_metric else debt_to_equity,
                        ),
                        recommendation=(
                            "Assess debt maturity schedule, covenant headroom, and "
                            "refinancing risk."
                        ),
                    )
                )
            elif debt_to_equity > self.config.debt_to_equity_warning_threshold:
                flags.append(
                    self._flag(
                        category=RiskCategory.DEBT,
                        title="Elevated debt-to-equity ratio",
                        severity=RiskSeverity.MEDIUM,
                        description=(
                            "Debt-to-equity ratio exceeds the configured warning "
                            f"threshold of {self.config.debt_to_equity_warning_threshold:.2f}."
                        ),
                        evidence=self._metric_evidence(
                            "Debt-to-equity ratio",
                            debt_metric.current_raw() if debt_metric else debt_to_equity,
                        ),
                        recommendation=(
                            "Monitor leverage trends and compare debt levels with "
                            "sector peers."
                        ),
                    )
                )

        interest_coverage = self._metric_current_number(
            request.metrics, self.INTEREST_COVERAGE_METRICS
        )
        coverage_metric = self._find_metric(
            request.metrics, self.INTEREST_COVERAGE_METRICS
        )
        if (
            interest_coverage is not None
            and interest_coverage < self.config.interest_coverage_min_threshold
        ):
            flags.append(
                self._flag(
                    category=RiskCategory.DEBT,
                    title="Weak interest coverage",
                    severity=RiskSeverity.CRITICAL
                    if interest_coverage <= 0
                    else RiskSeverity.HIGH,
                    description=(
                        "Interest coverage is below the configured minimum "
                        f"threshold of {self.config.interest_coverage_min_threshold:.2f}."
                    ),
                    evidence=self._metric_evidence(
                        "Interest coverage",
                        coverage_metric.current_raw()
                        if coverage_metric
                        else interest_coverage,
                    ),
                    recommendation=(
                        "Assess whether recurring earnings can service interest "
                        "costs under downside scenarios."
                    ),
                )
            )

        interest_expense = self._metric_current_number(
            request.metrics, self.INTEREST_EXPENSE_METRICS
        )
        revenue = self._metric_current_number(request.metrics, self.REVENUE_METRICS)
        if (
            interest_expense is not None
            and revenue is not None
            and revenue > 0
            and abs(interest_expense) / revenue > self.config.interest_burden_warning_ratio
        ):
            burden = abs(interest_expense) / revenue
            flags.append(
                self._flag(
                    category=RiskCategory.DEBT,
                    title="High interest burden",
                    severity=RiskSeverity.HIGH if burden >= 0.2 else RiskSeverity.MEDIUM,
                    description=(
                        "Interest or finance cost is high relative to reported revenue."
                    ),
                    evidence=(
                        self._metric_evidence("Interest expense", interest_expense)
                        + " "
                        + self._metric_evidence("Revenue", revenue)
                        + f" Interest burden={burden:.2%}."
                    ),
                    recommendation=(
                        "Review borrowing costs, refinancing needs, and sensitivity "
                        "to rate increases."
                    ),
                )
            )
        return flags

    def _analyze_balance_sheet(self, request: RedFlagRequest) -> list[RedFlag]:
        flags: list[RedFlag] = []
        flags.extend(
            self._increase_flag(
                request=request,
                candidates=self.LIABILITY_METRICS,
                display_name="Total liabilities",
                category=RiskCategory.BALANCE_SHEET,
                title="Rising liabilities",
                warning_threshold_pct=self.config.liability_growth_warning_pct,
                high_threshold_pct=self.config.liability_growth_high_pct,
                recommendation=(
                    "Review the composition, maturity, and cost of increased "
                    "liabilities."
                ),
            )
        )
        flags.extend(
            self._decline_flag(
                request=request,
                candidates=self.ASSET_METRICS,
                display_name="Total assets",
                category=RiskCategory.BALANCE_SHEET,
                title="Falling assets",
                recommendation=(
                    "Review whether asset decline is linked to disposals, impairment, "
                    "or working-capital contraction."
                ),
            )
        )

        assets = self._metric_current_number(request.metrics, self.ASSET_METRICS)
        liabilities = self._metric_current_number(request.metrics, self.LIABILITY_METRICS)
        equity = self._metric_current_number(request.metrics, self.EQUITY_METRICS)
        if equity is None and assets is not None and liabilities is not None:
            equity = assets - liabilities

        if equity is not None and equity <= 0:
            flags.append(
                self._flag(
                    category=RiskCategory.BALANCE_SHEET,
                    title="Weak equity base",
                    severity=RiskSeverity.CRITICAL,
                    description="Equity is zero or negative based on supplied metrics.",
                    evidence=self._balance_sheet_evidence(assets, liabilities, equity),
                    recommendation=(
                        "Assess solvency, recapitalization needs, and covenant "
                        "compliance."
                    ),
                )
            )
        elif (
            assets is not None
            and liabilities is not None
            and assets > 0
            and liabilities / assets > self.config.liabilities_to_assets_warning
        ):
            ratio = liabilities / assets
            flags.append(
                self._flag(
                    category=RiskCategory.BALANCE_SHEET,
                    title="High liabilities relative to assets",
                    severity=RiskSeverity.HIGH if ratio >= 0.9 else RiskSeverity.MEDIUM,
                    description=(
                        "Liabilities represent a high share of total assets based on "
                        "the supplied metrics."
                    ),
                    evidence=(
                        self._balance_sheet_evidence(assets, liabilities, equity)
                        + f" Liabilities/assets={ratio:.2%}."
                    ),
                    recommendation=(
                        "Review leverage, asset quality, and balance-sheet resilience."
                    ),
                )
            )
        return flags

    def _analyze_document_keywords(self, request: RedFlagRequest) -> list[RedFlag]:
        flags: list[RedFlag] = []
        indicators: tuple[tuple[RiskCategory, str, RiskSeverity, str, str], ...] = (
            (
                RiskCategory.AUDITOR,
                "Qualified audit opinion",
                RiskSeverity.HIGH,
                r"\bqualified opinion\b",
                "Review auditor qualifications and their impact on reported figures.",
            ),
            (
                RiskCategory.AUDITOR,
                "Disclaimer of opinion",
                RiskSeverity.CRITICAL,
                r"\bdisclaimer of opinion\b",
                "Investigate why the auditor could not express an opinion.",
            ),
            (
                RiskCategory.AUDITOR,
                "Adverse audit opinion",
                RiskSeverity.CRITICAL,
                r"\badverse opinion\b",
                "Assess whether the financial statements can be relied upon.",
            ),
            (
                RiskCategory.AUDITOR,
                "Going concern warning",
                RiskSeverity.HIGH,
                r"\bgoing concern\b|\bmaterial uncertainty related to going concern\b",
                "Review liquidity runway, debt maturities, and management plans.",
            ),
            (
                RiskCategory.AUDITOR,
                "Emphasis of matter",
                RiskSeverity.MEDIUM,
                r"\bemphasis of matter\b",
                "Read the referenced matter and evaluate financial statement impact.",
            ),
            (
                RiskCategory.GOVERNANCE,
                "Litigation disclosed",
                RiskSeverity.MEDIUM,
                r"\blitigation\b|\blegal proceedings\b",
                "Assess potential financial exposure and disclosure adequacy.",
            ),
            (
                RiskCategory.GOVERNANCE,
                "Regulatory investigation",
                RiskSeverity.HIGH,
                r"\bregulatory investigation\b|\binvestigation by regulator\b",
                "Review scope, status, and potential penalties of the investigation.",
            ),
            (
                RiskCategory.GOVERNANCE,
                "Contingent liabilities disclosed",
                RiskSeverity.MEDIUM,
                r"\bcontingent liabilit(?:y|ies)\b",
                "Quantify potential obligations and likelihood of cash outflow.",
            ),
            (
                RiskCategory.DEBT,
                "Debt covenant breach disclosed",
                RiskSeverity.HIGH,
                r"\bcovenant breach\b|\bbreach of covenant\b|\bloan covenant breach\b",
                "Review lender remedies, waiver status, and cross-default clauses.",
            ),
            (
                RiskCategory.DEBT,
                "Debt default disclosed",
                RiskSeverity.CRITICAL,
                r"\bdefault under (?:loan|debt|borrowing)\b|\bevent of default\b",
                "Assess acceleration risk, refinancing options, and liquidity runway.",
            ),
            (
                RiskCategory.GOVERNANCE,
                "Fraud or misconduct disclosed",
                RiskSeverity.HIGH,
                r"\bfraud\b|\bmisconduct\b|\bwhistleblower complaint\b",
                "Review investigation status, control failures, and financial impact.",
            ),
            (
                RiskCategory.BALANCE_SHEET,
                "Asset impairment disclosed",
                RiskSeverity.MEDIUM,
                r"\bimpairment\b|\basset write[- ]?down\b",
                "Review affected assets, assumptions, and recurring earnings impact.",
            ),
            (
                RiskCategory.GOVERNANCE,
                "Management change disclosed",
                RiskSeverity.LOW,
                r"\bmanagement change\b|\bchange in key management\b",
                "Evaluate continuity risk and transition context.",
            ),
            (
                RiskCategory.GOVERNANCE,
                "Key resignation disclosed",
                RiskSeverity.MEDIUM,
                (
                    r"\bresignation of "
                    r"(?:auditor|director|chief financial officer|cfo|key management)\b"
                ),
                "Review governance implications and stated reasons for resignation.",
            ),
        )

        for section in request.document_sections:
            for category, title, severity, pattern, recommendation in indicators:
                snippet = self._first_supported_snippet(section.content, pattern)
                if not snippet:
                    continue
                flags.append(
                    self._flag(
                        category=category,
                        title=title,
                        severity=severity,
                        description=(
                            "The supplied document section contains language matching "
                            f"{title.lower()}."
                        ),
                        evidence=f"{section.section}: {snippet}",
                        recommendation=recommendation,
                    )
                )
        return flags

    def _decline_flag(
        self,
        request: RedFlagRequest,
        candidates: tuple[str, ...],
        display_name: str,
        category: RiskCategory,
        title: str,
        recommendation: str,
    ) -> list[RedFlag]:
        metric = self._find_metric(request.metrics, candidates)
        if metric is None:
            return []

        current = self._parse_number(metric.current_raw())
        prior = self._parse_number(metric.prior_raw())
        if current is None or prior is None or prior == 0:
            return []

        change_pct = ((current - prior) / abs(prior)) * 100
        if change_pct >= 0:
            return []

        if change_pct <= self.config.decline_high_threshold_pct:
            severity = RiskSeverity.HIGH
        elif change_pct <= self.config.decline_medium_threshold_pct:
            severity = RiskSeverity.MEDIUM
        else:
            severity = RiskSeverity.LOW

        return [
            self._flag(
                category=category,
                title=title,
                severity=severity,
                description=(
                    f"{display_name} declined by {abs(change_pct):.2f}% versus the "
                    "prior period."
                ),
                evidence=self._metric_evidence(
                    display_name,
                    metric.current_raw(),
                    metric.prior_raw(),
                    change_pct,
                ),
                recommendation=recommendation,
            )
        ]

    def _increase_flag(
        self,
        request: RedFlagRequest,
        candidates: tuple[str, ...],
        display_name: str,
        category: RiskCategory,
        title: str,
        warning_threshold_pct: float,
        high_threshold_pct: float,
        recommendation: str,
    ) -> list[RedFlag]:
        metric = self._find_metric(request.metrics, candidates)
        if metric is None:
            return []

        current = self._parse_number(metric.current_raw())
        prior = self._parse_number(metric.prior_raw())
        if current is None or prior is None or prior == 0:
            return []

        change_pct = ((current - prior) / abs(prior)) * 100
        if change_pct < warning_threshold_pct:
            return []

        severity = RiskSeverity.HIGH if change_pct >= high_threshold_pct else RiskSeverity.MEDIUM
        return [
            self._flag(
                category=category,
                title=title,
                severity=severity,
                description=(
                    f"{display_name} increased by {change_pct:.2f}% versus the "
                    "prior period."
                ),
                evidence=self._metric_evidence(
                    display_name,
                    metric.current_raw(),
                    metric.prior_raw(),
                    change_pct,
                ),
                recommendation=recommendation,
            )
        ]

    def _margin_compression_flag(self, request: RedFlagRequest) -> RedFlag | None:
        revenue_metric = self._find_metric(request.metrics, self.REVENUE_METRICS)
        revenue_current = self._parse_number(
            revenue_metric.current_raw() if revenue_metric else None
        )
        revenue_prior = self._parse_number(
            revenue_metric.prior_raw() if revenue_metric else None
        )
        if revenue_current is None or revenue_prior is None:
            return None
        if revenue_current <= 0 or revenue_prior <= 0:
            return None

        profit_metric = self._find_metric(request.metrics, self.EBITDA_METRICS)
        margin_label = "EBITDA margin"
        if profit_metric is None:
            profit_metric = self._find_metric(request.metrics, self.NET_PROFIT_METRICS)
            margin_label = "Net profit margin"
        if profit_metric is None:
            return None

        profit_current = self._parse_number(profit_metric.current_raw())
        profit_prior = self._parse_number(profit_metric.prior_raw())
        if profit_current is None or profit_prior is None:
            return None

        current_margin = (profit_current / revenue_current) * 100
        prior_margin = (profit_prior / revenue_prior) * 100
        compression_pp = prior_margin - current_margin
        if compression_pp < self.config.margin_compression_pp_threshold:
            return None

        return self._flag(
            category=RiskCategory.PROFITABILITY,
            title="Margin compression",
            severity=RiskSeverity.HIGH if compression_pp >= 5 else RiskSeverity.MEDIUM,
            description=(
                f"{margin_label} compressed by {compression_pp:.2f} percentage "
                "points versus the prior period."
            ),
            evidence=(
                f"{margin_label}: current={current_margin:.2f}%, "
                f"prior={prior_margin:.2f}%. "
                + self._metric_evidence(
                    "Revenue",
                    revenue_metric.current_raw(),
                    revenue_metric.prior_raw(),
                )
                + " "
                + self._metric_evidence(
                    margin_label.replace(" margin", ""),
                    profit_metric.current_raw(),
                    profit_metric.prior_raw(),
                )
            ),
            recommendation=(
                "Review pricing, cost inflation, utilization, and mix changes behind "
                "the margin movement."
            ),
        )

    def _find_metric(
        self,
        metrics: dict[str, FinancialMetric],
        candidates: tuple[str, ...],
    ) -> FinancialMetric | None:
        normalized_candidates = {self._normalize_metric_key(candidate) for candidate in candidates}
        for key, metric in metrics.items():
            if self._normalize_metric_key(key) in normalized_candidates:
                return metric
        return None

    def _metric_current_number(
        self,
        metrics: dict[str, FinancialMetric],
        candidates: tuple[str, ...],
    ) -> float | None:
        metric = self._find_metric(metrics, candidates)
        if metric is None:
            return None
        return self._parse_number(metric.current_raw())

    def _metric_prior_number(
        self,
        metrics: dict[str, FinancialMetric],
        candidates: tuple[str, ...],
    ) -> float | None:
        metric = self._find_metric(metrics, candidates)
        if metric is None:
            return None
        return self._parse_number(metric.prior_raw())

    @staticmethod
    def _normalize_metric_key(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", value.lower())

    @staticmethod
    def _parse_number(value: Any) -> float | None:
        """Parse common financial strings such as '1,200 crore' or '(50)'."""

        if value is None:
            return None
        if isinstance(value, bool):
            return None
        if isinstance(value, int | float):
            return float(value)
        if not isinstance(value, str):
            return None

        text = value.strip().lower()
        if not text or text in {"na", "n/a", "none", "null", "-", "--"}:
            return None

        negative = text.startswith("(") and ")" in text
        text = text.replace(",", "")
        text = text.replace("(", " ").replace(")", " ")
        match = re.search(r"[-+]?\d*\.?\d+(?:e[-+]?\d+)?", text)
        if not match:
            return None
        try:
            number = float(match.group(0))
        except ValueError:
            return None
        return -abs(number) if negative else number

    @staticmethod
    def _metric_evidence(
        label: str,
        current: Any,
        prior: Any | None = None,
        change: float | None = None,
        percentage_points: bool = False,
    ) -> str:
        """Build compact metric evidence without inventing context."""

        parts = [f"{label}: current={current!r}"]
        if prior is not None:
            parts.append(f"prior={prior!r}")
        if change is not None:
            suffix = "pp" if percentage_points else "%"
            parts.append(f"change={change:.2f}{suffix}")
        return ", ".join(parts) + "."

    @staticmethod
    def _balance_sheet_evidence(
        assets: float | None,
        liabilities: float | None,
        equity: float | None,
    ) -> str:
        parts = []
        if assets is not None:
            parts.append(f"total_assets={assets}")
        if liabilities is not None:
            parts.append(f"total_liabilities={liabilities}")
        if equity is not None:
            parts.append(f"equity={equity}")
        return ", ".join(parts) + "."

    @staticmethod
    def _flag(
        category: RiskCategory,
        title: str,
        severity: RiskSeverity,
        description: str,
        evidence: str,
        recommendation: str,
    ) -> RedFlag:
        return RedFlag(
            category=category,
            title=title,
            severity=severity,
            description=description,
            evidence=evidence,
            recommendation=recommendation,
        )

    @staticmethod
    def _first_supported_snippet(content: str, pattern: str) -> str | None:
        """Return a non-negated keyword snippet from source text."""

        for match in re.finditer(pattern, content, flags=re.IGNORECASE):
            before = content[max(0, match.start() - 80) : match.start()].lower()
            if re.search(
                r"\b(no|not|without|none|nil|neither)\b.{0,50}$",
                before,
                flags=re.IGNORECASE,
            ):
                continue

            start = max(0, match.start() - 80)
            end = min(len(content), match.end() + 120)
            snippet = _compact_whitespace(content[start:end])
            return f'"{snippet}"'
        return None


class LLMRiskAnalyzer:
    """LLM-backed qualitative risk analyzer using LangChain and Groq."""

    def __init__(
        self,
        config: Config,
        groq_service: GroqService,
        prompt_builder: PromptBuilder,
        parser: PydanticOutputParser,
    ) -> None:
        self.config = config
        self.groq_service = groq_service
        self.parser = parser
        self.prompt = prompt_builder.build()
        self.chain: RunnableSequence | None = None

        if groq_service.client is not None:
            self.chain = self.prompt | groq_service.client | self.parser

    async def analyze(
        self,
        request: RedFlagRequest,
        rule_flags: list[RedFlag],
    ) -> LLMRiskAnalysis:
        """Analyze qualitative sections and return structured LLM findings."""

        if not request.document_sections:
            return LLMRiskAnalysis(
                red_flags=[],
                summary="No document sections supplied for qualitative analysis.",
            )
        if self.chain is None:
            return self._fallback_or_raise(
                LLMServiceUnavailableError(
                    "GROQ_API_KEY is not configured; LLM analysis is disabled"
                )
            )

        payload = {
            "company": request.company,
            "financial_year": request.financial_year,
            "metrics_json": self._metrics_json(request.metrics),
            "rule_flags_json": self._flags_json(rule_flags),
            "document_sections_json": self._sections_json(request.document_sections),
            "format_instructions": self.parser.get_format_instructions(),
        }

        logger.info(
            "Sending LLM risk analysis request for company=%s year=%s sections=%s",
            request.company,
            request.financial_year,
            len(request.document_sections),
        )

        try:
            analysis = await asyncio.wait_for(
                self.chain.ainvoke(payload),
                timeout=self.config.llm_timeout_seconds,
            )
        except asyncio.TimeoutError as exc:
            return self._fallback_or_raise(
                LLMTimeoutError("LLM analysis timed out"),
                exc,
            )
        except (OutputParserException, ValidationError, json.JSONDecodeError) as exc:
            return self._fallback_or_raise(
                LLMOutputParsingError("LLM returned invalid structured JSON"),
                exc,
            )
        except Exception as exc:
            return self._fallback_or_raise(
                LLMServiceUnavailableError(f"Groq LLM analysis failed: {exc}"),
                exc,
            )

        if not isinstance(analysis, LLMRiskAnalysis):
            return self._fallback_or_raise(
                LLMOutputParsingError("LLM parser returned an unexpected object")
            )

        logger.info(
            "LLM risk analysis completed with %s flags",
            len(analysis.red_flags),
        )
        logger.debug("LLM structured response: %s", analysis.model_dump(mode="json"))
        return analysis

    def _fallback_or_raise(
        self,
        error: LLMAnalysisError,
        cause: BaseException | None = None,
    ) -> LLMRiskAnalysis:
        """Return a safe fallback unless LLM analysis is configured as required."""

        if cause is not None:
            logger.warning("LLM qualitative analysis failed: %s", error, exc_info=cause)
        else:
            logger.warning("LLM qualitative analysis failed: %s", error)
        if self.config.llm_required:
            if cause is not None:
                raise error from cause
            raise error
        return LLMRiskAnalysis(
            red_flags=[],
            summary=f"{error}; rule-based analysis completed.",
        )

    def _metrics_json(self, metrics: dict[str, FinancialMetric]) -> str:
        data = {
            name: metric.model_dump(mode="json", exclude_none=True)
            for name, metric in metrics.items()
        }
        return self._bounded_json(data)

    def _flags_json(self, flags: list[RedFlag]) -> str:
        return self._bounded_json([flag.model_dump(mode="json") for flag in flags])

    def _sections_json(self, sections: list[DocumentSection]) -> str:
        data = [
            {"section": section.section, "content": section.content}
            for section in sections
        ]
        return self._bounded_json(data)

    def _bounded_json(self, value: Any) -> str:
        serialized = json.dumps(value, ensure_ascii=True, indent=2)
        if len(serialized) <= self.config.max_context_chars:
            return serialized
        return serialized[: self.config.max_context_chars] + "\n...[truncated]"


class EvidenceGrounder:
    """Validates that LLM findings are supported by supplied source material."""

    STOPWORDS = {
        "about",
        "above",
        "after",
        "again",
        "against",
        "also",
        "because",
        "before",
        "being",
        "between",
        "company",
        "could",
        "during",
        "evidence",
        "financial",
        "from",
        "have",
        "into",
        "more",
        "only",
        "other",
        "over",
        "risk",
        "section",
        "such",
        "than",
        "that",
        "their",
        "there",
        "this",
        "through",
        "under",
        "were",
        "with",
        "year",
    }

    def filter_supported_flags(
        self,
        request: RedFlagRequest,
        rule_flags: list[RedFlag],
        llm_flags: list[RedFlag],
    ) -> tuple[list[RedFlag], int]:
        """Return only LLM flags whose evidence is grounded in request data."""

        if not llm_flags:
            return [], 0

        normalized_corpus = _normalize_text(self._build_corpus(request, rule_flags))
        supported: list[RedFlag] = []
        for flag in llm_flags:
            if self.is_supported(flag, normalized_corpus):
                supported.append(flag)
            else:
                logger.warning(
                    "Discarded ungrounded LLM flag title=%r evidence=%r",
                    flag.title,
                    flag.evidence,
                )
        return supported, len(llm_flags) - len(supported)

    def is_supported(self, flag: RedFlag, normalized_corpus: str) -> bool:
        """Return whether a flag's evidence is traceable to source text."""

        normalized_evidence = _normalize_text(flag.evidence)
        if not normalized_evidence:
            return False
        if normalized_evidence in normalized_corpus:
            return True

        tokens = [
            token
            for token in normalized_evidence.split()
            if self._is_meaningful_token(token)
        ]
        unique_tokens = list(dict.fromkeys(tokens))
        if not unique_tokens:
            return False

        hits = sum(1 for token in unique_tokens if token in normalized_corpus)
        numeric_tokens = [token for token in unique_tokens if re.search(r"\d", token)]
        if numeric_tokens and all(token in normalized_corpus for token in numeric_tokens):
            return hits >= max(2, int(len(unique_tokens) * 0.5))
        if len(unique_tokens) <= 3:
            return hits == len(unique_tokens)
        return hits >= 3 and hits / len(unique_tokens) >= 0.65

    def _build_corpus(
        self,
        request: RedFlagRequest,
        rule_flags: list[RedFlag],
    ) -> str:
        parts: list[str] = [request.company, request.financial_year]
        for metric_name, metric in request.metrics.items():
            parts.append(metric_name)
            parts.append(json.dumps(metric.model_dump(mode="json"), ensure_ascii=True))
        for section in request.document_sections:
            parts.append(section.section)
            parts.append(section.content)
        for flag in rule_flags:
            parts.extend(
                [
                    str(flag.category),
                    flag.title,
                    flag.description,
                    flag.evidence,
                    flag.recommendation,
                ]
            )
        return "\n".join(parts)

    def _is_meaningful_token(self, token: str) -> bool:
        return len(token) >= 3 and token not in self.STOPWORDS


class RedFlagState(TypedDict, total=False):
    """LangGraph workflow state."""

    request: RedFlagRequest
    rule_flags: list[RedFlag]
    llm_flags: list[RedFlag]
    llm_summary: str
    merged_flags: list[RedFlag]
    response: RedFlagResponse


class RedFlagAgent:
    """Coordinates rule checks, LLM analysis, merging, and validation."""

    SEVERITY_ORDER = {
        RiskSeverity.LOW: 1,
        RiskSeverity.MEDIUM: 2,
        RiskSeverity.HIGH: 3,
        RiskSeverity.CRITICAL: 4,
        "Low": 1,
        "Medium": 2,
        "High": 3,
        "Critical": 4,
    }

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config()
        self.rule_engine = RuleEngine(self.config)
        self.parser = PydanticOutputParser(pydantic_object=LLMRiskAnalysis)
        self.groq_service = GroqService(self.config)
        self.prompt_builder = PromptBuilder(self.parser)
        self.llm_analyzer = LLMRiskAnalyzer(
            config=self.config,
            groq_service=self.groq_service,
            prompt_builder=self.prompt_builder,
            parser=self.parser,
        )
        self.evidence_grounder = EvidenceGrounder()
        self.workflow = self._build_workflow()

    async def analyze(self, request: RedFlagRequest) -> RedFlagResponse:
        """Run the complete LangGraph workflow for one request."""

        start = time.perf_counter()
        logger.info(
            "Incoming red flag request company=%s year=%s metrics=%s sections=%s",
            request.company,
            request.financial_year,
            len(request.metrics),
            len(request.document_sections),
        )
        try:
            state = await self.workflow.ainvoke({"request": request})
            response = state.get("response")
            if not isinstance(response, RedFlagResponse):
                raise RuntimeError("workflow did not produce a validated response")
            return response
        except ValidationError:
            logger.exception("Response validation failed")
            raise
        except LLMAnalysisError:
            logger.exception("Required LLM analysis failed")
            raise
        except Exception:
            logger.exception("Unexpected RedFlagAgent failure")
            raise
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.info("Red flag processing time %.2f ms", elapsed_ms)

    def _build_workflow(self) -> Any:
        workflow = StateGraph(RedFlagState)
        workflow.add_node("rule_engine", self._rule_engine_node)
        workflow.add_node("llm_analysis", self._llm_analysis_node)
        workflow.add_node("merge_results", self._merge_results_node)
        workflow.add_node("validation", self._validation_node)
        workflow.set_entry_point("rule_engine")
        workflow.add_edge("rule_engine", "llm_analysis")
        workflow.add_edge("llm_analysis", "merge_results")
        workflow.add_edge("merge_results", "validation")
        workflow.add_edge("validation", END)
        return workflow.compile()

    async def _rule_engine_node(self, state: RedFlagState) -> dict[str, Any]:
        request = state["request"]
        flags = self.rule_engine.analyze(request)
        logger.info("Rule engine generated %s flags", len(flags))
        logger.debug("Rule engine results: %s", [flag.model_dump(mode="json") for flag in flags])
        return {"rule_flags": flags}

    async def _llm_analysis_node(self, state: RedFlagState) -> dict[str, Any]:
        request = state["request"]
        rule_flags = state.get("rule_flags", [])
        analysis = await self.llm_analyzer.analyze(request, rule_flags)
        return {"llm_flags": analysis.red_flags, "llm_summary": analysis.summary}

    async def _merge_results_node(self, state: RedFlagState) -> dict[str, Any]:
        request = state["request"]
        rule_flags = state.get("rule_flags", [])
        llm_flags = state.get("llm_flags", [])
        grounded_llm_flags, dropped_llm_flags = (
            self.evidence_grounder.filter_supported_flags(
                request,
                rule_flags,
                llm_flags,
            )
        )
        merged = self._merge_flags(rule_flags, grounded_llm_flags)
        logger.info(
            "Merged red flags rule=%s llm=%s dropped_llm=%s merged=%s",
            len(rule_flags),
            len(grounded_llm_flags),
            dropped_llm_flags,
            len(merged),
        )
        return {"merged_flags": merged}

    async def _validation_node(self, state: RedFlagState) -> dict[str, Any]:
        request = state["request"]
        flags = state.get("merged_flags", [])
        response = RedFlagResponse(
            company=request.company,
            financial_year=request.financial_year,
            red_flags=flags,
            overall_risk=self.calculate_overall_risk(flags),
            summary=self._build_summary(flags, state.get("llm_summary", "")),
        )
        return {"response": response}

    @classmethod
    def severity_rank(cls, severity: RiskSeverity | str) -> int:
        """Return a sortable integer for a severity."""

        return cls.SEVERITY_ORDER.get(severity, 0)

    @classmethod
    def calculate_overall_risk(cls, flags: list[RedFlag]) -> RiskSeverity:
        """Calculate overall risk from flag severity and concentration."""

        if not flags:
            return RiskSeverity.LOW

        max_rank = max(cls.severity_rank(flag.severity) for flag in flags)
        high_or_above = sum(
            1 for flag in flags if cls.severity_rank(flag.severity) >= 3
        )
        if max_rank >= 4 or high_or_above >= 3:
            return RiskSeverity.CRITICAL
        if max_rank >= 3:
            return RiskSeverity.HIGH
        if max_rank >= 2:
            return RiskSeverity.MEDIUM
        return RiskSeverity.LOW

    def _merge_flags(
        self,
        rule_flags: list[RedFlag],
        llm_flags: list[RedFlag],
    ) -> list[RedFlag]:
        merged_by_key: dict[tuple[str, str], RedFlag] = {}

        for flag in [*rule_flags, *llm_flags]:
            key = (str(flag.category), _normalize_text(flag.title))
            existing = merged_by_key.get(key)
            if existing is None:
                merged_by_key[key] = flag
                continue

            if self.severity_rank(flag.severity) > self.severity_rank(existing.severity):
                merged_by_key[key] = flag
                continue

            if len(flag.evidence) > len(existing.evidence):
                merged_by_key[key] = RedFlag(
                    category=existing.category,
                    title=existing.title,
                    severity=existing.severity,
                    description=existing.description,
                    evidence=flag.evidence,
                    recommendation=existing.recommendation,
                )

        return sorted(
            merged_by_key.values(),
            key=lambda flag: (
                -self.severity_rank(flag.severity),
                str(flag.category),
                flag.title,
            ),
        )

    def _build_summary(self, flags: list[RedFlag], llm_summary: str) -> str:
        if not flags:
            base = "No red flags were identified from the provided metrics and document sections."
        else:
            counts = {
                severity.value: sum(1 for flag in flags if flag.severity == severity)
                for severity in RiskSeverity
            }
            non_zero_counts = [
                f"{count} {severity.lower()}"
                for severity, count in counts.items()
                if count > 0
            ]
            base = (
                f"Identified {len(flags)} red flag(s): "
                + ", ".join(non_zero_counts)
                + "."
            )

        if llm_summary:
            return f"{base} LLM analysis: {llm_summary}"
        return base

REDFLAG_UI_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Red Flag Agent</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --ink: #17202a;
      --muted: #667085;
      --line: #d7dde6;
      --brand: #275d71;
      --brand-dark: #1f4a5a;
      --danger: #b42318;
      --warning: #b54708;
      --ok: #027a48;
      --shadow: 0 10px 24px rgba(17, 24, 39, 0.08);
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      background: var(--bg);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
        "Segoe UI", sans-serif;
    }

    header {
      border-bottom: 1px solid var(--line);
      background: #fff;
    }

    .topbar {
      width: min(1440px, calc(100% - 32px));
      margin: 0 auto;
      min-height: 64px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }

    h1 {
      margin: 0;
      font-size: 20px;
      line-height: 1.2;
      font-weight: 700;
      letter-spacing: 0;
    }

    main {
      width: min(1440px, calc(100% - 32px));
      margin: 18px auto 28px;
      display: grid;
      grid-template-columns: minmax(360px, 0.92fr) minmax(420px, 1.08fr);
      gap: 18px;
    }

    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
      min-width: 0;
    }

    .panel-head {
      min-height: 52px;
      padding: 12px 14px;
      border-bottom: 1px solid var(--line);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }

    .panel-title {
      margin: 0;
      font-size: 14px;
      line-height: 1.25;
      font-weight: 700;
    }

    .actions {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }

    button, a.button {
      appearance: none;
      border: 1px solid var(--line);
      background: #fff;
      color: var(--ink);
      border-radius: 6px;
      min-height: 34px;
      padding: 0 11px;
      font: inherit;
      font-size: 13px;
      font-weight: 650;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 7px;
      text-decoration: none;
      cursor: pointer;
      white-space: nowrap;
    }

    button:hover, a.button:hover { border-color: #9aa7b8; }
    button:disabled { opacity: 0.55; cursor: wait; }

    .primary {
      border-color: var(--brand);
      background: var(--brand);
      color: #fff;
    }

    .primary:hover { background: var(--brand-dark); border-color: var(--brand-dark); }

    .icon {
      width: 16px;
      height: 16px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
      line-height: 1;
      font-weight: 800;
    }

    select {
      min-height: 34px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      color: var(--ink);
      padding: 0 10px;
      font: inherit;
      font-size: 13px;
      font-weight: 650;
    }

    .file-input { display: none; }

    .button.file-button { cursor: pointer; }

    select {
      min-height: 34px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      color: var(--ink);
      padding: 0 10px;
      font: inherit;
      font-size: 13px;
      font-weight: 650;
    }

    .file-input { display: none; }

    .button.file-button { cursor: pointer; }

    select {
      min-height: 34px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      color: var(--ink);
      padding: 0 10px;
      font: inherit;
      font-size: 13px;
      font-weight: 650;
    }

    .file-input { display: none; }

    .button.file-button { cursor: pointer; }

    select {
      min-height: 34px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      color: var(--ink);
      padding: 0 10px;
      font: inherit;
      font-size: 13px;
      font-weight: 650;
    }

    .file-input { display: none; }

    .button.file-button { cursor: pointer; }

    .status-row {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }

    .badge {
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 5px 9px;
      font-size: 12px;
      font-weight: 700;
      color: var(--muted);
      background: #fff;
      white-space: nowrap;
    }

    .badge.ok { color: var(--ok); border-color: #abefc6; background: #ecfdf3; }
    .badge.warn { color: var(--warning); border-color: #fedf89; background: #fffaeb; }
    .badge.high { color: var(--danger); border-color: #fecdca; background: #fff1f3; }

    textarea {
      width: 100%;
      min-height: calc(100vh - 190px);
      resize: vertical;
      border: 0;
      outline: none;
      padding: 14px;
      color: #111827;
      background: #fbfcfe;
      font-family: "Cascadia Code", Consolas, "SFMono-Regular", monospace;
      font-size: 13px;
      line-height: 1.55;
      tab-size: 2;
    }

    .result-body {
      padding: 14px;
      display: grid;
      gap: 12px;
    }

    .summary-grid {
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 10px;
    }

    .metric {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
      background: #fbfcfe;
      min-height: 74px;
    }

    .metric span {
      display: block;
      color: var(--muted);
      font-size: 12px;
      font-weight: 650;
      margin-bottom: 6px;
    }

    .metric strong {
      display: block;
      font-size: 22px;
      line-height: 1.1;
      letter-spacing: 0;
    }

    .message {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 11px 12px;
      background: #fbfcfe;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
      white-space: pre-wrap;
    }

    .message.error {
      color: var(--danger);
      border-color: #fecdca;
      background: #fff1f3;
    }

    .flags {
      display: grid;
      gap: 10px;
    }

    .flag {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      background: #fff;
    }

    .flag-top {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 8px;
    }

    .flag-title {
      margin: 0;
      font-size: 15px;
      line-height: 1.3;
      font-weight: 750;
    }

    .category {
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      margin-bottom: 4px;
    }

    .flag p {
      margin: 7px 0 0;
      color: #344054;
      font-size: 13px;
      line-height: 1.45;
    }

    .label {
      color: var(--muted);
      font-weight: 750;
    }

    pre {
      margin: 0;
      overflow: auto;
      max-height: 280px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      background: #111827;
      color: #e5e7eb;
      font-size: 12px;
      line-height: 1.45;
    }

    @media (max-width: 920px) {
      .topbar, main { width: min(100% - 20px, 720px); }
      main { grid-template-columns: 1fr; }
      textarea { min-height: 420px; }
      .summary-grid { grid-template-columns: 1fr; }
      .panel-head { align-items: flex-start; flex-direction: column; }
      .actions { justify-content: flex-start; }
    }
  </style>
</head>
<body>
  <header>
    <div class="topbar">
      <h1>Red Flag Agent</h1>
      <div class="status-row">
        <span id="serviceStatus" class="badge warn">Checking</span>
        <span id="modelStatus" class="badge">Model</span>
        <a class="button" href="/docs" target="_blank" rel="noreferrer">
          <span class="icon">?</span> Docs
        </a>
      </div>
    </div>
  </header>

  <main>
    <section class="panel" aria-label="Request editor">
      <div class="panel-head">
        <h2 class="panel-title">Request JSON</h2>
        <div class="actions">
          <select id="sampleSelect" aria-label="Sample payload">
            <option value="risky">Risky sample</option>
            <option value="clean">Clean sample</option>
            <option value="governance">Governance sample</option>
          </select>
          <button id="sampleButton" type="button"><span class="icon">R</span> Reset</button>
          <label class="button file-button" for="fileInput"><span class="icon">I</span> Import</label>
          <input id="fileInput" class="file-input" type="file" accept=".json,application/json">
          <button id="formatButton" type="button"><span class="icon">{}</span> Format</button>
          <button id="runButton" class="primary" type="button">
            <span class="icon">&gt;</span> Analyze
          </button>
        </div>
      </div>
      <textarea id="requestInput" spellcheck="false" aria-label="Request JSON"></textarea>
    </section>

    <section class="panel" aria-label="Analysis result">
      <div class="panel-head">
        <h2 class="panel-title">Result</h2>
        <div class="actions">
          <select id="categoryFilter" aria-label="Category filter">
            <option value="all">All categories</option>
          </select>
          <select id="severityFilter" aria-label="Severity filter">
            <option value="all">All severities</option>
            <option value="Critical">Critical</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>
          <button id="copyButton" type="button"><span class="icon">C</span> Copy JSON</button>
          <button id="downloadButton" type="button"><span class="icon">D</span> Download</button>
        </div>
      </div>
      <div class="result-body">
        <div class="summary-grid">
          <div class="metric"><span>Company</span><strong id="companyValue">-</strong></div>
          <div class="metric"><span>Overall Risk</span><strong id="riskValue">-</strong></div>
          <div class="metric"><span>Total Flags</span><strong id="countValue">0</strong></div>
          <div class="metric"><span>Visible Flags</span><strong id="visibleCountValue">0</strong></div>
          <div class="metric"><span>High or Critical</span><strong id="highCountValue">0</strong></div>
        </div>
        <div id="summaryValue" class="message">Run an analysis to populate results.</div>
        <div id="flagsValue" class="flags"></div>
        <pre id="rawValue">{}</pre>
      </div>
    </section>
  </main>

  <script>
    const samplePayloads = {
      risky: {
        company: "Example Industries Ltd",
        financial_year: "2025",
        metrics: {
          revenue: { current: 900, previous: 1000 },
          revenue_growth: { current: 2, previous: 12 },
          net_profit: { current: 60, previous: 100 },
          ebitda: { current: 120, previous: 180 },
          current_ratio: 0.75,
          debt_to_equity: 2.6,
          interest_coverage: 1.0,
          interest_expense: 120,
          operating_cash_flow: 20,
          total_assets: { current: 1000, previous: 1100 },
          total_liabilities: { current: 900, previous: 700 }
        },
        document_sections: [
          {
            section: "Auditor Report",
            content: "The auditor included a material uncertainty related to going concern."
          },
          {
            section: "Notes",
            content: "Management disclosed pending litigation and a covenant breach under the loan agreement."
          }
        ]
      },
      clean: {
        company: "Clean Operations Ltd",
        financial_year: "2025",
        metrics: {
          revenue: { current: 1250, previous: 1100 },
          revenue_growth: { current: 13.6, previous: 9.8 },
          net_profit: { current: 160, previous: 130 },
          ebitda: { current: 290, previous: 245 },
          current_ratio: 1.9,
          debt_to_equity: 0.35,
          interest_coverage: 8.2,
          operating_cash_flow: 190,
          total_assets: { current: 1800, previous: 1640 },
          total_liabilities: { current: 620, previous: 600 }
        },
        document_sections: [
          {
            section: "Auditor Report",
            content: "The auditor did not issue a qualified opinion and did not identify going concern uncertainty."
          }
        ]
      },
      governance: {
        company: "Governance Watch Ltd",
        financial_year: "2025",
        metrics: {
          revenue: { current: 760, previous: 780 },
          net_profit: { current: 42, previous: 55 },
          current_ratio: 1.15,
          debt_to_equity: 1.7,
          operating_cash_flow: 18,
          total_assets: { current: 990, previous: 1010 },
          total_liabilities: { current: 790, previous: 690 }
        },
        document_sections: [
          {
            section: "Risk Factors",
            content: "The company disclosed a regulatory investigation, pending litigation, and contingent liabilities."
          },
          {
            section: "Notes",
            content: "Management reported an asset impairment and an event of default under borrowing arrangements."
          }
        ]
      }
    };
    const requestInput = document.querySelector("#requestInput");
    const runButton = document.querySelector("#runButton");
    const sampleButton = document.querySelector("#sampleButton");
    const sampleSelect = document.querySelector("#sampleSelect");
    const fileInput = document.querySelector("#fileInput");
    const formatButton = document.querySelector("#formatButton");
    const copyButton = document.querySelector("#copyButton");
    const downloadButton = document.querySelector("#downloadButton");
    const categoryFilter = document.querySelector("#categoryFilter");
    const severityFilter = document.querySelector("#severityFilter");
    const rawValue = document.querySelector("#rawValue");
    const summaryValue = document.querySelector("#summaryValue");
    const flagsValue = document.querySelector("#flagsValue");
    const companyValue = document.querySelector("#companyValue");
    const riskValue = document.querySelector("#riskValue");
    const countValue = document.querySelector("#countValue");
    const visibleCountValue = document.querySelector("#visibleCountValue");
    const highCountValue = document.querySelector("#highCountValue");
    const serviceStatus = document.querySelector("#serviceStatus");
    const modelStatus = document.querySelector("#modelStatus");

    let lastResponse = {};
    let currentFlags = [];

    function pretty(value) {
      return JSON.stringify(value, null, 2);
    }

    function setSample() {
      const selected = sampleSelect.value || "risky";
      requestInput.value = pretty(samplePayloads[selected]);
    }

    function setMessage(message, isError = false) {
      summaryValue.textContent = message;
      summaryValue.classList.toggle("error", isError);
    }

    function severityClass(severity) {
      if (["Critical", "High"].includes(severity)) return "badge high";
      if (severity === "Medium") return "badge warn";
      return "badge ok";
    }

    function populateCategoryFilter(flags) {
      const selected = categoryFilter.value || "all";
      const categories = Array.from(new Set(flags.map((flag) => flag.category || "Risk"))).sort();
      categoryFilter.innerHTML = '<option value="all">All categories</option>';
      for (const category of categories) {
        const option = document.createElement("option");
        option.value = category;
        option.textContent = category;
        categoryFilter.appendChild(option);
      }
      categoryFilter.value = categories.includes(selected) ? selected : "all";
    }

    function renderFlags() {
      const category = categoryFilter.value || "all";
      const severity = severityFilter.value || "all";
      const visibleFlags = currentFlags.filter((flag) => {
        const categoryMatches = category === "all" || flag.category === category;
        const severityMatches = severity === "all" || flag.severity === severity;
        return categoryMatches && severityMatches;
      });

      visibleCountValue.textContent = String(visibleFlags.length);
      flagsValue.innerHTML = "";

      if (!visibleFlags.length) {
        const empty = document.createElement("div");
        empty.className = "message";
        empty.textContent = currentFlags.length ? "No red flags match the selected filters." : "No red flags to show.";
        flagsValue.appendChild(empty);
        return;
      }

      for (const flag of visibleFlags) {
        const item = document.createElement("article");
        item.className = "flag";
        item.innerHTML = `
          <div class="flag-top">
            <div>
              <div class="category"></div>
              <h3 class="flag-title"></h3>
            </div>
            <span class="${severityClass(flag.severity)}"></span>
          </div>
          <p class="description"></p>
          <p><span class="label">Evidence:</span> <span class="evidence"></span></p>
          <p><span class="label">Recommendation:</span> <span class="recommendation"></span></p>
        `;
        item.querySelector(".category").textContent = flag.category || "Risk";
        item.querySelector(".flag-title").textContent = flag.title || "Untitled";
        item.querySelector(".badge").textContent = flag.severity || "Low";
        item.querySelector(".description").textContent = flag.description || "";
        item.querySelector(".evidence").textContent = flag.evidence || "";
        item.querySelector(".recommendation").textContent = flag.recommendation || "";
        flagsValue.appendChild(item);
      }
    }

    function renderResult(data) {
      lastResponse = data || {};
      currentFlags = Array.isArray(lastResponse.red_flags) ? lastResponse.red_flags : [];
      companyValue.textContent = lastResponse.company || "-";
      riskValue.textContent = lastResponse.overall_risk || "-";
      countValue.textContent = String(currentFlags.length);
      highCountValue.textContent = String(currentFlags.filter((flag) => ["Critical", "High"].includes(flag.severity)).length);
      populateCategoryFilter(currentFlags);
      setMessage(lastResponse.summary || "No summary returned.");
      rawValue.textContent = pretty(lastResponse);
      renderFlags();
    }

    function downloadResult() {
      const blob = new Blob([pretty(lastResponse)], { type: "application/json" });
      const link = document.createElement("a");
      const company = (lastResponse.company || "redflag-analysis").replace(/[^a-z0-9-]+/gi, "-").replace(/^-+|-+$/g, "");
      link.href = URL.createObjectURL(blob);
      link.download = `${company || "redflag-analysis"}.json`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(link.href);
      setMessage("Result JSON downloaded.");
    }
    async function refreshHealth() {
      try {
        const response = await fetch("/health");
        const data = await response.json();
        serviceStatus.textContent = data.status === "ok" ? "Online" : "Unavailable";
        serviceStatus.className = data.status === "ok" ? "badge ok" : "badge high";
        modelStatus.textContent = data.llm_configured ? data.model : "Rules only";
        modelStatus.className = data.llm_configured ? "badge ok" : "badge warn";
      } catch (error) {
        serviceStatus.textContent = "Offline";
        serviceStatus.className = "badge high";
        modelStatus.textContent = "Model";
        modelStatus.className = "badge";
      }
    }

    async function runAnalysis() {
      let payload;
      try {
        payload = JSON.parse(requestInput.value);
      } catch (error) {
        setMessage(`Invalid JSON: ${error.message}`, true);
        return;
      }

      runButton.disabled = true;
      setMessage("Analyzing...");
      try {
        const response = await fetch("/redflags", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(pretty(data));
        }
        renderResult(data);
      } catch (error) {
        setMessage(error.message || String(error), true);
      } finally {
        runButton.disabled = false;
      }
    }

    sampleButton.addEventListener("click", setSample);
    sampleSelect.addEventListener("change", setSample);
    fileInput.addEventListener("change", async () => {
      const file = fileInput.files && fileInput.files[0];
      if (!file) return;
      try {
        const text = await file.text();
        const payload = JSON.parse(text);
        requestInput.value = pretty(payload);
        setMessage(`Imported ${file.name}.`);
      } catch (error) {
        setMessage(`Could not import JSON: ${error.message}`, true);
      } finally {
        fileInput.value = "";
      }
    });
    formatButton.addEventListener("click", () => {
      try {
        requestInput.value = pretty(JSON.parse(requestInput.value));
        setMessage("JSON formatted.");
      } catch (error) {
        setMessage(`Invalid JSON: ${error.message}`, true);
      }
    });
    categoryFilter.addEventListener("change", renderFlags);
    severityFilter.addEventListener("change", renderFlags);
    runButton.addEventListener("click", runAnalysis);
    copyButton.addEventListener("click", async () => {
      await navigator.clipboard.writeText(pretty(lastResponse));
      setMessage("Result JSON copied.");
    });
    downloadButton.addEventListener("click", downloadResult);

    setSample();
    renderResult({ red_flags: [] });
    refreshHealth();
  </script>
</body>
</html>"""

class APIController:
    """FastAPI route controller for the Red Flag Agent."""

    def __init__(self, agent: RedFlagAgent) -> None:
        self.agent = agent
        self.router = APIRouter()
        self.router.add_api_route(
            "/",
            self.ui,
            methods=["GET"],
            response_class=HTMLResponse,
            include_in_schema=False,
        )
        self.router.add_api_route(
            "/ui",
            self.ui,
            methods=["GET"],
            response_class=HTMLResponse,
            include_in_schema=False,
        )
        self.router.add_api_route(
            "/health",
            self.health,
            methods=["GET"],
            response_model=HealthResponse,
        )
        self.router.add_api_route(
            "/redflags",
            self.redflags,
            methods=["POST"],
            response_model=RedFlagResponse,
            status_code=status.HTTP_200_OK,
        )

    async def ui(self) -> HTMLResponse:
        """Return a browser UI for exercising the red flag API."""

        return HTMLResponse(REDFLAG_UI_HTML)

    async def health(self) -> HealthResponse:
        """Return basic service health and LLM configuration status."""

        return HealthResponse(
            status="ok",
            service="redflag-agent",
            llm_configured=self.agent.config.llm_configured,
            model=self.agent.config.groq_model,
        )

    async def redflags(self, request: RedFlagRequest) -> RedFlagResponse:
        """Analyze an Extraction Agent payload and return red flags."""

        if not request.metrics:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="metrics must not be empty",
            )

        try:
            return await self.agent.analyze(request)
        except LLMTimeoutError as exc:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=str(exc),
            ) from exc
        except LLMOutputParsingError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(exc),
            ) from exc
        except LLMServiceUnavailableError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc
        except ValidationError as exc:
            logger.exception("Internal response validation failure")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal response validation failed",
            ) from exc
        except Exception as exc:
            logger.exception("Unexpected API failure")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unexpected red flag analysis failure",
            ) from exc


def configure_logging(config: Config) -> None:
    """Configure process-wide logging once."""

    logging.basicConfig(
        level=getattr(logging, config.log_level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def find_available_port(host: str, preferred_port: int) -> int:
    """Return preferred_port if free, otherwise the next free local port."""

    bind_host = "127.0.0.1" if host in {"127.0.0.1", "::"} else host
    for port in range(preferred_port, preferred_port + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((bind_host, port))
            except OSError:
                continue
            return port
    raise RuntimeError(
        f"No available port found from {preferred_port} to {preferred_port + 99}"
    )
def create_app(config: Config | None = None) -> FastAPI:
    """Application factory used by Uvicorn and tests."""

    resolved_config = config or Config()
    configure_logging(resolved_config)
    agent = RedFlagAgent(resolved_config)
    controller = APIController(agent)

    app = FastAPI(
        title="Red Flag Agent API",
        description=(
            "Detects financial red flags from structured metrics and supplied "
            "document sections using deterministic rules and Groq-backed LLM analysis."
        ),
        version="1.0.0",
    )
    app.include_router(controller.router)

    @app.exception_handler(RequestValidationError)
    async def request_validation_exception_handler(
        _: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        logger.warning("Request validation failed: %s", exc.errors())
        return JSONResponse(
            status_code=422,
            content={"detail": jsonable_encoder(exc.errors())},
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(
        _: Request,
        exc: ValidationError,
    ) -> JSONResponse:
        logger.exception("Validation failure: %s", exc.errors())
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal validation failure"},
        )

    return app


app = create_app()


if __name__ == "__main__":
    runtime_config = Config()
    configure_logging(runtime_config)
    runtime_port = find_available_port(runtime_config.host, runtime_config.port)
    if runtime_port != runtime_config.port:
        logger.warning(
            "Configured port %s is busy; starting on %s instead",
            runtime_config.port,
            runtime_port,
        )
    uvicorn.run(
        app,
        host=runtime_config.host,
        port=runtime_port,
        reload=False,
    )


