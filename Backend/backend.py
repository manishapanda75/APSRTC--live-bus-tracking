import sys
import os

# ── Ensure Backend dir is always in the Python path ──
# Fixes `from models import db` whether gunicorn runs from root or Backend/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import math
import time
import threading
from datetime import timedelta, datetime
from functools import wraps

from flask import Flask, jsonify, request, render_template, session, redirect, url_for, make_response
from flask_cors import CORS
from flask_caching import Cache
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
import requests as http_requests
from dotenv import load_dotenv
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy import or_, and_
from sqlalchemy.exc import IntegrityError

from models import db, Route, Service, Vehicle, Stop, TimetableEntry, Driver, User, LiveLocation, BusSchedule

load_dotenv()

# ═══════════════════════════════════════════════════════
# APP CONFIG
# ═══════════════════════════════════════════════════════
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
Talisman(app, content_security_policy=None, force_https=False)
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day", "50 per hour"])

cache = Cache(app, config={
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 300
})

app.secret_key = os.getenv("SECRET_KEY", "fallback_dev_key_change_me")

app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# ── Database ──
_db_url = os.getenv('DATABASE_URL', '')
if _db_url.startswith('postgres://'):
    _db_url = _db_url.replace('postgres://', 'postgresql://', 1)

if not _db_url:
    # Fix for Azure: root is ephemeral, /home is persistent
    if os.environ.get('WEBSITE_HOSTNAME'):
        _db_url = 'sqlite:////home/apsrtc.db'
    else:
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
CORS(app)

# ── Global Template Version (Cache Busting) ──
@app.context_processor
def inject_version():
    return {'v': '1.1.1'}

# ═══════════════════════════════════════════════════════
# DEMO DATA SEEDER (routes + stops + drivers)
# ═══════════════════════════════════════════════════════

