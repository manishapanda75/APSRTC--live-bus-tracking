import sqlite3

print("Connecting to instance/apsrtc.db via pure sqlite3...")
try:
    conn = sqlite3.connect('instance/apsrtc.db')
    cursor = conn.cursor()

    coords_map = {
        'Gajuwaka': (17.7004, 83.2168),
        'Beach Road': (17.7141, 83.3236),
        'Maddilapalem': (17.7382, 83.3230),
        'Simhachalam': (17.7736, 83.2484),
        'RTC Complex': (17.7237, 83.3072),
        'Railway Station': (17.7222, 83.2897),
        'NAD Junction': (17.7495, 83.2030)
    }

    count = 0
    for stop_name, (lat, lng) in coords_map.items():
        cursor.execute("UPDATE stops SET lat = ?, lng = ? WHERE stop_name = ?", (lat, lng, stop_name))
        count += cursor.rowcount
        if cursor.rowcount > 0:
            print(f"Updated {stop_name} to {lat}, {lng} (affected {cursor.rowcount} rows)")
    
    conn.commit()
    conn.close()
    print(f"Total rows updated in instance: {count}")
except Exception as e:
    print(f"Error: {e}")
