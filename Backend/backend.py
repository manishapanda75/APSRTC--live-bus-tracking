import os
import math
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
_db_url = os.getenv('DATABASE_URL', '')
if _db_url.startswith('postgres://'):
    _db_url = _db_url.replace('postgres://', 'postgresql://', 1)

if not _db_url:
    _db_url = 'sqlite:///apsrtc.db'

app.config['SQLALCHEMY_DATABASE_URI'] = _db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

if _db_url.startswith('sqlite'):
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {}
else:
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 5,
        'pool_recycle': 1800,
        'pool_pre_ping': True,
        'connect_args': {'connect_timeout': 10}
    }

db.init_app(app)

with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        print(f"Database Initialization Error: {e}", flush=True)

CORS(app)

# ─── Haversine Distance Helper ─────────────────────────
def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance in km between two lat/lng points."""
    R = 6371.0
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


@app.route("/api/admin/force_seed")
def force_seed():
    from werkzeug.security import generate_password_hash
    import init_db
    
    # 1. Force extreme DB drop and initialization to fix SQLite corruption
    db.drop_all()
    init_db.initialize_db()

    # 2. Flush any hanging drivers and forcibly insert our 3 specific ones
    db.session.query(Driver).delete()
    db.session.commit()
    
    d1 = Driver(username='driver_28a', password=generate_password_hash('pass28a'))
    d2 = Driver(username='driver_6k', password=generate_password_hash('pass6k'))
    d3 = Driver(username='driver_400k', password=generate_password_hash('pass400k'))
    db.session.add_all([d1, d2, d3])
    db.session.commit()
    return "Database forcefully completely wiped, re-initialized and powerfully re-seeded with exactly 3 Drivers!"

# ─── Admin Auth Helpers ─────────────────────────────────
def is_admin():
    """Check if the current session belongs to an admin user."""
    if "user_id" not in session or not session.get("is_admin"):
        return False
    return True

def admin_required(f):
    """Decorator to protect admin-only endpoints."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_admin():
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated


# ═══════════════════════════════════════════════════════
# PAGE ROUTES
# ═══════════════════════════════════════════════════════

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

@app.route("/admin")
def admin_panel():
    if not is_admin():
        return redirect("/login")
    return render_template("admin.html", username=session.get("username"))

@app.route("/driver/login")
def driver_login_page():
    if "driver_id" in session:
        return redirect("/driver")
    return render_template("driver_login.html")

@app.route("/driver")
def driver_dashboard():
    if "driver_id" not in session:
        return redirect("/driver/login")
    return render_template("driver.html", username=session.get("username"))


# ═══════════════════════════════════════════════════════
# PWA — Service Worker & Manifest
# ═══════════════════════════════════════════════════════

@app.route("/manifest.json")
def serve_manifest():
    return app.send_static_file('manifest.json')

@app.route("/service-worker.js")
def serve_sw():
    response = app.send_static_file('service-worker.js')
    response.headers['Content-Type'] = 'application/javascript'
    response.headers['Service-Worker-Allowed'] = '/'
    return response

@app.route("/offline")
def offline_page():
    return render_template("offline.html")


# ═══════════════════════════════════════════════════════
# PUBLIC APIs
# ═══════════════════════════════════════════════════════

@app.route("/api/search")
def search_buses():
    from_station = request.args.get("from", "")
    to_station = request.args.get("to", "")
    service_type = request.args.get("service")

    query = db.session.query(Service, Route, Vehicle).join(Route).join(Vehicle)
    
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

    query = db.session.query(Service.service_no, TimetableEntry.arrival_time).join(TimetableEntry).join(Route).join(Stop, TimetableEntry.stop_id == Stop.stop_id)
    
    condition = or_(
        and_(Route.from_station.ilike(f"%{from_station}%"), Route.to_station.ilike(f"%{to_station}%")),
        and_(Route.from_station.ilike(f"%{to_station}%"), Route.to_station.ilike(f"%{from_station}%"))
    )
    query = query.filter(condition)
    query = query.filter(Stop.stop_name.ilike(f"%{from_station}%"))
    query = query.order_by(TimetableEntry.arrival_time.asc())

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
    return jsonify([{"name": st.stop_name, "lat": st.lat, "lng": st.lng, "stop_order": st.stop_order} for st in stops])


