import os
from flask import Flask
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
from models import db, Route, Service, Vehicle, Stop, TimetableEntry, Driver, User, LiveLocation

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def initialize_db():
    app = create_app()
    with app.app_context():
        print("[...] Initializing PostgreSQL Database...")
        # Create all tables if they don't exist
        db.create_all()

        # Insert sample data ONLY if the tables are empty
        if Route.query.count() == 0:
            print("[...] Inserting sample data...")
            # Routes
            r1 = Route(route_name='Gajuwaka → Beach Road', from_station='Gajuwaka', to_station='Beach Road')
            r2 = Route(route_name='Maddilapalem → Simhachalam', from_station='Maddilapalem', to_station='Simhachalam')
            r3 = Route(route_name='RTC Complex → Railway Station', from_station='RTC Complex', to_station='Railway Station')
            db.session.add_all([r1, r2, r3])
            db.session.commit()

            # Services
            s1 = Service(service_no='28A', route_id=r1.route_id, service_type='Express', ticket_price=30)
            s2 = Service(service_no='6K', route_id=r2.route_id, service_type='Metro', ticket_price=20)
            s3 = Service(service_no='400K', route_id=r3.route_id, service_type='Deluxe', ticket_price=50)
            db.session.add_all([s1, s2, s3])
            db.session.commit()

            # Vehicles
            v1 = Vehicle(vehicle_no='AP31 AB 1234', service_id=s1.service_id, status='Running')
            v2 = Vehicle(vehicle_no='AP31 CD 5678', service_id=s2.service_id, status='Running')
            v3 = Vehicle(vehicle_no='AP31 EF 9012', service_id=s3.service_id, status='Running')
            db.session.add_all([v1, v2, v3])
            db.session.commit()

            # Stops (Route 1)
            st1 = Stop(route_id=r1.route_id, stop_name='Gajuwaka', lat=17.72, lng=83.30, stop_order=1)
            st2 = Stop(route_id=r1.route_id, stop_name='Maddilapalem', lat=17.73, lng=83.31, stop_order=2)
            st3 = Stop(route_id=r1.route_id, stop_name='Beach Road', lat=17.75, lng=83.33, stop_order=3)
            # Stops (Route 3)
            st4 = Stop(route_id=r3.route_id, stop_name='RTC Complex', lat=17.72, lng=83.30, stop_order=1)
            st5 = Stop(route_id=r3.route_id, stop_name='Railway Station', lat=17.73, lng=83.31, stop_order=2)
            db.session.add_all([st1, st2, st3, st4, st5])
            db.session.commit()

            # Timetable
            t1 = TimetableEntry(service_id=s1.service_id, stop_id=st1.stop_id, arrival_time='10:00')
            t2 = TimetableEntry(service_id=s1.service_id, stop_id=st2.stop_id, arrival_time='10:20')
            t3 = TimetableEntry(service_id=s1.service_id, stop_id=st3.stop_id, arrival_time='10:45')
            t4 = TimetableEntry(service_id=s3.service_id, stop_id=st4.stop_id, arrival_time='11:00')
            t5 = TimetableEntry(service_id=s3.service_id, stop_id=st5.stop_id, arrival_time='11:30')
            db.session.add_all([t1, t2, t3, t4, t5])
            db.session.commit()
            print("[OK] Sample data for Routes inserted.")
        else:
            print("[OK] Routes already exist.")

        # Seed Authorized Drivers Independently
        if Driver.query.count() == 0:
            print("[...] Seeding highly secure driver accounts...")
            d1 = Driver(username='driver_28a', password=generate_password_hash('pass28a'))
            d2 = Driver(username='driver_6k', password=generate_password_hash('pass6k'))
            d3 = Driver(username='driver_400k', password=generate_password_hash('pass400k'))
            db.session.add_all([d1, d2, d3])
            db.session.commit()
            print("[OK] Specific drivers seeded successfully!")
        else:
            print("[OK] Drivers already seeded.")

        print("[OK] Full Database Initialization complete!")

def migrate():
    """Safely create tables if they don't exist, without dropping data."""
    app = create_app()
    with app.app_context():
        print("[...] Checking/Migrating PostgreSQL Database...")
        db.create_all()
        print("[OK] Migration complete!")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    initialize_db()
