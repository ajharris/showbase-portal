from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask import current_app
from itsdangerous import URLSafeTimedSerializer as Serializer
from sqlalchemy.ext.hybrid import hybrid_property
from . import db
import json

class Worker(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(30))  # Increase the length to 30
    is_admin = db.Column(db.Boolean, default=False)
    is_account_manager = db.Column(db.Boolean, default=False)
    password_hash = db.Column(db.String(256))
    theme = db.Column(db.String(10), default='light')
    active = db.Column(db.Boolean, default=True)
    password_is_temp = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    address = db.Column(db.String(256), nullable=False)
    loading_notes = db.Column(db.String(1024))  # Increase the length to 1024
    dress_code = db.Column(db.String(256))  # Increase the length to 256
    other_info = db.Column(db.String(1024))  # Increase the length to 1024

    events = db.relationship('Event', backref='location', lazy=True)



class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    show_name = db.Column(db.String(128), nullable=False)
    show_number = db.Column(db.Integer, nullable=False, unique=True)
    account_manager_id = db.Column(db.Integer, db.ForeignKey('worker.id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)
    sharepoint = db.Column(db.String, nullable=True)
    active = db.Column(db.Boolean, default=True)

    account_manager = db.relationship('Worker', foreign_keys=[account_manager_id], backref='events')
    crews = db.relationship('Crew', backref='event', lazy=True, cascade="all, delete-orphan")
    documents = db.relationship('Document', back_populates='event', lazy=True)
    notes = db.relationship('Note', backref='event', lazy=True, cascade="all, delete-orphan")
    expenses = db.relationship('Expense', backref='event_expense', lazy=True, cascade="all, delete-orphan")
    shifts = db.relationship('Shift', backref='event_shift', lazy=True, cascade="all, delete-orphan")

    @hybrid_property
    def account_manager_name(self):
        return f"{self.account_manager.first_name} {self.account_manager.last_name}"


class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    path = db.Column(db.String(256), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)

    event = db.relationship('Event', back_populates='documents')


class Crew(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    roles = db.Column(db.String, nullable=False)
    shift_type = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)

    crew_assignments = db.relationship('CrewAssignment', backref='crew', lazy=True)

    def get_roles(self):
        return json.loads(self.roles)

    @property
    def is_fulfilled(self):
        required_roles = self.get_roles()
        for role, count in required_roles.items():
            assigned_count = sum(1 for assignment in self.crew_assignments if assignment.role == role and assignment.status == 'accepted')
            if assigned_count < count:
                return False
        return True



class CrewAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    crew_id = db.Column(db.Integer, db.ForeignKey('crew.id'), nullable=False)
    worker_id = db.Column(db.Integer, db.ForeignKey('worker.id'), nullable=False)
    role = db.Column(db.String(64), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='offered')

    worker = db.relationship('Worker', backref='assignments', lazy=True)
    shift = db.relationship('Shift', uselist=False, backref='crew_assignment')

    @staticmethod
    def is_role_fulfilled(crew_id, role):
        crew = Crew.query.get(crew_id)
        required_roles = crew.get_roles()
        assigned_roles = {r: 0 for r in required_roles.keys()}
        for assignment in crew.crew_assignments:
            if assignment.status == 'accepted' and assignment.role == role:
                assigned_roles[assignment.role] += 1
        return assigned_roles[role] >= required_roles[role]

    def accept(self):
        if self.status != 'accepted':
            self.status = 'accepted'
            shift = Shift(
                start=self.crew.start_time,
                end=self.crew.end_time,
                show_name=self.crew.event.show_name,
                show_number=self.crew.event.show_number,
                account_manager_id=self.crew.event.account_manager_id,
                location=self.crew.event.location.name,
                worker_id=self.worker_id,
                crew_assignment=self
            )
            db.session.add(shift)
            db.session.commit()


class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    receipt_number = db.Column(db.String(50))
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    account_manager_id = db.Column(db.Integer, db.ForeignKey('worker.id'), nullable=False)
    show_name = db.Column(db.String(100))
    show_number = db.Column(db.Integer, db.ForeignKey('event.show_number'), nullable=False)
    details = db.Column(db.String(200))
    net = db.Column(db.Float)
    hst = db.Column(db.Float)
    receipt_filename = db.Column(db.String(100))
    worker_id = db.Column(db.Integer, db.ForeignKey('worker.id'), nullable=False)

    worker = db.relationship('Worker', foreign_keys=[worker_id], backref='expenses')


class Shift(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    show_name = db.Column(db.String(100))
    show_number = db.Column(db.Integer, db.ForeignKey('event.show_number'), nullable=False)
    account_manager_id = db.Column(db.Integer, db.ForeignKey('worker.id'), nullable=False)
    location = db.Column(db.String(200))
    worker_id = db.Column(db.Integer, db.ForeignKey('worker.id'), nullable=False)
    crew_assignment_id = db.Column(db.Integer, db.ForeignKey('crew_assignment.id'), nullable=False)

    worker = db.relationship('Worker', foreign_keys=[worker_id], backref='shifts')

    def unassign(self):
        crew_assignment = self.crew_assignment
        if crew_assignment:
            crew_assignment.status = 'offered'
            db.session.delete(self)
            db.session.commit()


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    worker_id = db.Column(db.Integer, db.ForeignKey('worker.id'), nullable=False)
    account_manager_only = db.Column(db.Boolean, default=False)
    account_manager_and_td_only = db.Column(db.Boolean, default=False)

    worker = db.relationship('Worker', backref='notes', lazy=True)
