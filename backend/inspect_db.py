import sqlite3

DB = "ORDERMONKEY.db"

conn = sqlite3.connect(DB)
cur = conn.cursor()

# List all tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cur.fetchall()
print("Tables:")
for table in tables:
    print("-", table[0])

# For each table, list columns
for table in tables:
    print(f"\nColumns in table '{table[0]}':")
    cur.execute(f"PRAGMA table_info({table[0]});")
    columns = cur.fetchall()
    for col in columns:
        print(f"  {col[1]} ({col[2]})")  # col[1] = column name, col[2] = data type

conn.close()
