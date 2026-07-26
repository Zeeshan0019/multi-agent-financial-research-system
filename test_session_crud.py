from backend.database.crud import *

print("All Sessions:")
print(get_all_research_sessions())

session = get_research_session(1)

if session:
    print("Session Found:", session.session_name)

update_research_session(1, "Updated Financial Research")

print("Updated Successfully")