def _seed_demo_drivers():
    """Seed routes 28A, 6K, 400K with stops, vehicles and driver accounts."""
    if Driver.query.count() > 0:
        return  # Already seeded

    DEMO = [
        {
            'route_name': 'RTC Complex - Gajuwaka',
            'from': 'RTC Complex, Visakhapatnam',
            'to': 'Gajuwaka',
            'service_no': '28A',
            'service_type': 'Express',
            'ticket_price': 18,
            'vehicle_no': 'AP31 V 1234',
            'driver_user': 'driver_28a',
            'driver_pass': 'pass28a',
            'stops': [
                ('RTC Complex',         17.7231, 83.3012, 1),
                ('Jagadamba Junction',  17.7185, 83.2998, 2),
                ('Dwaraka Nagar',       17.7101, 83.2981, 3),
                ('Seethammadhara',      17.7035, 83.2934, 4),
                ('NAD Junction',        17.6954, 83.2889, 5),
                ('Ukkunagaram',         17.6870, 83.2854, 6),
                ('Gajuwaka',            17.6787, 83.2819, 7),
            ],
        },
        {
            'route_name': 'RTC Complex - Steel Plant',
            'from': 'RTC Complex, Visakhapatnam',
            'to': 'Steel Plant',
            'service_no': '6K',
            'service_type': 'Metro Express',
            'ticket_price': 22,
            'vehicle_no': 'AP31 V 5678',
            'driver_user': 'driver_6k',
            'driver_pass': 'pass6k',
            'stops': [
                ('RTC Complex',         17.7231, 83.3012, 1),
                ('Jagadamba Junction',  17.7185, 83.2998, 2),
                ('Kancharapalem',       17.7090, 83.2953, 3),
                ('Gopalapatnam',        17.6988, 83.2902, 4),
                ('Kurmannapalem',       17.6901, 83.2871, 5),
                ('Ukkunagaram',         17.6870, 83.2854, 6),
                ('Steel Plant Gate',    17.6812, 83.2801, 7),
            ],
        },
        {
            'route_name': 'RTC Complex - Pendurthi',
            'from': 'RTC Complex, Visakhapatnam',
            'to': 'Pendurthi',
            'service_no': '400K',
            'service_type': 'Ordinary',
            'ticket_price': 30,
            'vehicle_no': 'AP31 V 9012',
            'driver_user': 'driver_400k',
            'driver_pass': 'pass400k',
            'stops': [
                ('RTC Complex',         17.7231, 83.3012, 1),
                ('Siripuram',           17.7278, 83.3098, 2),
                ('Old Town',            17.7350, 83.3201, 3),
                ('Kommadi',             17.7489, 83.3312, 4),
                ('Madhurawada',         17.7602, 83.3489, 5),
                ('Kapuluppada',         17.7712, 83.3601, 6),
                ('Pendurthi',           17.7901, 83.3789, 7),
            ],
        },
    ]

    for d in DEMO:
        try:
            # Route
            route = Route.query.filter_by(route_name=d['route_name']).first()
            if not route:
                route = Route(route_name=d['route_name'],
                              from_station=d['from'], to_station=d['to'])
                db.session.add(route)
                db.session.flush()

            # Service
            service = Service.query.filter_by(service_no=d['service_no']).first()
            if not service:
                service = Service(service_no=d['service_no'],
                                  route_id=route.route_id,
                                  service_type=d['service_type'],
                                  ticket_price=d['ticket_price'])
                db.session.add(service)
                db.session.flush()

            # Stops
            if Stop.query.filter_by(route_id=route.route_id).count() == 0:
                for name, lat, lng, order in d['stops']:
                    db.session.add(Stop(route_id=route.route_id,
                                        stop_name=name, lat=lat, lng=lng,
                                        stop_order=order))

            # Vehicle
            if not Vehicle.query.filter_by(vehicle_no=d['vehicle_no']).first():
                vehicle = Vehicle(vehicle_no=d['vehicle_no'],
                                  service_id=service.service_id,
                                  status='Running')
                db.session.add(vehicle)
                db.session.flush()

            # Driver
            if not Driver.query.filter_by(username=d['driver_user']).first():
                driver = Driver(username=d['driver_user'],
                                password=generate_password_hash(d['driver_pass']),
                                assigned_service_id=service.service_id)
                db.session.add(driver)

            db.session.commit()
            print(f"[OK] Seeded driver {d['driver_user']} → service {d['service_no']}", flush=True)
        except Exception as e:
            db.session.rollback()
            print(f"[WARN] Could not seed {d['driver_user']}: {e}", flush=True)


# ── Startup: create tables + seed data ──
with app.app_context():
    try:
        db.create_all()
        print("[OK] Database tables created/verified.", flush=True)
        # Auto-seed admin user
        if not User.query.filter_by(is_admin=True).first():
            admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
            admin = User(
                username='admin',
                password=generate_password_hash(admin_password),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print(f"[OK] Default admin created.", flush=True)

        # Seed bus schedule
        from seed_data import seed_bus_schedule
        seed_bus_schedule(db, BusSchedule)
        # Seed demo routes, stops, services, vehicles and drivers
        _seed_demo_drivers()

    except Exception as e:
        print(f"DB init error: {e}")


# ═══════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def is_admin():
    return "user_id" in session and session.get("is_admin")

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_admin():
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated

def verify_captcha(token):
    secret = os.getenv("RECAPTCHA_SECRET_KEY")
    if not secret:
        # If no secret is configured, bypass for development
        return True
    try:
        res = http_requests.post("https://www.google.com/recaptcha/api/siteverify", data={
            "secret": secret,
            "response": token
        }, timeout=5)
        return res.json().get("success", False)
    except Exception:
        return False

def get_ist_time():
    """Return current IST datetime string HH:MM."""
    from datetime import timezone
    ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist).strftime("%H:%M")

DEBUG_LOGS = []


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

@app.route("/offline")
def offline_page():
    return render_template("offline.html")

@app.route("/manifest.json")
def serve_manifest():
    return app.send_static_file('manifest.json')

