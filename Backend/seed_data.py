"""
seed_data.py  —  Seeds expanded APSRTC bus routes into the BusSchedule table.
Includes original RTC Complex routes, reverse routes, and new inter-destination routes.
"""

from datetime import datetime, timedelta

# List of major stations
STATIONS = [
    "RTC Complex", "Anakapalle", "Bheemili", "Gajuwaka", "Kurmannapalem",
    "Madhurawada", "NAD Junction", "Pendurthi", "Rushikonda", "Simhachalam", "Steel Plant"
]

STOP_COORDINATES = {
    "RTC Complex":        {"lat": 17.6868, "lon": 83.2185},
    "Jagadamba Junction": {"lat": 17.6978, "lon": 83.2993},
    "Maharani Peta":      {"lat": 17.7034, "lon": 83.2978},
    "MVP Colony":         {"lat": 17.7342, "lon": 83.3012},
    "Gajuwaka":           {"lat": 17.6820, "lon": 83.2054},
    "NAD Junction":       {"lat": 17.7240, "lon": 83.2198},
    "Steel Plant":        {"lat": 17.6925, "lon": 83.1734},
    "Simhachalam":        {"lat": 17.7650, "lon": 83.2712},
    "Pendurthi":          {"lat": 17.8012, "lon": 83.2156},
    "Kurmannapalem":      {"lat": 17.7198, "lon": 83.2367},
    "Madhurawada":        {"lat": 17.7840, "lon": 83.3721},
    "Bheemili":           {"lat": 17.8897, "lon": 83.4563},
    "Anakapalle":         {"lat": 17.6912, "lon": 82.9987},
    "Rushikonda":         {"lat": 17.7823, "lon": 83.3912},
    "Dwaraka Nagar":      {"lat": 17.7231, "lon": 83.3156},
    "Siripuram Junction": {"lat": 17.7198, "lon": 83.3089},
}

def generate_schedule(source, dest, start_h=5, end_h=21, interval_min=25, duration_str="45m", base_fare=20):
    """Generate a list of schedules between two points throughout the day."""
    schedules = []
    current = datetime.strptime(f"{start_h:02d}:00", "%H:%M")
    end_time = datetime.strptime(f"{end_h:02d}:00", "%H:%M")
    
    # Calculate duration in minutes for arrival calculation
    if 'h' in duration_str:
        h_part, m_part = duration_str.split('h')
        dur_mins = int(h_part.strip()) * 60 + (int(m_part.replace('m','').strip()) if m_part.strip() else 0)
    else:
        dur_mins = int(duration_str.replace('m','').strip())

    counter = 1
    while current <= end_time:
        dep_str = current.strftime("%H:%M")
        arr_dt = current + timedelta(minutes=dur_mins)
        arr_str = arr_dt.strftime("%H:%M")
        
        # Mix bus types
        if counter % 3 == 0: bus_type = "Metro Express"
        elif counter % 3 == 1: bus_type = "Express"
        else: bus_type = "Ordinary"
        
        # Unique ID placeholder
        route_id = f"R-{source[:3]}-{dest[:3]}-{counter:02d}".upper().replace(' ','')
        
        schedules.append((route_id, source, dest, bus_type, dep_str, arr_str, duration_str, base_fare))
        
        current += timedelta(minutes=interval_min)
        counter += 1
    return schedules

