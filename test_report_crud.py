from backend.database.database import SessionLocal
from backend.database.models import User
from backend.database.crud import (
    create_report,
    get_report,
    get_reports_by_user,
    delete_report
)

db = SessionLocal()

# Ensure we have a user with ID 1
user = db.query(User).filter(User.user_id == 1).first()
if not user:
    from backend.main import hash_password
    pw_hash, salt = hash_password("password123")
    user = User(user_id=1, username="test_user", password_hash=pw_hash, password_salt=salt)
    db.add(user)
    db.commit()
    db.refresh(user)

print("Creating Report...")
report = create_report(
    db,
    user.user_id,
    "Apple Financial Analysis",
    "reports/apple_report.pdf",
    "1,2",                      # document_ids (comma-separated string)
    "Executive Summary,Key Financials" # sections (comma-separated string)
)

print("Created Report ID:", report.report_id)

print("Fetching Report...")
fetched = get_report(db, report.report_id)
print("Fetched Title:", fetched.report_title)

print("Fetching Reports by User...")
reports = get_reports_by_user(db, user.user_id)
print("Number of reports for user:", len(reports))

# Clean up
print("Cleaning up report...")
delete_report(db, report.report_id)
print("Cleanup complete.")

db.close()