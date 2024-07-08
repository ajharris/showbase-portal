from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask import current_app
from itsdangerous import URLSafeTimedSerializer as Serializer
from . import db

class Worker(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    email = db.Column(db.String(120), unique=True, index=True)
    phone_number = db.Column(db.String(20))
    street_address = db.Column(db.String)
    city = db.Column(db.String)
    postal = db.Column(db.String)
    is_admin = db.Column(db.Boolean, default=False)
    is_account_manager = db.Column(db.Boolean, default=False)
    password_hash = db.Column(db.String(128))
    theme = db.Column(db.String(10), default='light')
    active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        return self.active

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return Worker.query.get(user_id)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    showName = db.Column(db.String(128), nullable=False)
    showNumber = db.Column(db.Integer, nullable=False, unique=True)
    accountManager = db.Column(db.String(128), db.ForeignKey('worker.email'), nullable=False)
    location = db.Column(db.String(256))
    sharepoint = db.Column(db.String, nullable=True)
    active = db.Column(db.Boolean, default=True)

    account_manager = db.relationship('Worker', backref='events', lazy=True)
    crews = db.relationship('Crew', backref='event', lazy=True, cascade="all, delete-orphan")
    documents = db.relationship('Document', back_populates='event')
    notes = db.relationship('Note', backref='event', lazy=True, cascade="all, delete-orphan")
    expenses = db.relationship('Expense', backref='event', lazy=True, cascade="all, delete-orphan")
    shifts = db.relationship('Shift', backref='event', lazy=True, cascade="all, delete-orphan")

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    path = db.Column(db.String(256), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)

    event = db.relationship('Event', back_populates='documents')

class Crew(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    roles = db.Column(db.JSON, nullable=False)
    shift_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    
    crew_assignments = db.relationship('CrewAssignment', backref='crew', lazy=True, cascade="all, delete-orphan")

class CrewAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    crew_id = db.Column(db.Integer, db.ForeignKey('crew.id'), nullable=False)
    worker_id = db.Column(db.Integer, db.ForeignKey('worker.id'), nullable=False)
    role = db.Column(db.String(64), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='offered')
    assigned_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    worker = db.relationship('Worker', backref='assignments', lazy=True)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    receiptNumber = db.Column(db.String(50))
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    accountManager = db.Column(db.String(120))
    showName = db.Column(db.String(100))
    showNumber = db.Column(db.String(100), db.ForeignKey('event.showNumber'), nullable=False)
    details = db.Column(db.String(200))
    net = db.Column(db.Float)
    hst = db.Column(db.Float)
    receipt_filename = db.Column(db.String(100))
    worker_id = db.Column(db.Integer, db.ForeignKey('worker.id'), nullable=False)

    worker = db.relationship('Worker', backref='expenses', lazy=True)

class Shift(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    showName = db.Column(db.String(100))
    showNumber = db.Column(db.String(100), db.ForeignKey('event.showNumber'), nullable=False)
    accountManager = db.Column(db.String(120))
    location = db.Column(db.String(200))
    worker_id = db.Column(db.Integer, db.ForeignKey('worker.id'), nullable=False)

    worker = db.relationship('Worker', backref='shifts', lazy=True)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    worker_id = db.Column(db.Integer, db.ForeignKey('worker.id'), nullable=False)
    account_manager_only = db.Column(db.Boolean, default=False)
    account_manager_and_td_only = db.Column(db.Boolean, default=False)

    worker = db.relationship('Worker', backref='notes', lazy=True)
