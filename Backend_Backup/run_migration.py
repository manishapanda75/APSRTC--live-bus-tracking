"""
Run database migration to fix live_location table schema
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run migration
import init_db

print("Running migration...")
init_db.migrate()
print("\nMigration complete! Checking schema...")

# Verify the changes
import sqlite3
db = sqlite3.connect(init_db.DB_NAME)
cur = db.cursor()

cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='live_location'")
result = cur.fetchone()

if result:
    print("\nUpdated live_location table schema:")
    print(result[0])
    print()
    
    if 'PRIMARY KEY' in result[0]:
        print("[OK] PRIMARY KEY successfully added!")
    else:
        print("[ERROR] PRIMARY KEY still missing!")

db.close()