@app.route("/service-worker.js")
def serve_sw():
    response = app.send_static_file('service-worker.js')
    response.headers['Content-Type'] = 'application/javascript'
    response.headers['Service-Worker-Allowed'] = '/'
    return response


# ═══════════════════════════════════════════════════════
# BUS SCHEDULE APIs (new)
# ═══════════════════════════════════════════════════════

@app.route("/api/buses")
def api_search_buses():
    """
    Search the BusSchedule table.
    Query params: from, to, type (optional)
    """
    from_loc = request.args.get("from", "RTC Complex")
    to_loc   = request.args.get("to", "").strip()
    bus_type = request.args.get("type", "").strip()

    q = BusSchedule.query.filter(
        BusSchedule.source.ilike(f"%{from_loc}%")
    )
    if to_loc:
        q = q.filter(BusSchedule.destination.ilike(f"%{to_loc}%"))
    if bus_type:
        q = q.filter(BusSchedule.bus_type.ilike(f"%{bus_type}%"))

    q = q.order_by(BusSchedule.departure_time.asc())
    results = [b.to_dict() for b in q.all()]

    # Annotate each result with "minutes_until" based on current IST
    ist_now = get_ist_time()
    for r in results:
        try:
            now_h, now_m = map(int, ist_now.split(":"))
            dep_h, dep_m = map(int, r["departure_time"].split(":"))
            now_total  = now_h * 60 + now_m
            dep_total  = dep_h * 60 + dep_m
            diff = dep_total - now_total
            if diff < 0:
                diff += 1440  # next day
            r["minutes_until"] = diff
            r["is_running"] = (0 <= dep_total - now_total <= int(r.get("duration_minutes", 60)))
        except Exception:
            r["minutes_until"] = None
            r["is_running"] = False

    return jsonify(results)


@app.route("/api/destinations")
@cache.cached(timeout=3600)
def api_destinations():
    """Return list of unique destinations."""
    dests = db.session.query(BusSchedule.destination).distinct().order_by(BusSchedule.destination).all()
    return jsonify([d[0] for d in dests])


@app.route("/api/next-bus")
def api_next_bus():
    """
    Return the next bus departing after current IST time.
    Query param: to=Gajuwaka
    """
    to_loc   = request.args.get("to", "").strip()
    bus_type = request.args.get("type", "").strip()
    ist_now  = get_ist_time()

    q = BusSchedule.query
    if to_loc:
        q = q.filter(BusSchedule.destination.ilike(f"%{to_loc}%"))
    if bus_type:
        q = q.filter(BusSchedule.bus_type.ilike(f"%{bus_type}%"))

    buses = q.order_by(BusSchedule.departure_time.asc()).all()
    if not buses:
        return jsonify({"error": "No buses found"}), 404

    # Find next bus after now (wrap around midnight)
    now_h, now_m = map(int, ist_now.split(":"))
    now_total = now_h * 60 + now_m

    next_bus = None
    min_diff = float('inf')
    for bus in buses:
        dep_h, dep_m = map(int, bus.departure_time.split(":"))
        dep_total = dep_h * 60 + dep_m
        diff = dep_total - now_total
        if diff < 0:
            diff += 1440
        if diff < min_diff:
            min_diff = diff
            next_bus = bus

    if not next_bus:
        return jsonify({"error": "No upcoming buses"}), 404

    result = next_bus.to_dict()
    result["minutes_until"] = min_diff
    return jsonify(result)


@app.route("/api/dashboard")
@cache.cached(timeout=60)
def dashboard():
    routes   = Route.query.count()
    services = Service.query.count()
    vehicles = Vehicle.query.count()
    running  = Vehicle.query.filter_by(status='Running').count()
    drivers  = Driver.query.count()
    schedules = BusSchedule.query.count()
    destinations = db.session.query(BusSchedule.destination).distinct().count()

    return jsonify({
        "total_routes": routes,
        "total_services": services,
        "total_vehicles": vehicles,
        "running_buses": running,
        "total_drivers": drivers,
        "total_schedules": schedules,
        "total_destinations": destinations,
    })


