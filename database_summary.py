from backend.database.database import SessionLocal
from backend.database.models import *

db = SessionLocal()

print("=" * 50)
print("DATABASE SUMMARY")
print("=" * 50)

print("Research Sessions :", db.query(ResearchSession).count())
print("Companies         :", db.query(Company).count())
print("Documents         :", db.query(Document).count())
print("Financial Metrics :", db.query(FinancialMetric).count())
print("Red Flags         :", db.query(RedFlag).count())
print("Comparisons       :", db.query(ComparisonResult).count())
print("Research Queries  :", db.query(ResearchQuery).count())
print("Reports           :", db.query(Report).count())

db.close()