from backend.database.database import SessionLocal
from backend.database.crud import *

db = SessionLocal()

query = create_research_query(
    db,
    "What is Apple's revenue?",
    "Apple reported approximately $391 billion revenue."
)

print("Created:", query.query_id)

print("\nAll Queries")
for q in get_all_research_queries(db):
    print(q.query_id, q.question)

update_research_query(
    db,
    query.query_id,
    "Apple reported approximately $400 billion revenue."
)

print("\nUpdated Successfully")

delete_research_query(
    db,
    query.query_id
)

print("Deleted Successfully")

db.close()