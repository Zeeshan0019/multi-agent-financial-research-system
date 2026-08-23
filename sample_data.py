from backend.database.database import SessionLocal
from backend.database.models import (
    ResearchSession,
    Company,
    Document,
    FinancialMetric,
    RedFlag,
    ComparisonResult,
    ResearchQuery,
    Report
)

db = SessionLocal()

# ----------------------------
# Research Session
# ----------------------------
session = ResearchSession(
    session_name="Apple Financial Analysis",
    description="FY2024 Annual Report"
)
db.add(session)
db.commit()
db.refresh(session)

# ----------------------------
# Company
# ----------------------------
company = Company(
    company_name="Apple Inc.",
    industry="Technology",
    fiscal_year="2024"
)
db.add(company)
db.commit()
db.refresh(company)

# ----------------------------
# Document
# ----------------------------
document = Document(
    session_id=session.session_id,
    company_id=company.company_id,
    file_name="Apple_Annual_Report.pdf",
    file_path="uploads/apple.pdf"
)
db.add(document)
db.commit()
db.refresh(document)

# ----------------------------
# Financial Metrics
# ----------------------------
metric = FinancialMetric(
    document_id=document.document_id,
    revenue=391000,
    net_income=99800,
    total_assets=352000,
    total_liabilities=290000,
    eps=6.11,
    debt_to_equity=1.85
)
db.add(metric)

# ----------------------------
# Red Flag
# ----------------------------
flag = RedFlag(
    document_id=document.document_id,
    risk_type="Debt Increase",
    severity="Medium",
    description="Debt increased compared to previous year."
)
db.add(flag)

# ----------------------------
# Comparison Result
# ----------------------------
comparison = ComparisonResult(
    company1_id=1,
    company2_id=2,
    comparison_summary="Apple has higher revenue while Microsoft has higher cloud growth."

)
db.add(comparison)

# ----------------------------
# Research Query
# ----------------------------
query = ResearchQuery(
    session_id=session.session_id,
    question="What are Apple's financial risks?",
    answer="Debt increased slightly but revenue remained strong."
)
db.add(query)

# ----------------------------
# Report
# ----------------------------
report = Report(
    session_id=session.session_id,
    report_title="Apple Financial Research Report",
    report_path="reports/apple_report.pdf"
)
db.add(report)

db.commit()

print("All sample data inserted successfully!")