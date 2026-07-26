from backend.database.database import Base, engine
from backend.database.models import ResearchSession, Company

# Create all tables defined in models.py
Base.metadata.create_all(bind=engine)

print("Database created successfully!")