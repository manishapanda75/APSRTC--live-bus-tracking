import os
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

def parse_duration_to_minutes(duration_str):
    """Convert duration strings like '1h 30m', '45m' to integer minutes."""
    if pd.isna(duration_str):
        return 0
    d_str = str(duration_str).lower().strip()
    minutes = 0
    if 'h' in d_str:
        parts = d_str.split('h')
        minutes += int(parts[0].strip() or 0) * 60
        if 'm' in parts[1]:
            minutes += int(parts[1].replace('m', '').strip() or 0)
    elif 'm' in d_str:
        minutes += int(d_str.replace('m', '').strip() or 0)
    else:
        try:
            minutes = int(d_str)
        except ValueError:
            minutes = 0
    return minutes

def import_data():
    # 6. Use DATABASE_URL from .env file
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("Error: DATABASE_URL not found in .env file.")
        return

    print("Connecting to PostgreSQL Database...")
    try:
        conn = psycopg2.connect(database_url)
        c = conn.cursor(cursor_factory=RealDictCursor)
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        return

    excel_path = 'dataset_bus.xlsx'
    if not os.path.exists(excel_path):
         print(f"Error: {excel_path} not found in the current directory.")
         return

    print(f"Loading data from {excel_path}...")
    df = pd.read_excel(excel_path)
    df = df.dropna(subset=['route_id', 'source', 'destination'])

    # Track counts for final summary
    counts = {
        'routes_created': 0,
        'services_created': 0,
        'vehicles_created': 0,
        'duplicates_skipped': 0
    }

    try:
        for idx, row in df.iterrows():
            service_no = str(row['route_id']).strip()
            source = str(row['source']).strip()
            destination = str(row['destination']).strip()
            bus_type = str(row.get('bus_type', 'Ordinary')).strip()
            duration_str = row.get('duration', '0m')
            
            # --- 1. Create unique Route for each (source, destination) pair ---
            route_name = f"{source} → {destination}"
            c.execute("SELECT route_id FROM routes WHERE from_station = %s AND to_station = %s", (source, destination))
            route_row = c.fetchone()
            
            if route_row:
                route_pk = route_row['route_id']
            else:
                c.execute(
                    "INSERT INTO routes (route_name, from_station, to_station) VALUES (%s, %s, %s) RETURNING route_id", 
                    (route_name, source, destination)
                )
                route_pk = c.fetchone()['route_id']
                counts['routes_created'] += 1
                print(f"[{idx+1}/{len(df)}] ✅ Created new Route: {route_name} (ID: {route_pk})")

            # --- 2. Create Service using route_id as service_no & 3. Calculate ticket_price ---
            # Don't create duplicates (check if exists first)
            c.execute("SELECT service_id FROM services WHERE service_no = %s", (service_no,))
            service_row = c.fetchone()
            
            if service_row:
                service_pk = service_row['service_id']
                counts['duplicates_skipped'] += 1
                print(f"[{idx+1}/{len(df)}] ⏭️  Skipped Service duplicate: {service_no}")
            else:
                # 3. Calculate ticket_price = max(20, min(150, duration_minutes * 1.5))
                duration_mins = parse_duration_to_minutes(duration_str)
                ticket_price = max(20, min(150, int(duration_mins * 1.5)))

                c.execute(
                    "INSERT INTO services (service_no, route_id, service_type, ticket_price) VALUES (%s, %s, %s, %s) RETURNING service_id",
                    (service_no, route_pk, bus_type, ticket_price)
                )
                service_pk = c.fetchone()['service_id']
                counts['services_created'] += 1
                print(f"[{idx+1}/{len(df)}] ✅ Created Service: {service_no} (Price: ₹{ticket_price})")

            # --- 4. Create Vehicle = f"AP31 {service_no}" with status "Running" ---
            vehicle_no = f"AP31 {service_no}"
            c.execute("SELECT vehicle_id FROM vehicles WHERE vehicle_no = %s", (vehicle_no,))
            vehicle_row = c.fetchone()
            
            if vehicle_row:
                pass # Already counted in duplicates_skipped since it's 1:1 with service
            else:
                c.execute(
                    "INSERT INTO vehicles (vehicle_no, service_id, status) VALUES (%s, %s, %s) RETURNING vehicle_id",
                    (vehicle_no, service_pk, "Running")
                )
                counts['vehicles_created'] += 1
                print(f"[{idx+1}/{len(df)}] ✅ Created Vehicle: {vehicle_no}")

        # Commit all changes
        conn.commit()
        print("\nAll database changes committed successfully.")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ An error occurred, rolling back changes: {e}")
    finally:
        c.close()
        conn.close()

    # --- 8. Show final summary with counts ---
    print("\n" + "="*40)
    print("🎯 IMPORT SUMMARY")
    print("="*40)
    print(f"Total rows processed   : {len(df)}")
    print(f"Routes created         : {counts['routes_created']}")
    print(f"Services created       : {counts['services_created']}")
    print(f"Vehicles created       : {counts['vehicles_created']}")
    print(f"Duplicates skipped     : {counts['duplicates_skipped']}")
    print("="*40)

if __name__ == "__main__":
    import_data()
