from backend.database.database import SessionLocal
from backend.database.crud import *

db = SessionLocal()

metric = create_financial_metric(
    db,
    1,        # document_id
    391.0,    # revenue
    99.8,     # net_income
    352.0,    # total_assets
    290.0,    # total_liabilities
    6.11,     # eps
    1.85      # debt_to_equity
)

print("Created:", metric.metric_id)

print("\nAll Metrics")
for m in get_all_financial_metrics(db):
    print(m.metric_id, m.revenue)

update_financial_metric(
    db,
    metric.metric_id,
    400.0
)

print("\nUpdated Successfully")

delete_financial_metric(
    db,
    metric.metric_id
)

print("Deleted Successfully")

db.close()