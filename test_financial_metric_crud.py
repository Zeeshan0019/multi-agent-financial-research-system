from backend.database.database import SessionLocal
from backend.database.models import User
from backend.database.crud import (
    create_company,
    create_document,
    create_financial_metric,
    get_financial_metric,
    get_metrics_by_document,
    delete_financial_metric,
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
company = create_company(db, "Test Corp", "Finance", "2024")
document = create_document(db, user.user_id, company.company_id, "test.pdf", "uploads/test.pdf")

print("Creating Financial Metric...")
metric = create_financial_metric(
    db,
    document.document_id,  # document_id
    391.0,                 # revenue
    99.8,                  # net_income
    120.0,                 # ebitda
    352.0,                 # total_assets
    290.0,                 # total_liabilities
    6.11,                  # eps
    1.85                   # debt_to_equity
)

print("Created Metric ID:", metric.metric_id)

print("Fetching Metric...")
fetched = get_financial_metric(db, metric.metric_id)
print("Fetched Revenue:", fetched.revenue)

print("Fetching Metric by Document...")
doc_metric = get_metrics_by_document(db, document.document_id)
print("Doc Metric EPS:", doc_metric.eps)

# Clean up
print("Cleaning up metric, document and company...")
delete_financial_metric(db, metric.metric_id)
delete_document(db, document.document_id)
delete_company(db, company.company_id)
print("Cleanup complete.")

db.close()