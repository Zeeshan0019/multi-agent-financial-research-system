from backend.database.database import SessionLocal
from backend.database.models import Company

db = SessionLocal()

companies = db.query(Company).all()

print("===== Companies =====")

for company in companies:
    print(
        company.company_id,
        company.company_name,
        company.industry,
        company.fiscal_year
    )