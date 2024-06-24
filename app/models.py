from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String, nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)

class Event(db.Model):
    __tablename__ = 'event'
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

class Expense(db.Model):
    __tablename__ = 'expense'
    id = db.Column(db.Integer, primary_key=True)
    receiptNumber = db.Column(db.Integer)
    date = db.Column(db.DateTime)
    accountManager = db.Column(db.String)
    showName = db.Column(db.String)
    showNumber = db.Column(db.Integer, db.ForeignKey('event.showNumber'))
    details = db.Column(db.String)
    net = db.Column(db.Float)
    hst = db.Column(db.Float)
    receipt_filename = db.Column(db.String)
    worker_id = db.Column(db.Integer, db.ForeignKey('worker.id'))
    worker = db.relationship('Worker', back_populates='expenses')
    event = db.relationship('Event', back_populates='expenses', primaryjoin="Expense.showNumber == Event.showNumber")

    def __repr__(self):
        return f'<Expense {self.showNumber} - {self.showName}>'

class Shift(db.Model):
    __tablename__ = 'shift'
    id = db.Column(db.Integer, primary_key=True)
    start = db.Column(db.DateTime)
    end = db.Column(db.DateTime)
    showName = db.Column(db.String)
    showNumber = db.Column(db.Integer, db.ForeignKey('event.showNumber'))
    accountManager = db.Column(db.String)
    location = db.Column(db.String)
    worker_id = db.Column(db.Integer, db.ForeignKey('worker.id'))
    worker = db.relationship('Worker', back_populates='shifts')
    event = db.relationship('Event', back_populates='shifts', primaryjoin="Shift.showNumber == Event.showNumber")

    def __repr__(self):
        return f'<Shift {self.showNumber} - {self.showName}>'

class Worker(db.Model, UserMixin):
    __tablename__ = 'worker'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    phone_number = db.Column(db.String, nullable=True)  # New column for phone number
    password_hash = db.Column(db.String, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)  # New column for admin status
    is_account_manager = db.Column(db.Boolean, default=False)  # New column for account manager status
    shifts = db.relationship('Shift', back_populates='worker')
    expenses = db.relationship('Expense', back_populates='worker')

    def __repr__(self):
        return f'<Worker {self.first_name} {self.last_name}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
