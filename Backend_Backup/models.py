from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Route(db.Model):
    __tablename__ = 'routes'
    route_id = db.Column(db.Integer, primary_key=True)
    route_name = db.Column(db.String, nullable=False)
    from_station = db.Column(db.String, nullable=False)
    to_station = db.Column(db.String, nullable=False)

    services = db.relationship('Service', back_populates='route')
    stops = db.relationship('Stop', back_populates='route')

class Service(db.Model):
    __tablename__ = 'services'
    service_id = db.Column(db.Integer, primary_key=True)
    service_no = db.Column(db.String, nullable=False)
    route_id = db.Column(db.Integer, db.ForeignKey('routes.route_id'))
    service_type = db.Column(db.String)
    ticket_price = db.Column(db.Integer)

    route = db.relationship('Route', back_populates='services')
    vehicles = db.relationship('Vehicle', back_populates='service')
    timetable = db.relationship('TimetableEntry', back_populates='service')

class Vehicle(db.Model):
    __tablename__ = 'vehicles'
    vehicle_id = db.Column(db.Integer, primary_key=True)
    vehicle_no = db.Column(db.String, nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.service_id'))
    status = db.Column(db.String)

    service = db.relationship('Service', back_populates='vehicles')
    location = db.relationship('LiveLocation', uselist=False, back_populates='vehicle')

class Stop(db.Model):
    __tablename__ = 'stops'
    stop_id = db.Column(db.Integer, primary_key=True)
    route_id = db.Column(db.Integer, db.ForeignKey('routes.route_id'))
    stop_name = db.Column(db.String, nullable=False)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    stop_order = db.Column(db.Integer)

    route = db.relationship('Route', back_populates='stops')
    timetable = db.relationship('TimetableEntry', back_populates='stop')

class TimetableEntry(db.Model):
    __tablename__ = 'timetable'
    time_id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.service_id'))
    stop_id = db.Column(db.Integer, db.ForeignKey('stops.stop_id'))
    arrival_time = db.Column(db.String)

    service = db.relationship('Service', back_populates='timetable')
    stop = db.relationship('Stop', back_populates='timetable')

class LiveLocation(db.Model):
    __tablename__ = 'live_location'
    bus_id = db.Column(db.Integer, db.ForeignKey('vehicles.vehicle_id'), primary_key=True)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    speed = db.Column(db.Integer)
    updated_at = db.Column(db.String)

    vehicle = db.relationship('Vehicle', back_populates='location')

class Driver(db.Model):
    __tablename__ = 'drivers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
