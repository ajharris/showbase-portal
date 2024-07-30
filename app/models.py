from datetime import datetime, timedelta
from flask import current_app
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer as Serializer
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.types import JSON
from . import db
import json
import logging

logger = logging.getLogger(__name__)

class Worker(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(30))
    is_admin = db.Column(db.Boolean, default=False)
    is_account_manager = db.Column(db.Boolean, default=False)
    password_hash = db.Column(db.String(256))
    theme = db.Column(db.String(10), default='light')
    active = db.Column(db.Boolean, default=True)
    password_is_temp = db.Column(db.Boolean, default=True)
    role_capabilities = db.Column(MutableDict.as_mutable(JSON), default=lambda: {})

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_available(self, start_time, end_time):
        for assignment in self.crew_assignments:
            if assignment.status in ['offered', 'accepted'] and not (assignment.assigned_crew.end_time <= start_time or assignment.assigned_crew.start_time >= end_time):
                logging.debug(f'Worker {self.first_name} {self.last_name} is not available between {start_time} and {end_time}')
                return False
        logging.debug(f'Worker {self.first_name} {self.last_name} is available between {start_time} and {end_time}')
        return True

    def get_role_capabilities(self):
        return self.role_capabilities

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(256))

    def __repr__(self):
        return f'<Role {self.name}>'

class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    address = db.Column(db.String(256), nullable=False)
    loading_notes = db.Column(db.String(1024))
    dress_code = db.Column(db.String(256))
    other_info = db.Column(db.String(1024))

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

    def is_within_48_hours(self):
        return any(crew.start_time <= datetime.utcnow() <= crew.start_time + timedelta(hours=48) for crew in self.crews)

    def has_unfulfilled_requests(self):
        return any(not crew.is_fulfilled for crew in self.crews)

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

    crew_assignments = db.relationship('CrewAssignment', backref='assigned_crew', lazy=True)

    def get_roles(self):
        return json.loads(self.roles)

    def get_assigned_role_count(self, role):
        count = sum(1 for assignment in self.crew_assignments if assignment.role == role and assignment.status in ['offered', 'accepted'])
        logging.debug(f'Role: {role}, Assigned Count: {count}')
        return count

    def get_assigned_roles(self):
        assigned_roles = {}
        for assignment in self.crew_assignments:
            if assignment.status in ['offered', 'accepted']:
                assigned_roles[assignment.role] = assigned_roles.get(assignment.role, 0) + 1
        return assigned_roles

    def get_unassigned_roles(self):
        required_roles = self.get_roles()
        assigned_roles = self.get_assigned_roles()
        unassigned_roles = {role: required_roles[role] - assigned_roles.get(role, 0) for role in required_roles}
        logging.debug(f'Unassigned Roles: {unassigned_roles}')
        return {role: count for role, count in unassigned_roles.items() if count > 0}

    @property
    def is_fulfilled(self):
        required_roles = self.get_roles()
        for role, count in required_roles.items():
            if self.get_assigned_role_count(role) < count:
                return False
        return True

    def assign_worker(self, worker, role):
        if self.get_assigned_role_count(role) < self.get_roles().get(role, 0):
            new_assignment = CrewAssignment(
                crew_id=self.id,
                worker_id=worker.id,
                role=role,
                status='offered'
            )
            db.session.add(new_assignment)
            db.session.commit()

    def get_assignment_for_role(self, role):
        assignment = [assignment for assignment in self.crew_assignments if assignment.role == role and assignment.status in ['offered', 'accepted']]
        logging.debug(f'Role: {role}, Assignment: {assignment}')
        return assignment

class CrewAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    crew_id = db.Column(db.Integer, db.ForeignKey('crew.id'), nullable=False)
    worker_id = db.Column(db.Integer, db.ForeignKey('worker.id'), nullable=False)
    role = db.Column(db.String(64), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='offered')

    worker = db.relationship('Worker', backref='crew_assignments')

    @staticmethod
    def is_role_fulfilled(crew_id, role):
        crew = Crew.query.get(crew_id)
        required_roles = crew.get_roles()
        assigned_roles = {r: 0 for r in required_roles.keys()}
        for assignment in crew.crew_assignments:
            if assignment.status in ['offered', 'accepted'] and assignment.role == role:
                assigned_roles[assignment.role] += 1
        return assigned_roles[role] >= required_roles[role]

    def unassign(self):
        db.session.delete(self)
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
