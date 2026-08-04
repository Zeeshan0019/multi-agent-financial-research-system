"""
run_comparison.py

End-to-End runner for Comparing NexaCore Technologies against another financial document
(InfoEdge Systems) using the completed Comparison Agent.

Usage:
    python run_comparison.py
"""

import os
import json

from comparison_agent import ComparisonAgent
from report_agent_stub import render_comparison_pdf


def main():
    base_dir = os.path.dirname(__file__)

    # Document 1: User's nexacore document
    doc1_path = os.path.join(base_dir, "nexacore_financial_document_final.pdf")

    # Document 2: Chosen peer document (InfoEdge Systems)
    doc2_path = os.path.join(base_dir, "infoedge_financial_document.pdf")

    print("==========================================================================")
    print("FINANCIAL COMPARISON AGENT - RUNNING DOCUMENT COMPARISON")
    print("==========================================================================")
    print(f"Document 1 (Focus Company): {os.path.basename(doc1_path)}")
    print(f"Document 2 (Peer Target)  : {os.path.basename(doc2_path)}")
    print("--------------------------------------------------------------------------")

    # Run Comparison Agent
    agent = ComparisonAgent(use_llm=True)
    result = agent.compare_two_documents(
        pdf_path1=doc1_path,
        pdf_path2=doc2_path,
        focus_company="NexaCore Technologies"
    )

    # 1. Output structured JSON result
    json_out_path = os.path.join(base_dir, "comparison_result.json")
    result_dict = result.model_dump()
    with open(json_out_path, "w", encoding="utf-8") as f:
        json.dump(result_dict, f, indent=2)

    print(f"\n[OK] Structured JSON result written to: {json_out_path}\n")

    # Print summary highlights in terminal
    print("Narrative Summary:")
    print(result.narrative_summary)
    print("\nSide-by-Side Metric Comparison:")
    print(f"{'Metric':<32} {'NexaCore':<14} {'Infoedge':<14} {'Variance':<12} {'Assessment'}")
    print("-" * 80)
    for m in result.metric_comparisons:
        f_val = f"{m.focus_company_value:,.1f}" if m.focus_company_value is not None else "-"
        p_val = f"{m.peer_average:,.1f}" if m.peer_average is not None else "-"
        diff = f"{m.focus_vs_peer_avg_pct:+.1f}%" if m.focus_vs_peer_avg_pct is not None else "-"
        print(f"{m.metric:<32} {f_val:<14} {p_val:<14} {diff:<12} {m.flag}")

    # 2. Render analyst-style PDF report
    pdf_out_path = os.path.join(base_dir, "comparison_report.pdf")
    render_comparison_pdf(
        result=result,
        out_path=pdf_out_path,
        source_docs=f"{os.path.basename(doc1_path)}, {os.path.basename(doc2_path)}"
    )

    print(f"\n[OK] Visual PDF report written to: {pdf_out_path}")
    print("==========================================================================")


if __name__ == "__main__":
    main()