# ─── Real ETA Calculation ──────────────────────────────
@app.route("/api/eta/<service_no>")
def calculate_eta(service_no):
    """
    Calculate real ETA based on bus position, route stops, and current speed.
    Optional query param: ?destination=StopName to get ETA to a specific stop.
    """
    # Get live location
    live = db.session.query(LiveLocation).join(Vehicle).join(Service).filter(Service.service_no == service_no).first()
    if not live:
        return jsonify({"error": "ETA data not found — bus not broadcasting"}), 404

    bus_lat, bus_lng = live.lat, live.lng
    speed = live.speed or 1  # Avoid division by zero

    # Get route stops in order
    stops = db.session.query(Stop).join(Route).join(Service, Service.route_id == Route.route_id)\
        .filter(Service.service_no == service_no).order_by(Stop.stop_order.asc()).all()

    if not stops:
        return jsonify({"error": "Route stops not found"}), 404

    destination_name = request.args.get("destination", "").strip()

    # Find the closest stop to the bus (current position on route)
    min_dist = float('inf')
    closest_idx = 0
    for i, st in enumerate(stops):
        d = haversine(bus_lat, bus_lng, st.lat, st.lng)
        if d < min_dist:
            min_dist = d
            closest_idx = i

    # Determine destination stop index
    dest_idx = len(stops) - 1  # Default: last stop (terminal)
    if destination_name:
        for i, st in enumerate(stops):
            if st.stop_name.lower() == destination_name.lower():
                dest_idx = i
                break

    # Calculate remaining distance along route from bus to destination
    remaining_distance = 0.0
    stops_remaining = 0

    if closest_idx < dest_idx:
        # Bus is before destination — normal forward travel
        # Distance from bus to the nearest stop ahead
        remaining_distance += haversine(bus_lat, bus_lng, stops[closest_idx].lat, stops[closest_idx].lng)
        # Then sum stop-to-stop distances
        for i in range(closest_idx, dest_idx):
            remaining_distance += haversine(stops[i].lat, stops[i].lng, stops[i+1].lat, stops[i+1].lng)
        stops_remaining = dest_idx - closest_idx
    elif closest_idx == dest_idx:
        # Bus is at/near the destination stop
        remaining_distance = haversine(bus_lat, bus_lng, stops[dest_idx].lat, stops[dest_idx].lng)
        stops_remaining = 0
    else:
        # Bus has passed the destination (reverse direction route?)
        remaining_distance = haversine(bus_lat, bus_lng, stops[dest_idx].lat, stops[dest_idx].lng)
        stops_remaining = 0

    # Calculate ETA in minutes
    eta_minutes = int((remaining_distance / max(speed, 1)) * 60)

    # Calculate stop status
    dist_to_closest = haversine(bus_lat, bus_lng, stops[closest_idx].lat, stops[closest_idx].lng)
    bus_status = "En Route"
    if dist_to_closest < 0.3:
        bus_status = "At Station"
    elif dist_to_closest < 1.0:
        bus_status = "Approaching"

    return jsonify({
        "service_no": service_no,
        "remaining_distance_km": round(remaining_distance, 2),
        "speed_kmph": speed,
        "eta_minutes": eta_minutes,
        "stops_remaining": stops_remaining,
        "destination": stops[dest_idx].stop_name,
        "closest_stop": stops[closest_idx].stop_name,
        "bus_status": bus_status,
        "bus_lat": bus_lat,
        "bus_lng": bus_lng
    })


# ═══════════════════════════════════════════════════════
# USER AUTH
# ═══════════════════════════════════════════════════════

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
        user = User(username=username, password=hashed_pw, is_admin=False)
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

    try:
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session.clear()
            session["user_id"] = user.id
            session["username"] = user.username
            session["is_admin"] = user.is_admin
            session.permanent = True if remember else False

            redirect_url = "/admin" if user.is_admin else "/"
            return jsonify({"message": "Login successful", "redirect": redirect_url, "is_admin": user.is_admin})
        
        return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Database Server Error: {str(e)}"}), 500

@app.route("/api/user/logout", methods=["POST"])
def user_logout():
    session.clear()
    return jsonify({"message": "Logged out", "redirect": "/login"})


# ═══════════════════════════════════════════════════════
# DRIVER AUTH (with service linking)
# ═══════════════════════════════════════════════════════

@app.route("/api/driver/login", methods=["POST"])
@limiter.limit("5 per minute")
def driver_login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    try:
        driver = Driver.query.filter_by(username=username).first()

        if driver and check_password_hash(driver.password, password):
            session.clear()
            session["driver_id"] = driver.id
            session["username"] = driver.username
            session.permanent = True

            # Include assigned service info
            assigned_service = None
            if driver.assigned_service_id:
                svc = Service.query.get(driver.assigned_service_id)
                if svc:
                    assigned_service = {
                        "service_id": svc.service_id,
                        "service_no": svc.service_no,
                        "route": svc.route.route_name if svc.route else ""
                    }
            
            session["assigned_service_no"] = assigned_service["service_no"] if assigned_service else None

            return jsonify({
                "message": "Login successful",
                "redirect": "/driver",
                "assigned_service": assigned_service
            })
        
        return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Database Server Error: {str(e)}"}), 500

