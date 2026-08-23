from backend.database.database import SessionLocal
from backend.database.models import User
from backend.database.crud import (
    create_company,
    create_comparison_result,
    get_comparison_result,
    delete_comparison_result,
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

print("Creating dummy companies...")
c1 = create_company(db, "Apple", "Tech", "2024")
c2 = create_company(db, "Microsoft", "Tech", "2024")

print("Creating Comparison Result...")
comparison = create_comparison_result(
    db,
    user.user_id,
    c1.company_id,
    c2.company_id,
    "Apple has higher revenue while Microsoft has stronger cloud growth."
)

print("Created Comparison ID:", comparison.comparison_id)

print("Fetching Comparison Result...")
fetched = get_comparison_result(db, comparison.comparison_id)
print("Fetched Summary:", fetched.comparison_summary)

# Clean up
print("Cleaning up comparison and companies...")
delete_comparison_result(db, comparison.comparison_id)
delete_company(db, c1.company_id)
delete_company(db, c2.company_id)
print("Cleanup complete.")

db.close()