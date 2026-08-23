from backend.database.database import SessionLocal
from backend.database.models import User
from backend.database.crud import (
    create_company,
    create_document,
    create_red_flag,
    get_red_flag,
    get_red_flags_by_document,
    delete_red_flag,
    delete_document,
    delete_company
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

print("Creating dummy company and document...")
company = create_company(db, "RedFlag Corp", "Finance", "2024")
document = create_document(db, user.user_id, company.company_id, "flag_test.pdf", "uploads/flag_test.pdf")

print("Creating Red Flag...")
flag = create_red_flag(
    db,
    document.document_id,
    "High Debt",
    "medium",
    "Debt increased by 10% over the previous year."
)

print("Created Red Flag ID:", flag.red_flag_id)

print("Fetching Red Flag...")
fetched = get_red_flag(db, flag.red_flag_id)
print("Fetched Severity:", fetched.severity)

print("Fetching Red Flags by Document...")
flags = get_red_flags_by_document(db, document.document_id)
print("Number of flags on document:", len(flags))

# Clean up
print("Cleaning up flag, document and company...")
delete_red_flag(db, flag.red_flag_id)
delete_document(db, document.document_id)
delete_company(db, company.company_id)
print("Cleanup complete.")

db.close()