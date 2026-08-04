"""
demo_comparison.py

Standalone runner for the Comparison Agent -- proves the agent works before
you wire it into the LangGraph orchestrator / FastAPI endpoint.

Run:
    python demo_comparison.py

What it does (mirrors Step 7-8-11 of your project's Step-by-Step Workflow):
    1. Loads "extracted" financial metrics (stand-in for what the Extraction
       Agent would have written to MongoDB) for NexaCore + 4 peers.
    2. Runs the Comparison Agent to benchmark NexaCore against the peer group.
    3. Prints the structured comparison result as JSON (what would be stored
       in the "Reports" / passed to the Research Agent).
    4. Hands the result to a small Report Agent stub that renders it into an
       analyst-style PDF (using ReportLab, per your tech stack).
"""

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agents"))

from comparison_agent import ComparisonAgent
from schemas import CompanyMetrics


def load_companies(path: str):
    with open(path) as f:
        raw = json.load(f)
    return [CompanyMetrics(**c) for c in raw]


def main():
    data_path = os.path.join(os.path.dirname(__file__), "sample_data", "company_metrics.json")
    companies = load_companies(data_path)

    agent = ComparisonAgent(use_llm=True)  # falls back to templated narrative if no GROQ_API_KEY
    result = agent.compare(companies, focus_company="NexaCore Technologies")

    out_path = os.path.join(os.path.dirname(__file__), "comparison_result.json")
    with open(out_path, "w") as f:
        json.dump(result.model_dump(), f, indent=2)
    print(f"Comparison result written to {out_path}\n")
    print(json.dumps(result.model_dump(), indent=2))

    # Hand off to the Report Agent stub
    from report_agent_stub import render_comparison_pdf
    pdf_path = os.path.join(os.path.dirname(__file__), "comparison_report.pdf")
    render_comparison_pdf(result, pdf_path)
    print(f"\nPDF report written to {pdf_path}")


if __name__ == "__main__":
    main()