# ═══════════════════════════════════════════════════════
# LEGACY PUBLIC APIs
# ═══════════════════════════════════════════════════════

@app.route("/api/search")
def search_buses():
    from_station = request.args.get("from", "")
    to_station   = request.args.get("to", "")
    service_type = request.args.get("service")

    q = db.session.query(Service, Route, Vehicle).join(Route).join(Vehicle)
    condition = or_(
        and_(Route.from_station.ilike(f"%{from_station}%"), Route.to_station.ilike(f"%{to_station}%")),
        and_(Route.from_station.ilike(f"%{to_station}%"), Route.to_station.ilike(f"%{from_station}%"))
    )
    q = q.filter(condition)
    if service_type:
        q = q.filter(Service.service_type == service_type)

    results = []
    for s, r, v in q.all():
        results.append({"service_no": s.service_no, "route_name": r.route_name,
                        "service_type": s.service_type, "ticket_price": s.ticket_price, "vehicle_no": v.vehicle_no})
    return jsonify(results)


@app.route("/api/timetable")
def timetable():
    from_station = request.args.get("from", "")
    to_station   = request.args.get("to", "")
    q = db.session.query(Service.service_no, TimetableEntry.arrival_time).join(TimetableEntry).join(Route).join(Stop, TimetableEntry.stop_id == Stop.stop_id)
    condition = or_(
        and_(Route.from_station.ilike(f"%{from_station}%"), Route.to_station.ilike(f"%{to_station}%")),
        and_(Route.from_station.ilike(f"%{to_station}%"), Route.to_station.ilike(f"%{from_station}%"))
    )
    q = q.filter(condition).filter(Stop.stop_name.ilike(f"%{from_station}%")).order_by(TimetableEntry.arrival_time.asc())
    return jsonify([{"service_no": sno, "arrival_time": at} for sno, at in q.all()])


@app.route("/api/live/<service_no>")
def live_tracking(service_no):
    res = db.session.query(LiveLocation).join(Vehicle).join(Service).filter(Service.service_no == service_no).first()
    if not res:
        return jsonify({"error": "Live data not found"}), 404
    return jsonify({"lat": res.lat, "lng": res.lng, "speed": res.speed, "updated_at": res.updated_at})


@app.route("/api/route_details/<service_no>")
def route_details(service_no):
    stops = db.session.query(Stop).join(Route).join(Service, Service.route_id == Route.route_id)\
        .filter(Service.service_no == service_no).order_by(Stop.stop_order.asc()).all()
    if not stops:
        return jsonify({"error": "Route details not found"}), 404
    return jsonify([{"name": st.stop_name, "lat": st.lat, "lng": st.lng, "stop_order": st.stop_order} for st in stops])



@app.route("/api/eta/<service_no>")
def bus_eta(service_no):
    """Calculate ETA to final stop based on live GPS location."""
    # Get live location
    loc = db.session.query(LiveLocation).join(Vehicle).join(Service)\
        .filter(Service.service_no == service_no).first()
    if not loc:
        return jsonify({"error": "No live location available"}), 404

    # Get route stops
    stops = db.session.query(Stop).join(Route)\
        .join(Service, Service.route_id == Route.route_id)\
        .filter(Service.service_no == service_no)\
        .order_by(Stop.stop_order.asc()).all()
    if not stops:
        return jsonify({"error": "No route stops found"}), 404

    bus_lat, bus_lng = float(loc.lat), float(loc.lng)

    # Find closest stop ahead of the bus
    closest_stop = min(stops, key=lambda s: haversine(bus_lat, bus_lng, s.lat, s.lng))
    closest_idx  = stops.index(closest_stop)

    # Remaining stops from bus position onward
    remaining_stops = stops[closest_idx:]
    stops_remaining = len(remaining_stops) - 1  # exclude current

    # Calculate distance along remaining stops
    total_km = 0.0
    for i in range(len(remaining_stops) - 1):
        total_km += haversine(remaining_stops[i].lat, remaining_stops[i].lng,
                              remaining_stops[i+1].lat, remaining_stops[i+1].lng)

    # Estimate speed (use live speed or default 25 km/h)
    avg_speed = max(float(loc.speed or 0), 15.0)  # at least 15 km/h
    eta_minutes = int((total_km / avg_speed) * 60) if avg_speed > 0 else 0

    # Bus status based on distance to closest stop
    dist_to_closest = haversine(bus_lat, bus_lng, closest_stop.lat, closest_stop.lng)
    if dist_to_closest < 0.1:
        bus_status = "At Station"
    elif dist_to_closest < 0.5:
        bus_status = "Approaching"
    else:
        bus_status = "En Route"

    return jsonify({
        "service_no":           service_no,
        "destination":          stops[-1].stop_name,
        "closest_stop":         closest_stop.stop_name,
        "stops_remaining":      stops_remaining,
        "remaining_distance_km": round(total_km, 2),
        "eta_minutes":          eta_minutes,
        "bus_status":           bus_status,
    })



@cache.cached(timeout=600)
def get_all_routes():
    routes = Route.query.all()
    return jsonify([{"route_id": r.route_id, "route_name": r.route_name, "from": r.from_station, "to": r.to_station} for r in routes])


@app.route("/api/stations")
@cache.cached(timeout=600)
def get_all_stations():
    from_stations = db.session.query(Route.from_station).distinct()
    to_stations   = db.session.query(Route.to_station).distinct()
    all_stations  = set([r[0] for r in from_stations.all()] + [r[0] for r in to_stations.all()])
    return jsonify(list(all_stations))


# ═══════════════════════════════════════════════════════
# USER AUTH
# ═══════════════════════════════════════════════════════

@app.route("/api/user/register", methods=["POST"])
@limiter.limit("3 per hour")
def user_register():
    data     = request.json
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400
    try:
        user = User(username=username, password=generate_password_hash(password), is_admin=False)
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
    data     = request.json
    username = data.get("username")
    password = data.get("password")
    remember = data.get("remember", False)
    captcha  = data.get("g-recaptcha-response")

    if not verify_captcha(captcha):
        return jsonify({"error": "CAPTCHA validation failed"}), 400

    try:
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session.clear()
            session["user_id"]  = user.id
            session["username"] = user.username
            session["is_admin"] = user.is_admin
            redirect_url = "/admin" if user.is_admin else "/"
            return jsonify({"message": "Login successful", "redirect": redirect_url, "is_admin": user.is_admin})
        return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": f"Server Error: {str(e)}"}), 500


@app.route("/api/user/logout", methods=["POST"])
def user_logout():
    session.clear()
    response = make_response(jsonify({"message": "Logged out", "redirect": "/login"}))
    response.delete_cookie('session')
    return response


# ═══════════════════════════════════════════════════════
# DRIVER AUTH
# ═══════════════════════════════════════════════════════

@app.route("/api/driver/login", methods=["POST"])
@limiter.limit("5 per minute")
def driver_login():
    data     = request.json
    username = data.get("username")
    password = data.get("password")
    captcha  = data.get("g-recaptcha-response")

    if not verify_captcha(captcha):
        return jsonify({"error": "CAPTCHA validation failed"}), 400

    try:
        driver = Driver.query.filter_by(username=username).first()
        if driver and check_password_hash(driver.password, password):
            session.clear()
            session["driver_id"] = driver.id
            session["username"]  = driver.username

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
            return jsonify({"message": "Login successful", "redirect": "/driver", "assigned_service": assigned_service})
        return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": f"Server Error: {str(e)}"}), 500


@app.route("/api/driver/logout", methods=["POST"])
def driver_logout():
    session.clear()
    response = make_response(jsonify({"message": "Logged out", "redirect": "/driver/login"}))
    response.delete_cookie('session')
    return response


@app.route("/api/driver/info")
def driver_info():
    if "driver_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    driver = Driver.query.get(session["driver_id"])
    if not driver:
        return jsonify({"error": "Driver not found"}), 404
    assigned_service = None
    if driver.assigned_service_id:
        svc = Service.query.get(driver.assigned_service_id)
        if svc:
            assigned_service = {"service_id": svc.service_id, "service_no": svc.service_no,
                                "route": svc.route.route_name if svc.route else ""}
    return jsonify({"driver_id": driver.id, "username": driver.username, "assigned_service": assigned_service})


# ═══════════════════════════════════════════════════════
# LOCATION UPDATE
# ═══════════════════════════════════════════════════════

@app.route("/api/debug")
def get_debug_logs():
    return jsonify(DEBUG_LOGS[-20:])


@app.route("/api/update_location", methods=["POST"])
def update_location():
    try:
        data       = request.json
        service_no = data.get("service_no")
        lat        = data.get("lat")
        lng        = data.get("lng")
        speed      = data.get("speed", 0)

        log_entry = f"{time.strftime('%H:%M:%S')}: Received {service_no} at {lat}, {lng}"
        print(log_entry, flush=True)
        DEBUG_LOGS.append(log_entry)

        if not service_no or not lat or not lng:
            return jsonify({"error": "Missing data"}), 400

        if "driver_id" in session:
            driver = Driver.query.get(session["driver_id"])
            if driver and driver.assigned_service_id:
                assigned_svc = Service.query.get(driver.assigned_service_id)
                if assigned_svc and assigned_svc.service_no != service_no:
                    return jsonify({"error": f"Assigned to {assigned_svc.service_no}, not {service_no}"}), 403

        v = db.session.query(Vehicle).join(Service).filter(Service.service_no == service_no).first()
        if not v:
            return jsonify({"error": "Service/Vehicle not found"}), 404

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        loc = LiveLocation.query.filter_by(bus_id=v.vehicle_id).first()
        if loc:
            loc.lat = lat; loc.lng = lng; loc.speed = speed; loc.updated_at = timestamp
        else:
            db.session.add(LiveLocation(bus_id=v.vehicle_id, lat=lat, lng=lng, speed=speed, updated_at=timestamp))
        db.session.commit()
        return jsonify({"message": "Location updated", "time": timestamp, "vehicle_id": v.vehicle_id})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ═══════════════════════════════════════════════════════
# ADMIN APIs
# ═══════════════════════════════════════════════════════

@app.route("/api/admin/routes")
@admin_required
def admin_list_routes():
    routes = Route.query.all()
    return jsonify([{"route_id": r.route_id, "route_name": r.route_name, "from": r.from_station, "to": r.to_station} for r in routes])

@app.route("/api/admin/services")
@admin_required
def admin_list_services():
    services = db.session.query(Service, Route).join(Route).all()
    return jsonify([{"service_id": s.service_id, "service_no": s.service_no, "route_id": s.route_id,
                     "route_name": r.route_name, "service_type": s.service_type, "ticket_price": s.ticket_price}
                    for s, r in services])

@app.route("/api/admin/vehicles")
@admin_required
def admin_list_vehicles():
    vehicles = db.session.query(Vehicle, Service).join(Service).all()
    return jsonify([{"vehicle_id": v.vehicle_id, "vehicle_no": v.vehicle_no, "service_id": v.service_id,
                     "service_no": s.service_no, "status": v.status} for v, s in vehicles])

@app.route("/api/admin/stops")
@admin_required
def admin_list_stops():
    stops = db.session.query(Stop, Route).join(Route).order_by(Stop.route_id, Stop.stop_order).all()
    return jsonify([{"stop_id": st.stop_id, "route_id": st.route_id, "route_name": r.route_name,
                     "stop_name": st.stop_name, "lat": st.lat, "lng": st.lng, "stop_order": st.stop_order}
                    for st, r in stops])

