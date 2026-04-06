import os
from flask import Flask
from models import db, Route, Stop
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# The new coordinates provided by the user
ROUTING_DATA = {
    # 1. Maddilapalem -> Simhachalam
    "Maddilapalem → Simhachalam": [
        {"name": "Maddilapalem Bus Station", "lat": 17.7382, "lng": 83.3230},
        {"name": "Satyam Junction", "lat": 17.7420, "lng": 83.3155},
        {"name": "Gurudwara Junction", "lat": 17.7358, "lng": 83.3032},
        {"name": "Akkayyapalem", "lat": 17.7305, "lng": 83.2975},
        {"name": "NAD Junction", "lat": 17.7505, "lng": 83.2590},
        {"name": "Gopalapatnam", "lat": 17.7595, "lng": 83.2505},
        {"name": "Simhachalam Bus Stand", "lat": 17.7785, "lng": 83.2422}
    ],
    # 2. Gajuwaka -> Beach Road
    "Gajuwaka → Beach Road": [
        {"name": "Gajuwaka Main Depot", "lat": 17.6917, "lng": 83.2104},
        {"name": "BHPV Junction", "lat": 17.6950, "lng": 83.2320},
        {"name": "Scindia Junction", "lat": 17.6895, "lng": 83.2750},
        {"name": "Naval Dockyard", "lat": 17.6980, "lng": 83.2950},
        {"name": "Jagadamba Centre", "lat": 17.7125, "lng": 83.3030},
        {"name": "Collectorate", "lat": 17.7110, "lng": 83.3135},
        {"name": "RK Beach Road", "lat": 17.7142, "lng": 83.3236}
    ],
    # 3. RTC Complex -> Railway Station
    "RTC Complex → Railway Station": [
        {"name": "Dwaraka Bus Station (RTC)", "lat": 17.7237, "lng": 83.3072},
        {"name": "Public Library", "lat": 17.7225, "lng": 83.3015},
        {"name": "Allipuram Market", "lat": 17.7210, "lng": 83.2960},
        {"name": "VSKP Railway Station", "lat": 17.7222, "lng": 83.2897}
    ]
}

def update_coordinates():
    with app.app_context():
        print("[...] Starting coordinate migration to Azure PostgreSQL...")
        
        for sequence_name, stops_data in ROUTING_DATA.items():
            # Find the parent route
            route = Route.query.filter_by(route_name=sequence_name).first()
            if not route:
                print(f"[!] Route not found in DB: {sequence_name}")
                continue
                
            print(f"[>] Found Route: {sequence_name} (ID: {route.route_id})")
            
            # Wiping old arbitrary stops for this route
            old_stops = Stop.query.filter_by(route_id=route.route_id).all()
            for old_stop in old_stops:
                db.session.delete(old_stop)
            db.session.commit()
            
            # Inserting the brand new geographical stops
            for i, stop_info in enumerate(stops_data):
                new_stop = Stop(
                    route_id=route.route_id,
                    stop_name=stop_info["name"],
                    lat=stop_info["lat"],
                    lng=stop_info["lng"],
                    stop_order=i + 1
                )
                db.session.add(new_stop)
                
            db.session.commit()
            print(f"    [OK] Inserted {len(stops_data)} accurate stops.")

        print("[OK] Coordinate migration complete!")

if __name__ == "__main__":
    update_coordinates()
