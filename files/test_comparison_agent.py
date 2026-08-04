"""
test_comparison_agent.py

Unit tests for the Comparison Agent, PDF Metric Extractor, and Document Benchmarking.
Run with:
    pytest test_comparison_agent.py -v
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(__file__))

from comparison_agent import ComparisonAgent
from pdf_extractor import extract_company_metrics_from_pdf
from schemas import CompanyMetrics


def make_company(name, revenue, ebit_margin, dso):
    return CompanyMetrics(
        company_name=name,
        fiscal_year="FY2025",
        source_document="test.pdf",
        revenue_cr=revenue,
        ebit_margin_pct=ebit_margin,
        dso_days=dso,
    )


def test_requires_at_least_two_companies():
    agent = ComparisonAgent(use_llm=False)
    with pytest.raises(ValueError):
        agent.compare([make_company("A", 100, 20, 60)], focus_company="A")


def test_higher_revenue_flags_outperform():
    agent = ComparisonAgent(use_llm=False)
    companies = [
        make_company("A", 200, 20, 60),
        make_company("B", 90, 18, 65),
        make_company("C", 80, 17, 70),
    ]
    result = agent.compare(companies, focus_company="A")
    rev_metric = next(m for m in result.metric_comparisons if m.metric.startswith("Revenue"))
    assert rev_metric.flag == "outperform"
    assert rev_metric.focus_rank == 1


def test_lower_is_better_metric_dso():
    agent = ComparisonAgent(use_llm=False)
    companies = [
        make_company("A", 100, 20, 90),   # worst (highest) DSO
        make_company("B", 100, 20, 60),
        make_company("C", 100, 20, 55),
    ]
    result = agent.compare(companies, focus_company="A")
    dso_metric = next(m for m in result.metric_comparisons if "Days Sales" in m.metric)
    assert dso_metric.flag == "underperform"
    assert dso_metric.focus_rank == 3  # worst of 3


def test_narrative_is_nonempty_without_llm():
    agent = ComparisonAgent(use_llm=False)
    companies = [make_company("A", 100, 20, 60), make_company("B", 90, 18, 65)]
    result = agent.compare(companies, focus_company="A")
    assert len(result.narrative_summary) > 0


def test_pairwise_document_comparison():
    agent = ComparisonAgent(use_llm=False)
    doc1 = os.path.join(os.path.dirname(__file__), "nexacore_financial_document_final.pdf")
    doc2 = os.path.join(os.path.dirname(__file__), "infoedge_financial_document.pdf")
    assert os.path.exists(doc1)
    assert os.path.exists(doc2)

    result = agent.compare_two_documents(doc1, doc2, focus_company="NexaCore Technologies")
    assert result.focus_company == "NexaCore Technologies"
    assert len(result.companies_compared) == 2
    assert len(result.metric_comparisons) == 10
