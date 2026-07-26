from backend.database.database import SessionLocal
from backend.database.crud import *

db = SessionLocal()

# Create a document
document = create_document(
    db,
    1,                      # session_id
    1,                      # company_id
    "Annual_Report.pdf",
    "uploads/annual_report.pdf"
)

print("Created Document:", document.document_id)

print("\nAll Documents")
for d in get_all_documents(db):
    print(d.document_id, d.file_name)

update_document(
    db,
    document.document_id,
    "Updated_Report.pdf"
)

print("\nUpdated Successfully")

delete_document(
    db,
    document.document_id
)

print("Deleted Successfully")

db.close()