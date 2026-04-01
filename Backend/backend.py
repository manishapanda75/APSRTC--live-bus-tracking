import os
from flask import Flask, jsonify, request, render_template, session, redirect, url_for
from flask_cors import CORS
from flask_caching import Cache
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
import time
import threading
from dotenv import load_dotenv
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy import or_, and_
from sqlalchemy.exc import IntegrityError
from models import db, Route, Service, Vehicle, Stop, TimetableEntry, Driver, User, LiveLocation

load_dotenv()

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
Talisman(app, content_security_policy=None, force_https=False)
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day", "50 per hour"])

cache = Cache(app, config={
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 300
})

app.secret_key = os.getenv("SECRET_KEY", "fallback_dev_key")

from datetime import timedelta
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV', 'development') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Setup Database Connection
# Render provides DATABASE_URL as 'postgres://' but SQLAlchemy needs 'postgresql://'
_db_url = os.getenv('DATABASE_URL', '')
if _db_url.startswith('postgres://'):
    _db_url = _db_url.replace('postgres://', 'postgresql://', 1)

# Fallback to SQLite if no DB url set (for local dev / testing)
if not _db_url:
    _db_url = 'sqlite:///apsrtc_local.db'
    app.config['SQLALCHEMY_DATABASE_URI'] = _db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {}   # SQLite doesn't support pool options
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = _db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 5,
        'pool_recycle': 1800,
        'pool_pre_ping': True,
        'connect_args': {'connect_timeout': 10}
    }

db.init_app(app)

CORS(app)

# Note: We won't auto-initialize db here to avoid context issues during web worker boot.
# Users should run init_db.py manually on deploy

@app.route("/")
def index():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("index.html", username=session.get("username"))

@app.route("/login")
def user_login_page():
    if "user_id" in session:
        return redirect("/")
    return render_template("user_login.html")

@app.route("/api/search")
def search_buses():
    from_station = request.args.get("from", "")
    to_station = request.args.get("to", "")
    service_type = request.args.get("service")

    query = db.session.query(Service, Route, Vehicle).join(Route).join(Vehicle)
    
    # from A -> to B OR from B -> to A
    condition = or_(
        and_(Route.from_station.ilike(f"%{from_station}%"), Route.to_station.ilike(f"%{to_station}%")),
        and_(Route.from_station.ilike(f"%{to_station}%"), Route.to_station.ilike(f"%{from_station}%"))
    )
    query = query.filter(condition)

    if service_type:
        query = query.filter(Service.service_type == service_type)

    results = []
    for s, r, v in query.all():
        results.append({
            "service_no": s.service_no,
            "route_name": r.route_name,
            "service_type": s.service_type,
            "ticket_price": s.ticket_price,
            "vehicle_no": v.vehicle_no
        })

    return jsonify(results)

@app.route("/api/service/<service_no>")
def get_service(service_no):
    res = db.session.query(Service, Route).join(Route).filter(Service.service_no == service_no).first()
    if not res:
        return jsonify({"error": "Service not found"}), 404
    s, r = res
    return jsonify({"service_no": s.service_no, "route": r.route_name})

@app.route("/api/vehicle/<vehicle_no>")
def get_vehicle(vehicle_no):
    res = db.session.query(Vehicle, Service, Route).join(Service).join(Route).filter(Vehicle.vehicle_no == vehicle_no).first()
    if not res:
        return jsonify({"error": "Vehicle not found"}), 404
    v, s, r = res
    return jsonify({
        "vehicle_no": v.vehicle_no,
        "service_no": s.service_no,
        "route": r.route_name,
        "status": v.status
    })

@app.route("/api/timetable")
def timetable():
    from_station = request.args.get("from", "")
    to_station = request.args.get("to", "")

    query = db.session.query(Service.service_no, TimetableEntry.arrival_time).join(TimetableEntry).join(Route).join(Stop)
    
    condition = or_(
        and_(Route.from_station.ilike(f"%{from_station}%"), Route.to_station.ilike(f"%{to_station}%")),
        and_(Route.from_station.ilike(f"%{to_station}%"), Route.to_station.ilike(f"%{from_station}%"))
    )
    query = query.filter(condition)

    results = []
    for service_no, arrival_time in query.all():
        results.append({"service_no": service_no, "arrival_time": arrival_time})

    return jsonify(results)

@app.route("/api/live/<service_no>")
def live_tracking(service_no):
    res = db.session.query(LiveLocation).join(Vehicle).join(Service).filter(Service.service_no == service_no).first()
    if not res:
        return jsonify({"error": "Live data not found"}), 404
    
    return jsonify({
        "lat": res.lat,
        "lng": res.lng,
        "speed": res.speed,
        "updated_at": res.updated_at
    })

@app.route("/api/route_details/<service_no>")
def route_details(service_no):
    stops = db.session.query(Stop).join(Route).join(Service, Service.route_id == Route.route_id).filter(Service.service_no == service_no).order_by(Stop.stop_order.asc()).all()
    if not stops:
        return jsonify({"error": "Route details not found"}), 404
    return jsonify([{"name": st.stop_name, "lat": st.lat, "lng": st.lng} for st in stops])

@app.route("/api/eta/<service_no>")
def calculate_eta(service_no):
    res = db.session.query(LiveLocation.speed).join(Vehicle).join(Service).filter(Service.service_no == service_no).first()
    if not res:
        return jsonify({"error": "ETA data not found"}), 404
    speed = res.speed or 1
    distance = 5
    eta_minutes = int((distance / speed) * 60)
    return jsonify({
        "service_no": service_no,
        "remaining_distance_km": distance,
        "speed_kmph": speed,
        "eta_minutes": eta_minutes
    })

