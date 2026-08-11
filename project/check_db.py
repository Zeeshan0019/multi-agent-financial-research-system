import sqlite3
import os

db_path = "backend/database/financial_research.db"

print("Database Path:", os.path.abspath(db_path))

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

tables = cursor.fetchall()

print("\nTables in database:")
for table in tables:
    print(table[0])

conn.close()