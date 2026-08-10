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

# Create all tables defined in models.py
Base.metadata.create_all(bind=engine)
