from backend.database.database import SessionLocal
from backend.database.crud import *

db = SessionLocal()

report = create_report(
    db,
    1,
    "Apple Financial Analysis",
    "reports/apple_report.pdf"
)

print("Created:", report.report_id)

print("\nAll Reports")
for r in get_all_reports(db):
    print(r.report_id, r.report_title)

update_report(
    db,
    report.report_id,
    "Updated Apple Financial Report"
)

print("\nUpdated Successfully")

delete_report(
    db,
    report.report_id
)

print("Deleted Successfully")

db.close()