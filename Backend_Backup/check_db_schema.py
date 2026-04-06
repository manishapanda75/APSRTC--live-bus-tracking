import sqlite3
import os

# Use absolute path relative to this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "apsrtc.db")

# Connect to database
db = sqlite3.connect(DB_NAME)
cur = db.cursor()

# Get schema for live_location table
cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='live_location'")
result = cur.fetchone()

if result:
    print("Current live_location table schema:")
    print(result[0])
    print()
    
    # Check if PRIMARY KEY exists
    if 'PRIMARY KEY' in result[0]:
        print("[OK] PRIMARY KEY is present on bus_id")
    else:
        print("[!] PRIMARY KEY is MISSING - needs migration!")
else:
    print("live_location table does not exist yet")

# Get sample data
cur.execute("SELECT COUNT(*) FROM live_location")
count = cur.fetchone()[0]
print(f"\nTotal records in live_location: {count}")

if count > 0:
    cur.execute("SELECT * FROM live_location LIMIT 3")
    rows = cur.fetchall()
    print("\nSample data:")
    for row in rows:
        print(f"  bus_id={row[0]}, lat={row[1]}, lng={row[2]}, speed={row[3]}, updated_at={row[4]}")

db.close()
