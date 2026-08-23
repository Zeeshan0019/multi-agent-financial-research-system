from backend.database.database import SessionLocal
from backend.database.models import User
from backend.database.crud import (
    create_company,
    create_document,
    create_research_query,
    get_research_query,
    get_queries_by_user,
    delete_research_query,
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
company = create_company(db, "Query Corp", "Finance", "2024")
document = create_document(db, user.user_id, company.company_id, "query_test.pdf", "uploads/query_test.pdf")

print("Creating Research Query...")
query = create_research_query(
    db,
    user.user_id,
    document.document_id,
    "What is Apple's revenue?",
    "Apple reported approximately $391 billion revenue."
)

print("Created Query ID:", query.query_id)

print("Fetching Research Query...")
fetched = get_research_query(db, query.query_id)
print("Fetched Question:", fetched.question)

print("Fetching Research Queries by User...")
queries = get_queries_by_user(db, user.user_id)
print("Number of queries for user:", len(queries))

# Clean up
print("Cleaning up query, document and company...")
delete_research_query(db, query.query_id)
delete_document(db, document.document_id)
delete_company(db, company.company_id)
print("Cleanup complete.")

db.close()