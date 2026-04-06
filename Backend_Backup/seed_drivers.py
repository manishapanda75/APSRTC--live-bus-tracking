import os
from flask import Flask
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
from models import db, Driver

def seed_production_drivers():
    # Force use the Azure URL locally to seed the remote DB
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://dbadmin:Starboy_20@apsrtc-postgres-db.postgres.database.azure.com:5432/postgres?sslmode=require"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        print("Connecting to live database...")
        db.create_all()  # Ensures the Driver table exists in production
        
        print("Checking for existing drivers...")
        if Driver.query.count() == 0:
            print("Seeding production drivers...")
            d1 = Driver(username='driver_28a', password=generate_password_hash('pass28a'))
            d2 = Driver(username='driver_6k', password=generate_password_hash('pass6k'))
            d3 = Driver(username='driver_400k', password=generate_password_hash('pass400k'))
            db.session.add_all([d1, d2, d3])
            db.session.commit()
            print("Successfully seeded drivers into Live Database!")
        else:
            print(f"Drivers already exist (Count: {Driver.query.count()})")

if __name__ == "__main__":
    seed_production_drivers()