@app.route("/api/admin/drivers")
@admin_required
def admin_list_drivers():
    drivers = Driver.query.all()
    result  = []
    for d in drivers:
        svc_info = None
        if d.assigned_service_id:
            svc = Service.query.get(d.assigned_service_id)
            if svc:
                svc_info = {"service_id": svc.service_id, "service_no": svc.service_no}
        result.append({"id": d.id, "username": d.username, "assigned_service": svc_info})
    return jsonify(result)

@app.route("/api/admin/add_route", methods=["POST"])
@admin_required
def add_route():
    d = request.json
    r = Route(route_name=d["route_name"], from_station=d["from"], to_station=d["to"])
    db.session.add(r); db.session.commit(); cache.clear()
    return jsonify({"message": "Route added", "route_id": r.route_id})

@app.route("/api/admin/add_service", methods=["POST"])
@admin_required
def add_service():
    d = request.json
    s = Service(service_no=d["service_no"], route_id=d["route_id"],
                service_type=d.get("service_type", "Express"), ticket_price=d.get("ticket_price", 0))
    db.session.add(s); db.session.commit(); cache.clear()
    return jsonify({"message": "Service added", "service_id": s.service_id})

@app.route("/api/admin/add_vehicle", methods=["POST"])
@admin_required
def add_vehicle():
    d = request.json
    v = Vehicle(vehicle_no=d["vehicle_no"], service_id=d["service_id"], status=d.get("status", "Running"))
    db.session.add(v); db.session.commit(); cache.clear()
    return jsonify({"message": "Vehicle added", "vehicle_id": v.vehicle_id})

@app.route("/api/admin/add_stop", methods=["POST"])
@admin_required
def add_stop():
    d = request.json
    st = Stop(route_id=d["route_id"], stop_name=d["stop_name"],
              lat=d.get("lat", 0.0), lng=d.get("lng", 0.0), stop_order=d.get("stop_order", 1))
    db.session.add(st); db.session.commit(); cache.clear()
    return jsonify({"message": "Stop added", "stop_id": st.stop_id})

@app.route("/api/admin/assign_driver", methods=["POST"])
@admin_required
def assign_driver():
    d          = request.json
    driver_id  = d.get("driver_id")
    service_id = d.get("service_id")
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

@app.route("/api/admin/add_driver", methods=["POST"])
@admin_required
def add_driver():
    d        = request.json
    username = d.get("username")
    password = d.get("password")
    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400
    try:
        driver = Driver(username=username, password=generate_password_hash(password))
        db.session.add(driver); db.session.commit()
        return jsonify({"message": "Driver added", "id": driver.id})
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Username already exists"}), 409

@app.route("/api/admin/delete_route/<int:route_id>", methods=["DELETE"])
@admin_required
def delete_route(route_id):
    r = Route.query.get(route_id)
    if not r: return jsonify({"error": "Route not found"}), 404
    db.session.delete(r); db.session.commit(); cache.clear()
    return jsonify({"message": "Route deleted"})

@app.route("/api/admin/delete_service/<int:service_id>", methods=["DELETE"])
@admin_required
def delete_service(service_id):
    s = Service.query.get(service_id)
    if not s: return jsonify({"error": "Service not found"}), 404
    db.session.delete(s); db.session.commit(); cache.clear()
    return jsonify({"message": "Service deleted"})

@app.route("/api/admin/delete_vehicle/<int:vehicle_id>", methods=["DELETE"])
@admin_required
def delete_vehicle(vehicle_id):
    v = Vehicle.query.get(vehicle_id)
    if not v: return jsonify({"error": "Vehicle not found"}), 404
    db.session.delete(v); db.session.commit(); cache.clear()
    return jsonify({"message": "Vehicle deleted"})

@app.route("/api/admin/delete_stop/<int:stop_id>", methods=["DELETE"])
@admin_required
def delete_stop(stop_id):
    st = Stop.query.get(stop_id)
    if not st: return jsonify({"error": "Stop not found"}), 404
    db.session.delete(st); db.session.commit(); cache.clear()
    return jsonify({"message": "Stop deleted"})

@app.route("/api/admin/delete_driver/<int:driver_id>", methods=["DELETE"])
@admin_required
def delete_driver(driver_id):
    d = Driver.query.get(driver_id)
    if not d: return jsonify({"error": "Driver not found"}), 404
    db.session.delete(d); db.session.commit()
    return jsonify({"message": "Driver deleted"})

@app.route("/api/admin/create_admin", methods=["POST"])
@admin_required
def create_admin_user():
    d = request.json
    username = d.get("username")
    password = d.get("password")
    captcha  = d.get("g-recaptcha-response")
    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400
    
    if not verify_captcha(captcha):
        return jsonify({"error": "CAPTCHA validation failed"}), 400

    try:
        user = User(username=username, password=generate_password_hash(password), is_admin=True)
        db.session.add(user); db.session.commit()
        return jsonify({"message": "Admin user created"})
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Username already exists"}), 409

@app.route("/api/admin/force_seed")
def force_seed():
    """Emergency: re-seed bus schedule data."""
    try:
        BusSchedule.query.delete()
        db.session.commit()
        from seed_data import seed_bus_schedule
        seed_bus_schedule(db, BusSchedule)
        return jsonify({"message": "Bus schedule re-seeded successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ═══════════════════════════════════════════════════════
# ETA Calculation
# ═══════════════════════════════════════════════════════

@app.route("/api/eta/<service_no>")
def calculate_eta(service_no):
    live = db.session.query(LiveLocation).join(Vehicle).join(Service).filter(Service.service_no == service_no).first()
    if not live:
        return jsonify({"error": "Bus not broadcasting"}), 404
    bus_lat, bus_lng = live.lat, live.lng
    speed = live.speed or 1
    stops = db.session.query(Stop).join(Route).join(Service, Service.route_id == Route.route_id)\
        .filter(Service.service_no == service_no).order_by(Stop.stop_order.asc()).all()
    if not stops:
        return jsonify({"error": "Route stops not found"}), 404
    destination_name = request.args.get("destination", "").strip()
    min_dist, closest_idx = float('inf'), 0
    for i, st in enumerate(stops):
        d = haversine(bus_lat, bus_lng, st.lat, st.lng)
        if d < min_dist:
            min_dist = d; closest_idx = i
    dest_idx = len(stops) - 1
    if destination_name:
        for i, st in enumerate(stops):
            if st.stop_name.lower() == destination_name.lower():
                dest_idx = i; break
    remaining_distance = 0.0
    stops_remaining = 0
    if closest_idx < dest_idx:
        remaining_distance += haversine(bus_lat, bus_lng, stops[closest_idx].lat, stops[closest_idx].lng)
        for i in range(closest_idx, dest_idx):
            remaining_distance += haversine(stops[i].lat, stops[i].lng, stops[i+1].lat, stops[i+1].lng)
        stops_remaining = dest_idx - closest_idx
    else:
        remaining_distance = haversine(bus_lat, bus_lng, stops[dest_idx].lat, stops[dest_idx].lng)
    eta_minutes = int((remaining_distance / max(speed, 1)) * 60)
    dist_to_closest = haversine(bus_lat, bus_lng, stops[closest_idx].lat, stops[closest_idx].lng)
    bus_status = "At Station" if dist_to_closest < 0.3 else ("Approaching" if dist_to_closest < 1.0 else "En Route")
    return jsonify({"service_no": service_no, "remaining_distance_km": round(remaining_distance, 2),
                    "speed_kmph": speed, "eta_minutes": eta_minutes, "stops_remaining": stops_remaining,
                    "destination": stops[dest_idx].stop_name, "closest_stop": stops[closest_idx].stop_name,
                    "bus_status": bus_status, "bus_lat": bus_lat, "bus_lng": bus_lng})


# ═══════════════════════════════════════════════════════
# RUN
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)