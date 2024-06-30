# models.py

from itsdangerous.url_safe import URLSafeTimedSerializer as Serializer
from flask import current_app
from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Crew(db.Model):
    __tablename__ = 'crews'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    event = db.relationship('Event', back_populates='crews')
    # Additional fields can be added here as required

class Worker(db.Model, UserMixin):
    __tablename__ = 'workers'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    phone_number = db.Column(db.String, nullable=True)
    password_hash = db.Column(db.String, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_account_manager = db.Column(db.Boolean, default=False)
    theme = db.Column(db.String, default='light')
    shifts = db.relationship('Shift', back_populates='worker', lazy=True)
    expenses = db.relationship('Expense', back_populates='worker', lazy=True)

    def __repr__(self):
        return f'<Worker {self.first_name} {self.last_name}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    showName = db.Column(db.String, nullable=False)
    showNumber = db.Column(db.Integer, unique=True, nullable=False)
    accountManager = db.Column(db.String)
    location = db.Column(db.String)
    active = db.Column(db.Boolean)
    notes = db.Column(db.Text)
    sharepoint_link = db.Column(db.String)
    documents = db.relationship('Document', backref='event', lazy=True)
    expenses = db.relationship('Expense', back_populates='event', primaryjoin="Event.showNumber == Expense.showNumber", foreign_keys="[Expense.showNumber]")
    shifts = db.relationship('Shift', back_populates='event', primaryjoin="Event.showNumber == Shift.showNumber", foreign_keys="[Shift.showNumber]")
    crews = db.relationship('Crew', back_populates='event', lazy=True)

    def add_crew_request(self, account_manager, crew_data, shift_data):
        # Check if the account_manager is valid and has permission
        if not account_manager.is_account_manager:
            raise ValueError("User does not have account manager permissions.")

        # Create a new Crew request
        new_crew = Crew(event_id=self.id)
        db.session.add(new_crew)

        # Create and associate Shifts
        for shift in shift_data:
            new_shift = Shift(
                start=shift['start'],
                end=shift['end'],
                showName=self.showName,
                showNumber=self.showNumber,
                accountManager=account_manager.email,
                location=shift['location'],
                worker_id=shift['worker_id'],
                event_id=self.id
            )
            db.session.add(new_shift)

        # Commit changes to the database
        db.session.commit()

class Document(db.Model):
    __tablename__ = 'documents'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String, nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)

class Expense(db.Model):
    __tablename__ = 'expenses'
    id = db.Column(db.Integer, primary_key=True)
    receiptNumber = db.Column(db.Integer)
    date = db.Column(db.DateTime)
    accountManager = db.Column(db.String)
    showName = db.Column(db.String)
    showNumber = db.Column(db.Integer, db.ForeignKey('events.showNumber'))
    details = db.Column(db.String)
    net = db.Column(db.Float)
    hst = db.Column(db.Float)
    receipt_filename = db.Column(db.String)
    worker_id = db.Column(db.Integer, db.ForeignKey('workers.id'))
    worker = db.relationship('Worker', back_populates='expenses')
    event = db.relationship('Event', back_populates='expenses', primaryjoin="Expense.showNumber == Event.showNumber")

    def __repr__(self):
        return f'<Expense {self.showNumber} - {self.showName}>'

class Shift(db.Model):
    __tablename__ = 'shifts'
    id = db.Column(db.Integer, primary_key=True)
    start = db.Column(db.DateTime)
    end = db.Column(db.DateTime)
    showName = db.Column(db.String)
    showNumber = db.Column(db.Integer, db.ForeignKey('events.showNumber'))
    accountManager = db.Column(db.String)
    location = db.Column(db.String)
    worker_id = db.Column(db.Integer, db.ForeignKey('workers.id'))
    worker = db.relationship('Worker', back_populates='shifts')
    event = db.relationship('Event', back_populates='shifts', primaryjoin="Shift.showNumber == Event.showNumber")

    def __repr__(self):
        return f'<Shift {self.showNumber} - {self.showName}>'