@app.route("/api/admin/add_route", methods=["POST"])
def add_route():
    data = request.json
    r = Route(route_name=data["route_name"], from_station=data["from"], to_station=data["to"])
    db.session.add(r)
    db.session.commit()
    return jsonify({"message": "Route added successfully"})

@app.route("/api/admin/add_service", methods=["POST"])
def add_service():
    data = request.json
    s = Service(service_no=data["service_no"], route_id=data["route_id"], service_type=data["service_type"])
    db.session.add(s)
    db.session.commit()
    return jsonify({"message": "Service added successfully"})

@app.route("/api/admin/add_vehicle", methods=["POST"])
def add_vehicle():
    data = request.json
    v = Vehicle(vehicle_no=data["vehicle_no"], service_id=data["service_id"], status=data["status"])
    db.session.add(v)
    db.session.commit()
    return jsonify({"message": "Vehicle added successfully"})


@app.route("/api/user/register", methods=["POST"])
@limiter.limit("3 per hour")
def user_register():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    hashed_pw = generate_password_hash(password)

    try:
        user = User(username=username, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        return jsonify({"message": "Registration successful! Please login."})
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Username already exists"}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/api/user/login", methods=["POST"])
@limiter.limit("10 per minute")
def user_login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    remember = data.get("remember", False)

    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password, password):
        session.clear()
        session["user_id"] = user.id
        session["username"] = user.username
        session.permanent = True if remember else False
        return jsonify({"message": "Login successful", "redirect": "/"})
    
    return jsonify({"error": "Invalid credentials"}), 401

@app.route("/api/user/logout", methods=["POST"])
def user_logout():
    session.clear()
    return jsonify({"message": "Logged out", "redirect": "/login"})

@app.route("/driver/login")
def driver_login_page():
    if "driver_id" in session:
        return redirect("/driver")
    return render_template("driver_login.html")

@app.route("/api/driver/register", methods=["POST"])
@limiter.limit("3 per hour")
def driver_register():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    hashed_pw = generate_password_hash(password)

    try:
        driver = Driver(username=username, password=hashed_pw)
        db.session.add(driver)
        db.session.commit()
        return jsonify({"message": "Registration successful! Please login."})
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Username already exists"}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/api/driver/login", methods=["POST"])
@limiter.limit("5 per minute")
def driver_login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    driver = Driver.query.filter_by(username=username).first()

    if driver and check_password_hash(driver.password, password):
        session.clear()
        session["driver_id"] = driver.id
        session["username"] = driver.username
        session.permanent = True
        return jsonify({"message": "Login successful", "redirect": "/driver"})
    
    return jsonify({"error": "Invalid credentials"}), 401

@app.route("/api/driver/logout", methods=["POST"])
def driver_logout():
    session.clear()
    return jsonify({"message": "Logged out", "redirect": "/driver/login"})

@app.route("/driver")
def driver_dashboard():
    if "driver_id" not in session:
        return redirect("/driver/login")
    return render_template("driver.html", username=session.get("username"))

DEBUG_LOGS = []

@app.route("/api/debug")
def get_debug_logs():
    return jsonify(DEBUG_LOGS[-20:])

@app.route("/api/update_location", methods=["POST"])
def update_location():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data received"}), 400
            
        service_no = data.get("service_no")
        lat = data.get("lat")
        lng = data.get("lng")
        speed = data.get("speed", 0)
        
        log_entry = f"{time.strftime('%H:%M:%S')}: Received {service_no} at {lat}, {lng}"
        print(log_entry, flush=True)
        DEBUG_LOGS.append(log_entry)

        if not service_no or not lat or not lng:
            return jsonify({"error": "Missing data"}), 400

        v = db.session.query(Vehicle).join(Service).filter(Service.service_no == service_no).first()
        if not v:
            return jsonify({"error": "Service/Vehicle not found"}), 404

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        loc = LiveLocation.query.filter_by(bus_id=v.vehicle_id).first()
        if loc:
            loc.lat = lat
            loc.lng = lng
            loc.speed = speed
            loc.updated_at = timestamp
        else:
            loc = LiveLocation(bus_id=v.vehicle_id, lat=lat, lng=lng, speed=speed, updated_at=timestamp)
            db.session.add(loc)

        db.session.commit()

        log_entry = f"{time.strftime('%H:%M:%S')}: [OK] Updated DB for vehicle {v.vehicle_id}"
        print(log_entry, flush=True)
        DEBUG_LOGS.append(log_entry)

        return jsonify({"message": "Location updated", "time": timestamp, "vehicle_id": v.vehicle_id})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/routes")
@cache.cached(timeout=600)
def get_all_routes():
    routes = Route.query.all()
    return jsonify([{"route_name": r.route_name, "from": r.from_station, "to": r.to_station} for r in routes])

@app.route("/api/stations")
@cache.cached(timeout=600)
def get_all_stations():
    from_stations = db.session.query(Route.from_station).distinct()
    to_stations = db.session.query(Route.to_station).distinct()
    all_stations = set([r[0] for r in from_stations.all()] + [r[0] for r in to_stations.all()])
    return jsonify(list(all_stations))

@app.route("/api/dashboard")
@cache.cached(timeout=60)
def dashboard():
    routes = Route.query.count()
    services = Service.query.count()
    vehicles = Vehicle.query.count()
    running = Vehicle.query.filter_by(status='Running').count()

    return jsonify({
        "total_routes": routes,
        "total_services": services,
        "total_vehicles": vehicles,
        "running_buses": running
    })

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug)