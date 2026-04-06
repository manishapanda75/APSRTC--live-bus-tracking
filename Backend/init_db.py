import os
from flask import Flask
from werkzeug.security import generate_password_hash
from models import db, Route, Service, Vehicle, Stop, TimetableEntry, Driver, User, LiveLocation

def create_app():
    app = Flask(__name__)
    _db_url = os.getenv('DATABASE_URL', '')
    if _db_url.startswith('postgres://'):
        _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
    if not _db_url:
        _db_url = 'sqlite:///apsrtc_local.db'
    app.config['SQLALCHEMY_DATABASE_URI'] = _db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def initialize_db():
    app = create_app()
    with app.app_context():
        print("[...] Initializing Database...")
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

            # Stops (Route 1: Gajuwaka → Beach Road)
            st1 = Stop(route_id=r1.route_id, stop_name='Gajuwaka', lat=17.72, lng=83.30, stop_order=1)
            st2 = Stop(route_id=r1.route_id, stop_name='Maddilapalem', lat=17.73, lng=83.31, stop_order=2)
            st3 = Stop(route_id=r1.route_id, stop_name='Beach Road', lat=17.75, lng=83.33, stop_order=3)
            # Stops (Route 2: Maddilapalem → Simhachalam)
            st6 = Stop(route_id=r2.route_id, stop_name='Maddilapalem', lat=17.73, lng=83.31, stop_order=1)
            st7 = Stop(route_id=r2.route_id, stop_name='NAD Junction', lat=17.74, lng=83.28, stop_order=2)
            st8 = Stop(route_id=r2.route_id, stop_name='Simhachalam', lat=17.77, lng=83.25, stop_order=3)
            # Stops (Route 3: RTC Complex → Railway Station)
            st4 = Stop(route_id=r3.route_id, stop_name='RTC Complex', lat=17.72, lng=83.30, stop_order=1)
            st5 = Stop(route_id=r3.route_id, stop_name='Railway Station', lat=17.73, lng=83.31, stop_order=2)
            db.session.add_all([st1, st2, st3, st4, st5, st6, st7, st8])
            db.session.commit()

            # Timetable
            t1 = TimetableEntry(service_id=s1.service_id, stop_id=st1.stop_id, arrival_time='10:00')
            t2 = TimetableEntry(service_id=s1.service_id, stop_id=st2.stop_id, arrival_time='10:20')
            t3 = TimetableEntry(service_id=s1.service_id, stop_id=st3.stop_id, arrival_time='10:45')
            t4 = TimetableEntry(service_id=s3.service_id, stop_id=st4.stop_id, arrival_time='11:00')
            t5 = TimetableEntry(service_id=s3.service_id, stop_id=st5.stop_id, arrival_time='11:30')
            db.session.add_all([t1, t2, t3, t4, t5])
            db.session.commit()

            print("[OK] Database created and seeded successfully!")
        else:
            print("[OK] Database tables already seeded.")

        # ── Create default admin user if none exists ──
        admin_exists = User.query.filter_by(is_admin=True).first()
        if not admin_exists:
            print("[...] Creating default admin user...")
            admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
            admin = User(
                username='admin',
                password=generate_password_hash(admin_password),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print(f"[OK] Admin user created! Username: admin, Password: {admin_password}")
            print("[!] IMPORTANT: Change the admin password immediately via the admin panel or env var ADMIN_PASSWORD")
        else:
            print("[OK] Admin user already exists.")

        # ── Seed Authorized Drivers Independently ──
        if Driver.query.count() == 0:
            print("[...] Seeding highly secure driver accounts...")
            d1 = Driver(username='driver_28a', password=generate_password_hash('pass28a'))
            d2 = Driver(username='driver_6k', password=generate_password_hash('pass6k'))
            d3 = Driver(username='driver_400k', password=generate_password_hash('pass400k'))
            db.session.add_all([d1, d2, d3])
            db.session.commit()
            print("[OK] Authorized Drivers securely seeded.")
        else:
            print("[OK] Drivers already seeded.")

def migrate():
    """Safely create tables if they don't exist, without dropping data."""
    app = create_app()
    with app.app_context():
        print("[...] Checking/Migrating Database...")
        db.create_all()
        
        # Add new columns if they don't exist (safe migration)
        try:
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            
            # Check if 'is_admin' column exists in users table
            user_columns = [col['name'] for col in inspector.get_columns('users')]
            if 'is_admin' not in user_columns:
                print("[...] Adding 'is_admin' column to users table...")
                db.engine.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE")
                print("[OK] 'is_admin' column added.")
            
            # Check if 'assigned_service_id' column exists in drivers table
            driver_columns = [col['name'] for col in inspector.get_columns('drivers')]
            if 'assigned_service_id' not in driver_columns:
                print("[...] Adding 'assigned_service_id' column to drivers table...")
                db.engine.execute("ALTER TABLE drivers ADD COLUMN assigned_service_id INTEGER REFERENCES services(service_id)")
                print("[OK] 'assigned_service_id' column added.")

        except Exception as e:
            print(f"[WARN] Migration check error (may be normal for new DB): {e}")
        
        print("[OK] Migration complete!")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    initialize_db()
