from backend.database.database import SessionLocal
from backend.database.crud import *

db = SessionLocal()

flag = create_red_flag(
    db,
    1,
    "High Debt",
    "Medium",
    "Debt increased by 10% over the previous year."
)

print("Created:", flag.red_flag_id)

print("\nAll Red Flags")
for f in get_all_red_flags(db):
    print(f.red_flag_id, f.risk_type, f.severity)

update_red_flag(
    db,
    flag.red_flag_id,
    "High"
)

print("\nUpdated Successfully")

delete_red_flag(
    db,
    flag.red_flag_id
)

print("Deleted Successfully")

db.close()

# -----------------------------
# COMPARISON RESULT CRUD
# -----------------------------

def create_comparison_result(
    db,
    company1_id,
    company2_id,
    comparison_summary
):
    comparison = ComparisonResult(
        company1_id=company1_id,
        company2_id=company2_id,
        comparison_summary=comparison_summary
    )

    db.add(comparison)
    db.commit()
    db.refresh(comparison)

    return comparison


def get_comparison_result(db, comparison_id):
    return db.query(ComparisonResult).filter(
        ComparisonResult.comparison_id == comparison_id
    ).first()


def get_all_comparison_results(db):
    return db.query(ComparisonResult).all()


def update_comparison_result(db, comparison_id, summary):
    comparison = get_comparison_result(db, comparison_id)

    if comparison:
        comparison.comparison_summary = summary
        db.commit()
        db.refresh(comparison)

    return comparison


def delete_comparison_result(db, comparison_id):
    comparison = get_comparison_result(db, comparison_id)

    if comparison:
        db.delete(comparison)
        db.commit()

    return comparison