# ─── Original RTC Complex Data (Condensed Sample for ID reference) ───
ORIGINAL_DATA = [
    # Gajuwaka (15)
    ("VZ001", "RTC Complex", "Gajuwaka", "Metro Express", "05:00", "05:35", "35m", 25),
    ("VZ002", "RTC Complex", "Gajuwaka", "Express",       "05:15", "06:00", "45m", 18),
    ("VZ003", "RTC Complex", "Gajuwaka", "Ordinary",      "05:30", "06:35", "1h 5m", 12),
    ("VZ004", "RTC Complex", "Gajuwaka", "Metro Express", "06:00", "06:35", "35m", 25),
    ("VZ005", "RTC Complex", "Gajuwaka", "Express",       "06:30", "07:15", "45m", 18),
    ("VZ006", "RTC Complex", "Gajuwaka", "Metro Express", "07:15", "07:50", "35m", 25),
    ("VZ007", "RTC Complex", "Gajuwaka", "Ordinary",      "07:45", "08:50", "1h 5m", 12),
    ("VZ008", "RTC Complex", "Gajuwaka", "Express",       "08:30", "09:15", "45m", 18),
    ("VZ009", "RTC Complex", "Gajuwaka", "Metro Express", "10:00", "10:35", "35m", 25),
    ("VZ010", "RTC Complex", "Gajuwaka", "Express",       "12:00", "12:45", "45m", 18),
    ("VZ011", "RTC Complex", "Gajuwaka", "Ordinary",      "13:30", "14:35", "1h 5m", 12),
    ("VZ012", "RTC Complex", "Gajuwaka", "Metro Express", "15:30", "16:05", "35m", 25),
    ("VZ013", "RTC Complex", "Gajuwaka", "Express",       "17:00", "17:45", "45m", 18),
    ("VZ014", "RTC Complex", "Gajuwaka", "Metro Express", "19:00", "19:35", "35m", 25),
    ("VZ015", "RTC Complex", "Gajuwaka", "Ordinary",      "21:00", "22:05", "1h 5m", 12),

    # NAD Junction (13)
    ("VZ016", "RTC Complex", "NAD Junction", "Metro Express", "05:00", "05:25", "25m", 18),
    ("VZ017", "RTC Complex", "NAD Junction", "Express",       "05:20", "05:55", "35m", 12),
    ("VZ018", "RTC Complex", "NAD Junction", "Ordinary",      "05:45", "06:35", "50m", 8),
    ("VZ019", "RTC Complex", "NAD Junction", "Metro Express", "06:30", "06:55", "25m", 18),
    ("VZ020", "RTC Complex", "NAD Junction", "Express",       "07:00", "07:35", "35m", 12),
    ("VZ021", "RTC Complex", "NAD Junction", "Metro Express", "08:00", "08:25", "25m", 18),
    ("VZ022", "RTC Complex", "NAD Junction", "Ordinary",      "09:00", "09:50", "50m", 8),
    ("VZ023", "RTC Complex", "NAD Junction", "Express",       "10:30", "11:05", "35m", 12),
    ("VZ024", "RTC Complex", "NAD Junction", "Metro Express", "12:00", "12:25", "25m", 18),
    ("VZ025", "RTC Complex", "NAD Junction", "Ordinary",      "14:00", "14:50", "50m", 8),
    ("VZ026", "RTC Complex", "NAD Junction", "Express",       "16:00", "16:35", "35m", 12),
    ("VZ027", "RTC Complex", "NAD Junction", "Metro Express", "18:30", "18:55", "25m", 18),
    ("VZ028", "RTC Complex", "NAD Junction", "Ordinary",      "20:30", "21:20", "50m", 8),

    # Steel Plant (13)
    ("VZ029", "RTC Complex", "Steel Plant", "Metro Express", "05:00", "05:45", "45m", 28),
    ("VZ030", "RTC Complex", "Steel Plant", "Express",       "05:30", "06:30", "1h", 20),
    ("VZ031", "RTC Complex", "Steel Plant", "Ordinary",      "06:00", "07:20", "1h 20m", 14),
    ("VZ032", "RTC Complex", "Steel Plant", "Metro Express", "07:00", "07:45", "45m", 28),
    ("VZ033", "RTC Complex", "Steel Plant", "Express",       "07:30", "08:30", "1h", 20),
    ("VZ034", "RTC Complex", "Steel Plant", "Metro Express", "09:00", "09:45", "45m", 28),
    ("VZ035", "RTC Complex", "Steel Plant", "Ordinary",      "09:30", "10:50", "1h 20m", 14),
    ("VZ036", "RTC Complex", "Steel Plant", "Express",       "11:00", "12:00", "1h", 20),
    ("VZ037", "RTC Complex", "Steel Plant", "Metro Express", "13:00", "13:45", "45m", 28),
    ("VZ038", "RTC Complex", "Steel Plant", "Ordinary",      "14:30", "15:50", "1h 20m", 14),
    ("VZ039", "RTC Complex", "Steel Plant", "Express",       "16:00", "17:00", "1h", 20),
    ("VZ040", "RTC Complex", "Steel Plant", "Metro Express", "18:00", "18:45", "45m", 28),
    ("VZ041", "RTC Complex", "Steel Plant", "Ordinary",      "20:00", "21:20", "1h 20m", 14),

    # Simhachalam (13)
    ("VZ042", "RTC Complex", "Simhachalam", "Metro Express", "05:10", "05:40", "30m", 20),
    ("VZ043", "RTC Complex", "Simhachalam", "Express",       "05:30", "06:12", "42m", 15),
    ("VZ044", "RTC Complex", "Simhachalam", "Ordinary",      "06:00", "07:00", "1h", 10),
    ("VZ045", "RTC Complex", "Simhachalam", "Metro Express", "07:00", "07:30", "30m", 20),
    ("VZ046", "RTC Complex", "Simhachalam", "Express",       "08:00", "08:42", "42m", 15),
    ("VZ047", "RTC Complex", "Simhachalam", "Metro Express", "09:30", "10:00", "30m", 20),
    ("VZ048", "RTC Complex", "Simhachalam", "Ordinary",      "10:00", "11:00", "1h", 10),
    ("VZ049", "RTC Complex", "Simhachalam", "Express",       "11:30", "12:12", "42m", 15),
    ("VZ050", "RTC Complex", "Simhachalam", "Metro Express", "13:00", "13:30", "30m", 20),
    ("VZ051", "RTC Complex", "Simhachalam", "Ordinary",      "14:30", "15:30", "1h", 10),
    ("VZ052", "RTC Complex", "Simhachalam", "Express",       "16:00", "16:42", "42m", 15),
    ("VZ053", "RTC Complex", "Simhachalam", "Metro Express", "18:00", "18:30", "30m", 20),
    ("VZ054", "RTC Complex", "Simhachalam", "Ordinary",      "20:30", "21:30", "1h", 10),

    # Pendurthi (12)
    ("VZ055", "RTC Complex", "Pendurthi", "Metro Express", "05:00", "05:50", "50m", 32),
    ("VZ056", "RTC Complex", "Pendurthi", "Express",       "05:30", "06:40", "1h 10m", 22),
    ("VZ057", "RTC Complex", "Pendurthi", "Ordinary",      "06:00", "07:30", "1h 30m", 15),
    ("VZ058", "RTC Complex", "Pendurthi", "Metro Express", "07:30", "08:20", "50m", 32),
    ("VZ059", "RTC Complex", "Pendurthi", "Express",       "09:00", "10:10", "1h 10m", 22),
    ("VZ060", "RTC Complex", "Pendurthi", "Metro Express", "11:00", "11:50", "50m", 32),
    ("VZ061", "RTC Complex", "Pendurthi", "Ordinary",      "12:30", "14:00", "1h 30m", 15),
    ("VZ062", "RTC Complex", "Pendurthi", "Express",       "14:00", "15:10", "1h 10m", 22),
    ("VZ063", "RTC Complex", "Pendurthi", "Metro Express", "16:00", "16:50", "50m", 32),
    ("VZ064", "RTC Complex", "Pendurthi", "Ordinary",      "17:30", "19:00", "1h 30m", 15),
    ("VZ065", "RTC Complex", "Pendurthi", "Express",       "19:00", "20:10", "1h 10m", 22),
    ("VZ066", "RTC Complex", "Pendurthi", "Metro Express", "21:00", "21:50", "50m", 32),

    # Kurmannapalem (13)
    ("VZ067", "RTC Complex", "Kurmannapalem", "Metro Express", "05:00", "05:18", "18m", 12),
    ("VZ068", "RTC Complex", "Kurmannapalem", "Express",       "05:15", "05:40", "25m", 8),
    ("VZ069", "RTC Complex", "Kurmannapalem", "Ordinary",      "05:30", "06:05", "35m", 5),
    ("VZ070", "RTC Complex", "Kurmannapalem", "Metro Express", "06:30", "06:48", "18m", 12),
    ("VZ071", "RTC Complex", "Kurmannapalem", "Express",       "07:00", "07:25", "25m", 8),
    ("VZ072", "RTC Complex", "Kurmannapalem", "Ordinary",      "07:30", "08:05", "35m", 5),
    ("VZ073", "RTC Complex", "Kurmannapalem", "Metro Express", "09:00", "09:18", "18m", 12),
    ("VZ074", "RTC Complex", "Kurmannapalem", "Express",       "11:00", "11:25", "25m", 8),
    ("VZ075", "RTC Complex", "Kurmannapalem", "Metro Express", "13:00", "13:18", "18m", 12),
    ("VZ076", "RTC Complex", "Kurmannapalem", "Ordinary",      "14:30", "15:05", "35m", 5),
    ("VZ077", "RTC Complex", "Kurmannapalem", "Express",       "16:00", "16:25", "25m", 8),
    ("VZ078", "RTC Complex", "Kurmannapalem", "Metro Express", "18:00", "18:18", "18m", 12),
    ("VZ079", "RTC Complex", "Kurmannapalem", "Ordinary",      "20:00", "20:35", "35m", 5),

    # Madhurawada (13)
    ("VZ080", "RTC Complex", "Madhurawada", "Metro Express", "05:00", "05:45", "45m", 28),
    ("VZ081", "RTC Complex", "Madhurawada", "Express",       "05:30", "06:30", "1h", 20),
    ("VZ082", "RTC Complex", "Madhurawada", "Ordinary",      "06:00", "07:20", "1h 20m", 14),
    ("VZ083", "RTC Complex", "Madhurawada", "Metro Express", "07:15", "08:00", "45m", 28),
    ("VZ084", "RTC Complex", "Madhurawada", "Express",       "08:00", "09:00", "1h", 20),
    ("VZ085", "RTC Complex", "Madhurawada", "Metro Express", "10:00", "10:45", "45m", 28),
    ("VZ086", "RTC Complex", "Madhurawada", "Ordinary",      "11:00", "12:20", "1h 20m", 14),
    ("VZ087", "RTC Complex", "Madhurawada", "Express",       "13:00", "14:00", "1h", 20),
    ("VZ088", "RTC Complex", "Madhurawada", "Metro Express", "15:00", "15:45", "45m", 28),
    ("VZ089", "RTC Complex", "Madhurawada", "Ordinary",      "16:00", "17:20", "1h 20m", 14),
    ("VZ090", "RTC Complex", "Madhurawada", "Express",       "18:00", "19:00", "1h", 20),
    ("VZ091", "RTC Complex", "Madhurawada", "Metro Express", "19:30", "20:15", "45m", 28),
    ("VZ092", "RTC Complex", "Madhurawada", "Ordinary",      "21:00", "22:20", "1h 20m", 14),

    # Bheemili (12)
    ("VZ093", "RTC Complex", "Bheemili", "Metro Express", "05:30", "06:40", "1h 10m", 42),
    ("VZ094", "RTC Complex", "Bheemili", "Express",       "06:00", "07:30", "1h 30m", 30),
    ("VZ095", "RTC Complex", "Bheemili", "Ordinary",      "06:30", "08:25", "1h 55m", 20),
    ("VZ096", "RTC Complex", "Bheemili", "Metro Express", "08:00", "09:10", "1h 10m", 42),
    ("VZ097", "RTC Complex", "Bheemili", "Express",       "09:30", "11:00", "1h 30m", 30),
    ("VZ098", "RTC Complex", "Bheemili", "Metro Express", "11:30", "12:40", "1h 10m", 42),
    ("VZ099", "RTC Complex", "Bheemili", "Ordinary",      "13:00", "14:55", "1h 55m", 20),
    ("VZ100", "RTC Complex", "Bheemili", "Express",       "14:30", "16:00", "1h 30m", 30),
    ("VZ101", "RTC Complex", "Bheemili", "Metro Express", "16:00", "17:10", "1h 10m", 42),
    ("VZ102", "RTC Complex", "Bheemili", "Ordinary",      "17:30", "19:25", "1h 55m", 20),
    ("VZ103", "RTC Complex", "Bheemili", "Express",       "19:00", "20:30", "1h 30m", 30),
    ("VZ104", "RTC Complex", "Bheemili", "Metro Express", "21:00", "22:10", "1h 10m", 42),

    # Anakapalle (12)
    ("VZ105", "RTC Complex", "Anakapalle", "Metro Express", "05:00", "06:40", "1h 40m", 65),
    ("VZ106", "RTC Complex", "Anakapalle", "Express",       "05:30", "07:40", "2h 10m", 48),
    ("VZ107", "RTC Complex", "Anakapalle", "Ordinary",      "06:00", "08:45", "2h 45m", 32),
    ("VZ108", "RTC Complex", "Anakapalle", "Metro Express", "07:30", "09:10", "1h 40m", 65),
    ("VZ109", "RTC Complex", "Anakapalle", "Express",       "09:00", "11:10", "2h 10m", 48),
    ("VZ110", "RTC Complex", "Anakapalle", "Metro Express", "11:00", "12:40", "1h 40m", 65),
    ("VZ111", "RTC Complex", "Anakapalle", "Ordinary",      "12:00", "14:45", "2h 45m", 32),
    ("VZ112", "RTC Complex", "Anakapalle", "Express",       "14:00", "16:10", "2h 10m", 48),
    ("VZ113", "RTC Complex", "Anakapalle", "Metro Express", "15:30", "17:10", "1h 40m", 65),
    ("VZ114", "RTC Complex", "Anakapalle", "Ordinary",      "17:00", "19:45", "2h 45m", 32),
    ("VZ115", "RTC Complex", "Anakapalle", "Express",       "18:30", "20:40", "2h 10m", 48),
    ("VZ116", "RTC Complex", "Anakapalle", "Metro Express", "20:00", "21:40", "1h 40m", 65),

    # Rushikonda (13)
    ("VZ117", "RTC Complex", "Rushikonda", "Metro Express", "05:15", "05:50", "35m", 22),
    ("VZ118", "RTC Complex", "Rushikonda", "Express",       "05:45", "06:33", "48m", 16),
    ("VZ119", "RTC Complex", "Rushikonda", "Ordinary",      "06:15", "07:25", "1h 10m", 11),
    ("VZ120", "RTC Complex", "Rushikonda", "Metro Express", "07:00", "07:35", "35m", 22),
    ("VZ121", "RTC Complex", "Rushikonda", "Express",       "08:00", "08:48", "48m", 16),
    ("VZ122", "RTC Complex", "Rushikonda", "Metro Express", "09:30", "10:05", "35m", 22),
    ("VZ123", "RTC Complex", "Rushikonda", "Ordinary",      "10:30", "11:40", "1h 10m", 11),
    ("VZ124", "RTC Complex", "Rushikonda", "Express",       "12:00", "12:48", "48m", 16),
    ("VZ125", "RTC Complex", "Rushikonda", "Metro Express", "14:00", "14:35", "35m", 22),
    ("VZ126", "RTC Complex", "Rushikonda", "Ordinary",      "15:30", "16:40", "1h 10m", 11),
    ("VZ127", "RTC Complex", "Rushikonda", "Express",       "17:00", "17:48", "48m", 16),
    ("VZ128", "RTC Complex", "Rushikonda", "Metro Express", "19:30", "20:05", "35m", 22),
    ("VZ129", "RTC Complex", "Rushikonda", "Ordinary",      "21:00", "22:10", "1h 10m", 11),
]

