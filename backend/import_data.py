import pandas as pd
import sqlite3

# Load CSV
df = pd.read_csv("ORDERMONKEY.csv")  # Make sure the CSV is in the same folder

# Create a database and insert the data
conn = sqlite3.connect("ORDERMONKEY.db")  # Creates SQLite database
df.to_sql("restaurants", conn, if_exists="replace", index=False)
conn.close()

print("Data successfully moved from CSV to SQLite database.")
