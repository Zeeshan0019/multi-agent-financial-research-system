
import inspect
from backend.database import crud

print(inspect.signature(crud.create_company))
from backend.database.database import SessionLocal
from backend.database.crud import *

db = SessionLocal()

company = create_company(
    db,
    "Tesla",
    "Automobile",
    "2025"
)

print("Created:", company.company_id)

print("\nAll Companies")
for c in get_all_companies(db):
    print(c.company_id, c.company_name)

update_company(db, company.company_id, "Tesla Inc.")

print("\nUpdated")

delete_company(db, company.company_id)

print("Deleted")

db.close()