def format_duration(mins):
    if mins < 60: return f"{mins}m"
    h = mins // 60
    m = mins % 60
    return f"{h}h {m}m" if m > 0 else f"{h}h"

def seed_bus_schedule(db, BusSchedule):
    """Insert original, reverse, and inter-destination routes."""
    if BusSchedule.query.count() > 500:
        print("[OK] Expanded bus schedule already seeded — skipping.", flush=True)
        return

    # 1. Clear existing schedule to allow clean re-seed
    db.session.query(BusSchedule).delete()
    db.session.commit()

    all_rows = []
    
    # --- PHASE 1: Add Original 129 Routes ---
    for row in ORIGINAL_DATA:
        route_code, src, dest, b_type, dep, arr, dur, fare = row
        all_rows.append(BusSchedule(
            route_code=route_code, source=src, destination=dest,
            bus_type=b_type, departure_time=dep, arrival_time=arr,
            duration=dur, fare=fare
        ))
        
        # --- PHASE 2: Generate Reverse Routes for each original ---
        all_rows.append(BusSchedule(
            route_code=f"R-{route_code}", source=dest, destination=src,
            bus_type=b_type, departure_time=dep, arrival_time=arr, # Reuse times for simplicity
            duration=dur, fare=fare
        ))

    # --- PHASE 3: Generate New Inter-Destination Routes ---
    inter_configs = [
        ("Gajuwaka", "Steel Plant", "25m", 15),
        ("Gajuwaka", "NAD Junction", "30m", 18),
        ("Madhurawada", "Rushikonda", "20m", 12),
        ("Simhachalam", "Pendurthi", "35m", 20),
        ("Anakapalle", "Bheemili", "1h 45m", 55),
        ("Kurmannapalem", "NAD Junction", "25m", 15)
    ]

    for src, dest, dur, fare in inter_configs:
        # A -> B
        schedules_ab = generate_schedule(src, dest, duration_str=dur, base_fare=fare)
        for s in schedules_ab:
            all_rows.append(BusSchedule(
                route_code=s[0], source=s[1], destination=s[2], bus_type=s[3],
                departure_time=s[4], arrival_time=s[5], duration=s[6], fare=s[7]
            ))
        # B -> A
        schedules_ba = generate_schedule(dest, src, duration_str=dur, base_fare=fare)
        for s in schedules_ba:
            all_rows.append(BusSchedule(
                route_code=f"RV-{s[0]}", source=s[1], destination=s[2], bus_type=s[3],
                departure_time=s[4], arrival_time=s[5], duration=s[6], fare=s[7]
            ))

    db.session.bulk_save_objects(all_rows)
    db.session.commit()
    print(f"[OK] Seeded {len(all_rows)} bus schedule entries!", flush=True)
