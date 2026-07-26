from backend.database.database import Base, engine
from backend.database.models import (
    ResearchSession,
    Company,
    Document,
    FinancialMetric,
    RedFlag,
    ComparisonResult,
    ResearchQuery,
    Report
    
    
    

)

Base.metadata.create_all(bind=engine)

print("Database created successfully!")
