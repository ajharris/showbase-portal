# app/routes/admin.py
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, session, jsonify, request, current_app
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from ..models import Crew, Location, Worker, CrewAssignment, Event
from ..forms import AssignWorkerForm, AdminCreateWorkerForm, EditWorkerForm, LocationForm, CSRFForm
from .. import db
from ..utils import ROLES
import json
import logging

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

def handle_view_modes(view_as_employee=None, view_as_manager=None):
    if view_as_employee is not None:
        session['view_as_employee'] = view_as_employee == 'true'
        session.pop('view_as_account_manager', None)
    if view_as_manager is not None:
        session['view_as_account_manager'] = view_as_manager == 'true'
        session.pop('view_as_employee', None)

@admin_bp.route('/edit_worker/<int:worker_id>', methods=['GET', 'POST'])
@login_required
def edit_worker(worker_id):
    worker = Worker.query.get_or_404(worker_id)
    form = EditWorkerForm(obj=worker)
    if form.validate_on_submit():
        role_capabilities = {role: getattr(form.role_capabilities, role).data for role in ROLES}
        form.populate_obj(worker)
        worker.role_capabilities = json.dumps(role_capabilities)
        db.session.commit()
        flash('Worker updated successfully!', 'success')
        return redirect(url_for('admin.edit_worker', worker_id=worker.id))
    return render_template('admin/edit_worker.html', form=form, worker=worker)

@admin_bp.route('/view_all_shifts')
@login_required
def view_all_shifts():
    now = datetime.utcnow()
    # Fetch all upcoming crew assignments with status 'unassigned', 'offered', or 'accepted'
    crew_assignments = CrewAssignment.query.join(Crew).filter(
        CrewAssignment.status.in_(['offered', 'accepted']),
        Crew.start_time >= now
    ).order_by(Crew.start_time).all()

    workers = Worker.query.all()
    form = AssignWorkerForm()
    return render_template('admin/view_all_shifts.html', crew_assignments=crew_assignments, workers=workers, form=form)

@admin_bp.route('/save_view_mode', methods=['POST'])
@login_required
def save_view_mode():
    data = request.json
    handle_view_modes(data.get('viewAsEmployee'), data.get('viewAsManager'))
    return jsonify({'status': 'success'})

@admin_bp.route('/unfulfilled_crew_requests', methods=['GET', 'POST'])
@login_required
def unfulfilled_crew_requests():
    form = AssignWorkerForm()

    # Set the worker choices before form validation
    form.worker.choices = [(worker.id, f'{worker.first_name} {worker.last_name}') for worker in Worker.query.all()]

    if form.validate_on_submit():
        worker_id = form.worker.data
        crew_id = form.crew_id.data
        role = form.role.data

        try:
            # Create the crew assignment with status 'offered'
            assignment = CrewAssignment(
                crew_id=crew_id,
                worker_id=worker_id,
                role=role,
                status='offered'
            )
            db.session.add(assignment)
            db.session.commit()
            flash(f'Worker assigned successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')

        return redirect(url_for('admin.unfulfilled_crew_requests'))

    # Fetch all crews that are not fully fulfilled
    unfulfilled_crews = [crew for crew in Crew.query.all() if not crew.is_fulfilled]
    workers = Worker.query.all()
    return render_template('admin/admin_unfulfilled_crew_requests.html', form=form, unfulfilled_crews=unfulfilled_crews, workers=workers)

@admin_bp.route('/create_worker', methods=['GET', 'POST'])
@login_required
def create_worker():
    form = AdminCreateWorkerForm()
    if form.validate_on_submit():
        role_capabilities = {role: getattr(form.role_capabilities, role).data for role in ROLES}
        worker = Worker(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            phone_number=form.phone_number.data,
            is_admin=form.is_admin.data,
            is_account_manager=form.is_account_manager.data,
            role_capabilities=json.dumps(role_capabilities)
        )
        worker.set_password(form.temp_password.data)
        try:
            db.session.add(worker)
            db.session.commit()
            flash('Worker created successfully!', 'success')
            return redirect(url_for('admin.create_worker'))
        except IntegrityError as e:
            db.session.rollback()
            flash('Email already registered. Please use a different email.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'An unexpected error occurred: {str(e)}', 'danger')
    workers = Worker.query.all()
    return render_template('admin/admin_create_worker.html', form=form, workers=workers)

@admin_bp.route('/add_location', methods=['GET', 'POST'])
@login_required
def add_location():
    form = LocationForm()
    if form.validate_on_submit():
        location = Location(
            name=form.name.data,
            address=form.address.data,
            loading_notes=form.loading_notes.data,
            dress_code=form.dress_code.data,
            other_info=form.other_info.data
        )

        db.session.add(location)
        db.session.commit()
        flash('Location added successfully', 'success')
        return redirect(url_for('admin.add_location'))

    return render_template('admin/add_location.html', form=form)

@admin_bp.route('/inactivate_event/<int:event_id>')
@login_required
def inactivate_event(event_id):
    event = Event.query.get_or_404(event_id)
    event.active = False
    db.session.commit()
    flash('Event inactivated successfully.', 'success')
    return redirect(url_for('admin.list_events'))

@admin_bp.route('/view_event/<int:event_id>')
@login_required
def view_event(event_id):
    event = Event.query.get_or_404(event_id)
    return render_template('admin/view_event.html', event=event)

# app/routes/admin.py

from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()

# app/routes/admin.py

# app/routes/admin.py

@admin_bp.route('/assign_worker', methods=['POST'])
@login_required
def assign_worker():
    form = AssignWorkerForm()

    # Set the worker choices before form validation
    form.worker.choices = [(worker.id, f'{worker.first_name} {worker.last_name}') for worker in Worker.query.all()]

    if form.validate_on_submit():
        worker_id = form.worker.data
        crew_id = form.crew_id.data
        role = form.role.data

        try:
            # Check if the role is already fulfilled
            if CrewAssignment.is_role_fulfilled(crew_id, role):
                flash('This role is already fulfilled.', 'warning')
                return redirect(url_for('admin.unfulfilled_crew_requests'))

            # Create the crew assignment with status 'offered'
            assignment = CrewAssignment(
                crew_id=crew_id,
                worker_id=worker_id,
                role=role,
                status='offered'
            )
            db.session.add(assignment)
            db.session.commit()
            flash(f'Worker assigned successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')

        return redirect(url_for('admin.unfulfilled_crew_requests'))

    unfulfilled_crews = [crew for crew in Crew.query.all() if not crew.is_fulfilled]
    workers = Worker.query.all()
    return render_template('admin/admin_unfulfilled_crew_requests.html', form=form, unfulfilled_crews=unfulfilled_crews, workers=workers)

@admin_bp.route('/remind_worker', methods=['POST'])
@login_required
def remind_worker():
    assignment_id = request.form.get('assignment_id')
    assignment = CrewAssignment.query.get_or_404(assignment_id)
    # Implement your reminder logic here
    flash(f'Reminder sent to {assignment.worker.first_name} {assignment.worker.last_name}.', 'success')
    return redirect(url_for('admin.unfulfilled_crew_requests'))

@admin_bp.route('/revoke_offer', methods=['POST'])
@login_required
def revoke_offer():
    assignment_id = request.form.get('assignment_id')
    assignment = CrewAssignment.query.get_or_404(assignment_id)
    db.session.delete(assignment)
    db.session.commit()
    flash(f'Offer revoked for {assignment.worker.first_name} {assignment.worker.last_name}.', 'success')
    return redirect(url_for('admin.unfulfilled_crew_requests'))
