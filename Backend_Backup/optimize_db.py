import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "apsrtc.db")

def add_indexes():
    """Add database indexes for frequently queried columns to improve performance"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    print("Adding database indexes for performance optimization...")
    
    # Add indexes for frequently queried columns
    indexes = [
        ("idx_services_service_no", "CREATE INDEX IF NOT EXISTS idx_services_service_no ON services(service_no)"),
        ("idx_vehicles_vehicle_no", "CREATE INDEX IF NOT EXISTS idx_vehicles_vehicle_no ON vehicles(vehicle_no)"),
        ("idx_routes_stations", "CREATE INDEX IF NOT EXISTS idx_routes_stations ON routes(from_station, to_station)"),
        ("idx_live_location_bus_id", "CREATE INDEX IF NOT EXISTS idx_live_location_bus_id ON live_location(bus_id)"),
        ("idx_services_route_id", "CREATE INDEX IF NOT EXISTS idx_services_route_id ON services(route_id)"),
        ("idx_vehicles_service_id", "CREATE INDEX IF NOT EXISTS idx_vehicles_service_id ON vehicles(service_id)"),
    ]
    
    for idx_name, idx_query in indexes:
        try:
            cur.execute(idx_query)
            print(f"  [OK] Created index: {idx_name}")
        except Exception as e:
            print(f"  [WARNING] Error creating {idx_name}: {e}")
    
    conn.commit()
    conn.close()
    print("\n[SUCCESS] Database optimization complete!")

if __name__ == "__main__":
    add_indexes()
