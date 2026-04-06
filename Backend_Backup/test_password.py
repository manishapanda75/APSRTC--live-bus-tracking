import sqlite3
from werkzeug.security import check_password_hash

# Connect to database
conn = sqlite3.connect('apsrtc.db')
cur = conn.cursor()

# Get the driver entry
cur.execute('SELECT id, username, password FROM drivers WHERE username = ?', ('ABCD',))
driver = cur.fetchone()

if driver:
    print(f"Found driver: ID={driver[0]}, Username={driver[1]}")
    print(f"Password hash: {driver[2]}")
    
    # Test password verification
    test_password = input("\nEnter the password you're trying to use: ")
    
    if check_password_hash(driver[2], test_password):
        print("✓ Password matches!")
    else:
        print("✗ Password does NOT match!")
        print("\nThis means the password you entered doesn't match the stored hash.")
        print("You need to use the EXACT password that was used during registration.")
else:
    print("Driver 'ABCD' not found in database")

conn.close()
