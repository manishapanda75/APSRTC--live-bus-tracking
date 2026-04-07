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
        _db_url = 'sqlite:///apsrtc.db'
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
            # ── 1. Routes ──
            r1 = Route(route_name='Anakapalle → Steel Plant', from_station='Anakapalle Bus Stop', to_station='Steel Plant Bus Stop')
            r2 = Route(route_name='NAD Junction → Pendurthi', from_station='NAD Junction Bus Stop', to_station='Pendurthi Bus Stop')
            r3 = Route(route_name='Rushikonda → Bheemili', from_station='Rushikonda Bus Stop', to_station='Bheemili Bus Stop')
            db.session.add_all([r1, r2, r3])
            db.session.commit()

            # ── 2. Services ──
            s1 = Service(service_no='28A', route_id=r1.route_id, service_type='Express', ticket_price=40)
            s2 = Service(service_no='6K', route_id=r2.route_id, service_type='Metro', ticket_price=25)
            s3 = Service(service_no='400K', route_id=r3.route_id, service_type='Deluxe', ticket_price=50)
            db.session.add_all([s1, s2, s3])
            db.session.commit()

            # ── 3. Vehicles ──
            v1 = Vehicle(vehicle_no='AP31 AB 1111', service_id=s1.service_id, status='Running')
            v2 = Vehicle(vehicle_no='AP31 CD 2222', service_id=s2.service_id, status='Running')
            v3 = Vehicle(vehicle_no='AP31 EF 3333', service_id=s3.service_id, status='Running')
            db.session.add_all([v1, v2, v3])
            db.session.commit()

            # ── 4. Stops ──
            # Route 1: Anakapalle → Steel Plant
            st1 = Stop(route_id=r1.route_id, stop_name='Anakapalle Bus Stop', lat=17.6868, lng=83.0032, stop_order=1)
            st2 = Stop(route_id=r1.route_id, stop_name='Kurmannapalem Bus Stop', lat=17.6862, lng=83.1655, stop_order=2)
            st3 = Stop(route_id=r1.route_id, stop_name='Gajuwaka Bus Stop', lat=17.7006, lng=83.2136, stop_order=3)
            st4 = Stop(route_id=r1.route_id, stop_name='Steel Plant Bus Stop', lat=17.6396, lng=83.1626, stop_order=4)

            # Route 2: NAD Junction → Pendurthi
            st5 = Stop(route_id=r2.route_id, stop_name='NAD Junction Bus Stop', lat=17.7415, lng=83.2303, stop_order=1)
            st6 = Stop(route_id=r2.route_id, stop_name='Simhachalam Bus Stop', lat=17.7669, lng=83.2456, stop_order=2)
            st7 = Stop(route_id=r2.route_id, stop_name='Pendurthi Bus Stop', lat=17.7897, lng=83.1296, stop_order=3)

            # Route 3: Rushikonda → Bheemili
            st8 = Stop(route_id=r3.route_id, stop_name='Rushikonda Bus Stop', lat=17.7820, lng=83.3850, stop_order=1)
            st9 = Stop(route_id=r3.route_id, stop_name='Bheemili Bus Stop', lat=17.8903, lng=83.4527, stop_order=2)
            
            db.session.add_all([st1, st2, st3, st4, st5, st6, st7, st8, st9])
            db.session.commit()

            # ── 5. Timetable ──
            t1 = TimetableEntry(service_id=s1.service_id, stop_id=st1.stop_id, arrival_time='08:00')
            t2 = TimetableEntry(service_id=s1.service_id, stop_id=st4.stop_id, arrival_time='09:00')
            t3 = TimetableEntry(service_id=s2.service_id, stop_id=st5.stop_id, arrival_time='08:30')
            t4 = TimetableEntry(service_id=s3.service_id, stop_id=st8.stop_id, arrival_time='10:00')
            db.session.add_all([t1, t2, t3, t4])
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
