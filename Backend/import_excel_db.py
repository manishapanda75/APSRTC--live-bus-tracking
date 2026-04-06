import sqlite3
import pandas as pd
import os

db_path = 'instance/apsrtc_local.db'
if not os.path.exists(db_path):
    print(f"Database {db_path} not found.")
    exit(1)

conn = sqlite3.connect(db_path)
c = conn.cursor()

# Load the excel file
excel_path = r'C:\Users\panda\OneDrive\Documents\GitHub\APSRTC--live-bus-tracking\dataset_bus.xlsx'
df = pd.read_excel(excel_path)

# Drop any rows where required fields are missing
df = df.dropna(subset=['route_id', 'source', 'destination'])
df = df.astype(str)

print(f"Loaded {len(df)} valid rows from excel.")

def get_or_create_route(source, destination):
    route_name = f"{source} → {destination}"
    c.execute("SELECT route_id FROM routes WHERE from_station=? AND to_station=?", (source, destination))
    row = c.fetchone()
    if row:
        return row[0]
    
    c.execute("INSERT INTO routes (route_name, from_station, to_station) VALUES (?, ?, ?)", 
              (route_name, source, destination))
    route_id = c.lastrowid
    
    # Create stops for this new route
    c.execute("INSERT INTO stops (route_id, stop_name, lat, lng, stop_order) VALUES (?, ?, ?, ?, ?)",
              (route_id, source, None, None, 1))
    c.execute("INSERT INTO stops (route_id, stop_name, lat, lng, stop_order) VALUES (?, ?, ?, ?, ?)",
              (route_id, destination, None, None, 2))
    
    return route_id

def get_stop_ids_for_route(route_id):
    c.execute("SELECT stop_id, stop_order FROM stops WHERE route_id=? ORDER BY stop_order", (route_id,))
    rows = c.fetchall()
    return {row[1]: row[0] for row in rows}

inserted_services = 0
for idx, row in df.iterrows():
    s_no = row['route_id'].strip()
    src = row['source'].strip()
    dest = row['destination'].strip()
    b_type = row.get('bus_type', 'Ordinary').strip()
    dep_time = row.get('departure_time', '00:00:00').strip()
    arr_time = row.get('arrival_time', '00:00:00').strip()
    
    r_id = get_or_create_route(src, dest)
    stops_dict = get_stop_ids_for_route(r_id)
    
    if not stops_dict:
        print(f"Error: Stops not found for route {r_id}")
        continue
    
    # Assume minimum stop_order is source, maximum is destination
    src_stop_id = stops_dict[min(stops_dict.keys())]
    dest_stop_id = stops_dict[max(stops_dict.keys())]
    
    # Check if service already exists
    c.execute("SELECT service_id FROM services WHERE service_no=? AND route_id=?", (s_no, r_id))
    s_row = c.fetchone()
    if s_row:
        continue
        
    c.execute("INSERT INTO services (service_no, route_id, service_type, ticket_price) VALUES (?, ?, ?, ?)",
              (s_no, r_id, b_type, 50))
    s_id = c.lastrowid
    
    c.execute("INSERT INTO vehicles (vehicle_no, service_id, status) VALUES (?, ?, ?)", 
              (f"AP_{s_no}", s_id, 'Running'))
    
    dep_str = dep_time.split(' ')[-1] if ' ' in dep_time else dep_time
    arr_str = arr_time.split(' ')[-1] if ' ' in arr_time else arr_time
    
    if len(dep_str.split(':')) > 2:
        dep_str = ':'.join(dep_str.split(':')[:2])
    if len(arr_str.split(':')) > 2:
        arr_str = ':'.join(arr_str.split(':')[:2])
    
    c.execute("INSERT INTO timetable (service_id, stop_id, arrival_time) VALUES (?, ?, ?)", 
              (s_id, src_stop_id, dep_str))
    c.execute("INSERT INTO timetable (service_id, stop_id, arrival_time) VALUES (?, ?, ?)", 
              (s_id, dest_stop_id, arr_str))
              
    inserted_services += 1

conn.commit()
conn.close()

print(f"Successfully inserted {inserted_services} new services into the database.")
