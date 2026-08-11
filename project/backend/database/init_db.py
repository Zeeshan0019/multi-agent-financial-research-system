"""
Initialize the database schema.
Run this once to create all tables.
"""
from backend.database.database import Base, engine
from backend.database.models import (
    User,
    UserToken,
    Company,
    Document,
    FinancialMetric,
    RedFlag,
    ComparisonResult,
    ResearchQuery,
    Report,
)

Base.metadata.create_all(bind=engine)

print("Database tables created successfully!")
