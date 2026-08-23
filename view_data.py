from backend.database.database import SessionLocal
from backend.database.models import User, Company, Document, FinancialMetric, RedFlag, ComparisonResult, ResearchQuery, Report

db = SessionLocal()

print("\n========== USERS ==========")
for row in db.query(User).all():
    print(row.user_id, row.username)

print("\n========== COMPANIES ==========")
for row in db.query(Company).all():
    print(row.company_id, row.company_name)

print("\n========== DOCUMENTS ==========")
for row in db.query(Document).all():
    print(row.document_id, row.file_name)

print("\n========== FINANCIAL METRICS ==========")
for row in db.query(FinancialMetric).all():
    print(row.metric_id, row.revenue)

print("\n========== RED FLAGS ==========")
for row in db.query(RedFlag).all():
    print(
        row.red_flag_id,
        row.risk_type,
        row.severity,
        row.description
    )

print("\n========== COMPARISON RESULTS ==========")
for row in db.query(ComparisonResult).all():
    print(row.comparison_id, row.comparison_summary)

print("\n========== RESEARCH QUERIES ==========")
for row in db.query(ResearchQuery).all():
    print(row.query_id, row.question)

print("\n========== REPORTS ==========")
for row in db.query(Report).all():
    print(row.report_id, row.report_title)

db.close()