from backend.database.crud import (
    create_research_session,
    create_company,
    create_document
)

print("Creating Research Session...")
session = create_research_session(
    "Apple Financial Analysis",
    "Annual Report 2024"
)

print("Session ID:", session.session_id)

print("Creating Company...")
company = create_company(
    "Apple Inc.",
    "Technology",
    "2024"
)

print("Company ID:", company.company_id)

print("Creating Document...")
document = create_document(
    session.session_id,
    company.company_id,
    "Apple_Annual_Report.pdf",
    "uploads/apple.pdf"
)

print("Document ID:", document.document_id)

print("\nData inserted successfully!")