@app.route("/api/driver/logout", methods=["POST"])
def driver_logout():
    session.clear()
    return jsonify({"message": "Logged out", "redirect": "/driver/login"})

@app.route("/api/driver/info")
def driver_info():
    """Get current driver's info including assigned service."""
    if "driver_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    driver = Driver.query.get(session["driver_id"])
    if not driver:
        return jsonify({"error": "Driver not found"}), 404

    assigned_service = None
    if driver.assigned_service_id:
        svc = Service.query.get(driver.assigned_service_id)
        if svc:
            assigned_service = {
                "service_id": svc.service_id,
                "service_no": svc.service_no,
                "route": svc.route.route_name if svc.route else ""
            }

    return jsonify({
        "driver_id": driver.id,
        "username": driver.username,
        "assigned_service": assigned_service
    })


# ═══════════════════════════════════════════════════════
# LOCATION UPDATE (with driver-service enforcement + WebSocket broadcast)
# ═══════════════════════════════════════════════════════

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

        # ── Driver-Service Linking Enforcement ──
        if "driver_id" in session:
            driver = Driver.query.get(session["driver_id"])
            if driver and driver.assigned_service_id:
                assigned_svc = Service.query.get(driver.assigned_service_id)
                if assigned_svc and assigned_svc.service_no != service_no:
                    return jsonify({"error": f"You are assigned to service {assigned_svc.service_no}, not {service_no}"}), 403

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


# ═══════════════════════════════════════════════════════
# PUBLIC DATA APIs (cached)
# ═══════════════════════════════════════════════════════

@app.route("/api/routes")
@cache.cached(timeout=600)
def get_all_routes():
    routes = Route.query.all()
    return jsonify([{"route_id": r.route_id, "route_name": r.route_name, "from": r.from_station, "to": r.to_station} for r in routes])

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
    drivers = Driver.query.count()

    return jsonify({
        "total_routes": routes,
        "total_services": services,
        "total_vehicles": vehicles,
        "running_buses": running,
        "total_drivers": drivers
    })


# ═══════════════════════════════════════════════════════
# ADMIN APIs (all protected by @admin_required)
# ═══════════════════════════════════════════════════════

# ── List All ──
@app.route("/api/admin/routes")
@admin_required
def admin_list_routes():
    routes = Route.query.all()
    return jsonify([{"route_id": r.route_id, "route_name": r.route_name, "from": r.from_station, "to": r.to_station} for r in routes])

@app.route("/api/admin/services")
@admin_required
def admin_list_services():
    services = db.session.query(Service, Route).join(Route).all()
    return jsonify([{
        "service_id": s.service_id,
        "service_no": s.service_no,
        "route_id": s.route_id,
        "route_name": r.route_name,
        "service_type": s.service_type,
        "ticket_price": s.ticket_price
    } for s, r in services])

@app.route("/api/admin/vehicles")
@admin_required
def admin_list_vehicles():
    vehicles = db.session.query(Vehicle, Service).join(Service).all()
    return jsonify([{
        "vehicle_id": v.vehicle_id,
        "vehicle_no": v.vehicle_no,
        "service_id": v.service_id,
        "service_no": s.service_no,
        "status": v.status
    } for v, s in vehicles])

@app.route("/api/admin/stops")
@admin_required
def admin_list_stops():
    stops = db.session.query(Stop, Route).join(Route).order_by(Stop.route_id, Stop.stop_order).all()
    return jsonify([{
        "stop_id": st.stop_id,
        "route_id": st.route_id,
        "route_name": r.route_name,
        "stop_name": st.stop_name,
        "lat": st.lat,
        "lng": st.lng,
        "stop_order": st.stop_order
    } for st, r in stops])

@app.route("/api/admin/drivers")
@admin_required
def admin_list_drivers():
    drivers = Driver.query.all()
    result = []
    for d in drivers:
        svc_info = None
        if d.assigned_service_id:
            svc = Service.query.get(d.assigned_service_id)
            if svc:
                svc_info = {"service_id": svc.service_id, "service_no": svc.service_no}
        result.append({
            "id": d.id,
            "username": d.username,
            "assigned_service": svc_info
        })
    return jsonify(result)

