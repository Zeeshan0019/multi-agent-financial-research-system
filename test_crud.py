from backend.database.database import SessionLocal
from backend.database.models import User
from backend.database.crud import (
    create_company,
    create_document,
    delete_company,
    delete_document
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

print("Using User ID:", user.user_id)

print("Creating Company...")
company = create_company(
    db,
    "Apple Inc.",
    "Technology",
    "2024"
)

print("Company ID:", company.company_id)

print("Creating Document...")
document = create_document(
    db,
    user.user_id,
    company.company_id,
    "Apple_Annual_Report.pdf",
    "uploads/apple.pdf"
)

print("Document ID:", document.document_id)
print("Data inserted successfully!")

# Clean up
print("Cleaning up created test data...")
delete_document(db, document.document_id)
delete_company(db, company.company_id)
print("Cleanup complete.")

db.close()