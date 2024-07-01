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
    showName = db.Column(db.String(100))
    showNumber = db.Column(db.String(100), unique=True, nullable=False)
    accountManager = db.Column(db.String(120), db.ForeignKey('worker.email'), nullable=False)
    location = db.Column(db.String(200))
    active = db.Column(db.Boolean, default=True)

    account_manager = db.relationship('Worker', backref='events', lazy=True)

class Shift(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    showName = db.Column(db.String(100))
    showNumber = db.Column(db.String(100), db.ForeignKey('event.showNumber'), nullable=False)
    accountManager = db.Column(db.String(120))
    location = db.Column(db.String(200))
    worker_id = db.Column(db.Integer, db.ForeignKey('worker.id'), nullable=False)

    event = db.relationship('Event', backref='shifts', lazy=True)
    worker = db.relationship('Worker', backref='shifts', lazy=True)

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

    event = db.relationship('Event', backref='expenses', lazy=True)
    worker = db.relationship('Worker', backref='expenses', lazy=True)

class Crew(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    worker_id = db.Column(db.Integer, db.ForeignKey('worker.id'), nullable=False)
    setup = db.Column(db.Boolean, default=False)
    show = db.Column(db.Boolean, default=False)
    strike = db.Column(db.Boolean, default=False)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    roles = db.Column(db.String(200))

    event = db.relationship('Event', backref='crews', lazy=True)
    worker = db.relationship('Worker', backref='crews', lazy=True)