# ── Create ──
@app.route("/api/admin/add_route", methods=["POST"])
@admin_required
def add_route():
    data = request.json
    r = Route(route_name=data["route_name"], from_station=data["from"], to_station=data["to"])
    db.session.add(r)
    db.session.commit()
    cache.clear()
    return jsonify({"message": "Route added successfully", "route_id": r.route_id})

@app.route("/api/admin/add_service", methods=["POST"])
@admin_required
def add_service():
    data = request.json
    s = Service(
        service_no=data["service_no"],
        route_id=data["route_id"],
        service_type=data.get("service_type", "Express"),
        ticket_price=data.get("ticket_price", 0)
    )
    db.session.add(s)
    db.session.commit()
    cache.clear()
    return jsonify({"message": "Service added successfully", "service_id": s.service_id})

@app.route("/api/admin/add_vehicle", methods=["POST"])
@admin_required
def add_vehicle():
    data = request.json
    v = Vehicle(vehicle_no=data["vehicle_no"], service_id=data["service_id"], status=data.get("status", "Running"))
    db.session.add(v)
    db.session.commit()
    cache.clear()
    return jsonify({"message": "Vehicle added successfully", "vehicle_id": v.vehicle_id})

@app.route("/api/admin/add_stop", methods=["POST"])
@admin_required
def add_stop():
    data = request.json
    st = Stop(
        route_id=data["route_id"],
        stop_name=data["stop_name"],
        lat=data.get("lat", 0.0),
        lng=data.get("lng", 0.0),
        stop_order=data.get("stop_order", 1)
    )
    db.session.add(st)
    db.session.commit()
    cache.clear()
    return jsonify({"message": "Stop added successfully", "stop_id": st.stop_id})

@app.route("/api/admin/assign_driver", methods=["POST"])
@admin_required
def assign_driver():
    data = request.json
    driver_id = data.get("driver_id")
    service_id = data.get("service_id")  # Can be None to unassign

    driver = Driver.query.get(driver_id)
    if not driver:
        return jsonify({"error": "Driver not found"}), 404

    if service_id:
        svc = Service.query.get(service_id)
        if not svc:
            return jsonify({"error": "Service not found"}), 404
        driver.assigned_service_id = service_id
    else:
        driver.assigned_service_id = None

    db.session.commit()
    return jsonify({"message": "Driver assignment updated"})

# ── Delete ──
@app.route("/api/admin/delete_route/<int:route_id>", methods=["DELETE"])
@admin_required
def delete_route(route_id):
    r = Route.query.get(route_id)
    if not r:
        return jsonify({"error": "Route not found"}), 404
    db.session.delete(r)
    db.session.commit()
    cache.clear()
    return jsonify({"message": "Route deleted"})

@app.route("/api/admin/delete_service/<int:service_id>", methods=["DELETE"])
@admin_required
def delete_service(service_id):
    s = Service.query.get(service_id)
    if not s:
        return jsonify({"error": "Service not found"}), 404
    db.session.delete(s)
    db.session.commit()
    cache.clear()
    return jsonify({"message": "Service deleted"})

@app.route("/api/admin/delete_vehicle/<int:vehicle_id>", methods=["DELETE"])
@admin_required
def delete_vehicle(vehicle_id):
    v = Vehicle.query.get(vehicle_id)
    if not v:
        return jsonify({"error": "Vehicle not found"}), 404
    db.session.delete(v)
    db.session.commit()
    cache.clear()
    return jsonify({"message": "Vehicle deleted"})

@app.route("/api/admin/delete_stop/<int:stop_id>", methods=["DELETE"])
@admin_required
def delete_stop(stop_id):
    st = Stop.query.get(stop_id)
    if not st:
        return jsonify({"error": "Stop not found"}), 404
    db.session.delete(st)
    db.session.commit()
    cache.clear()
    return jsonify({"message": "Stop deleted"})

@app.route("/api/admin/delete_driver/<int:driver_id>", methods=["DELETE"])
@admin_required
def delete_driver(driver_id):
    d = Driver.query.get(driver_id)
    if not d:
        return jsonify({"error": "Driver not found"}), 404
    db.session.delete(d)
    db.session.commit()
    return jsonify({"message": "Driver deleted"})

# ── Admin Create Admin User ──
@app.route("/api/admin/create_admin", methods=["POST"])
@admin_required
def create_admin_user():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    hashed_pw = generate_password_hash(password)
    try:
        user = User(username=username, password=hashed_pw, is_admin=True)
        db.session.add(user)
        db.session.commit()
        return jsonify({"message": "Admin user created successfully"})
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Username already exists"}), 409


# ═══════════════════════════════════════════════════════
# RUN
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug)