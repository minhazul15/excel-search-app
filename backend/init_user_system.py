import sqlite3, hashlib

DB = "ORDERMONKEY.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()

# Create users table
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'user',
    approved INTEGER DEFAULT 0
)
""")

# Create activity log table
cur.execute("""
CREATE TABLE IF NOT EXISTS activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    action TEXT,
    record_id INTEGER,
    details TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# Add default admin
admin_user = "admin"
admin_pass = "1234"  # change later
hash_pw = hashlib.sha256(admin_pass.encode()).hexdigest()

cur.execute("INSERT OR IGNORE INTO users (username, password_hash, role, approved) VALUES (?, ?, 'admin', 1)", 
            (admin_user, hash_pw))

conn.commit()
conn.close()
print("✅ User system initialized with default admin (username=admin, password=1234)")
