from backend.database.database import SessionLocal
from backend.database.crud import *

db = SessionLocal()

comparison = create_comparison_result(
    db,
    1,
    2,
    "Apple has higher revenue while Microsoft has stronger cloud growth."
)

print("Created:", comparison.comparison_id)

print("\nAll Comparisons")
for c in get_all_comparison_results(db):
    print(c.comparison_id, c.comparison_summary)

update_comparison_result(
    db,
    comparison.comparison_id,
    "Updated comparison summary."
)

print("\nUpdated Successfully")

delete_comparison_result(
    db,
    comparison.comparison_id
)

print("Deleted Successfully")

db.close()