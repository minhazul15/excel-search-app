import sqlite3
import shutil

# === CONFIGURATION ===
db_path = "ORDERMONKEY.db"
backup_path = "ORDERMONKEY_backup_before_alter.db"

# === 1. Make a Backup ===
shutil.copy(db_path, backup_path)
print(f"✅ Backup created at: {backup_path}")

# === 2. Connect to Database ===
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# === 3. Rename old table ===
cur.execute("ALTER TABLE restaurants RENAME TO restaurants_old;")

# === 4. Create new table with id as Primary Key ===
cur.execute("""
CREATE TABLE restaurants (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  "Location Name" TEXT,
  "BackOffice Email" TEXT,
  "APP" TEXT,
  "Status" TEXT,
  "KIOSK" TEXT,
  "Restaurent ID" TEXT,
  "Kiosk Build No" TEXT,
  "No of Terminal" REAL,
  "Payment Provider" TEXT,
  "NUC " TEXT,
  "Product Module" TEXT,
  "Terminal ID" TEXT,
  "Payment Service Version" TEXT,
  "Intregation" TEXT,
  "Org ID" TEXT,
  "Branch UUID" TEXT,
  "No of Printer" REAL,
  "Polling Enabled" TEXT,
  "Scanner" TEXT,
  "KIOSK PIN" REAL,
  "AnyDesk ID" TEXT,
  "AnyDesk Password" TEXT,
  "Deliverect" TEXT,
  "LightSpeed" TEXT,
  "Contacts of Client" TEXT,
  "TEAMVIEWER ID" REAL
);
""")

# === 5. Copy data back ===
cur.execute("""
INSERT INTO restaurants (
  "Location Name", "BackOffice Email", "APP", "Status", "KIOSK", "Restaurent ID",
  "Kiosk Build No", "No of Terminal", "Payment Provider", "NUC ", "Product Module",
  "Terminal ID", "Payment Service Version", "Intregation", "Org ID", "Branch UUID",
  "No of Printer", "Polling Enabled", "Scanner", "KIOSK PIN", "AnyDesk ID",
  "AnyDesk Password", "Deliverect", "LightSpeed", "Contacts of Client", "TEAMVIEWER ID"
)
SELECT
  "Location Name", "BackOffice Email", "APP", "Status", "KIOSK", "Restaurent ID",
  "Kiosk Build No", "No of Terminal", "Payment Provider", "NUC ", "Product Module",
  "Terminal ID", "Payment Service Version", "Intregation", "Org ID", "Branch UUID",
  "No of Printer", "Polling Enabled", "Scanner", "KIOSK PIN", "AnyDesk ID",
  "AnyDesk Password", "Deliverect", "LightSpeed", "Contacts of Client", "TEAMVIEWER ID"
FROM restaurants_old;
""")

# === 6. Drop the old table ===
cur.execute("DROP TABLE restaurants_old;")

conn.commit()
conn.close()

print("✅ Database successfully updated with `id` as PRIMARY KEY.")
