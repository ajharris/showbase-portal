# app/routes/admin.py
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, session, jsonify, request
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from ..models import Crew, Location, Worker, CrewAssignment, Event
from ..forms import AssignWorkerForm, AdminCreateWorkerForm, EditWorkerForm, LocationForm
from .. import db

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

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
        form.populate_obj(worker)
        db.session.commit()
        flash('Worker updated successfully!', 'success')
        return redirect(url_for('admin.create_worker'))
    return render_template('admin/edit_worker.html', form=form, worker=worker)

@admin_bp.route('/view_all_shifts')
@login_required
def view_all_shifts():
    shifts = []  # Replace with actual data retrieval logic
    return render_template('admin/view_all_shifts.html', shifts=shifts)

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
        logger.debug(f"Form Data - Worker ID: {worker_id}, Crew ID: {crew_id}, Role: {role}")

        try:
            # Check if the role is already fulfilled
            if CrewAssignment.is_role_fulfilled(crew_id, role):
                flash('This role is already fulfilled.', 'warning')
                return redirect(url_for('admin.unfulfilled_crew_requests'))

            # Create the crew assignment
            assignment = CrewAssignment(
                crew_id=crew_id,
                worker_id=worker_id,
                role=role,
                status='offered'
            )
            db.session.add(assignment)
            db.session.commit()
            assigned_worker_name = next((name for id, name in form.worker.choices if id == worker_id), None)
            flash(f'Worker {assigned_worker_name} assigned successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
            logger.error(f"Error assigning worker: {str(e)}")
        return redirect(url_for('admin.unfulfilled_crew_requests'))
    else:
        logger.debug(f"Form errors: {form.errors}")

    unfulfilled_crews = [crew for crew in Crew.query.all() if not crew.is_fulfilled]
    workers = Worker.query.all()
    return render_template('admin/admin_unfulfilled_crew_requests.html', form=form, unfulfilled_crews=unfulfilled_crews, workers=workers)

@admin_bp.route('/create_worker', methods=['GET', 'POST'])
@login_required
def create_worker():
    form = AdminCreateWorkerForm()
    if form.validate_on_submit():
        worker = Worker(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            phone_number=form.phone_number.data,
            is_admin=form.is_admin.data,
            is_account_manager=form.is_account_manager.data
        )
        worker.set_password(form.temp_password.data)
        try:
            db.session.add(worker)
            db.session.commit()
            flash('Worker created successfully!', 'success')
            return redirect(url_for('admin.create_worker'))
        except IntegrityError as e:
            db.session.rollback()
            # Check for unique constraint violation
            if "unique constraint" in str(e.orig):
                flash('Email already registered. Please use a different email.', 'danger')
            else:
                flash(f'IntegrityError: {str(e.orig)}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'An unexpected error occurred: {str(e)}', 'danger')
            logger.error(f"Error creating worker: {str(e)}")
    else:
        flash(f"Form errors: {form.errors}", 'danger')

    workers = Worker.query.all()
    return render_template('admin/admin_create_worker.html', form=form, workers=workers)


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

@admin_bp.route('/delete_event/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted successfully.', 'success')
    return redirect(url_for('admin.list_events'))

@admin_bp.route('/list_events')
@login_required
def list_events():
    events = Event.query.all()
    return render_template('admin/list_events.html', events=events)

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

@admin_bp.route('/assign_worker', methods=['POST'])
@login_required
def assign_worker():
    form = AssignWorkerForm()
    
    # Set the worker choices before form validation
    form.worker.choices = [(worker.id, f'{worker.first_name} {worker.last_name}') for worker in Worker.query.all()]
    assigned_worker_name = None

    logger.debug(f"Worker choices: {form.worker.choices}")

    logger.debug(f"AssignWorkerForm data: {request.form}")
    if form.validate_on_submit():
        worker_id = form.worker.data
        crew_id = form.crew_id.data
        role = form.role.data
        logger.debug(f"Form Data - Worker ID: {worker_id}, Crew ID: {crew_id}, Role: {role}")

        try:
            # Check if the role is already fulfilled
            if CrewAssignment.is_role_fulfilled(crew_id, role):
                flash('This role is already fulfilled.', 'warning')
                return redirect(url_for('admin.unfulfilled_crew_requests'))

            # Create the crew assignment
            assignment = CrewAssignment(
                crew_id=crew_id,
                worker_id=worker_id,
                role=role,
                status='offered'
            )
            db.session.add(assignment)
            db.session.commit()
            assigned_worker_name = next((name for id, name in form.worker.choices if id == worker_id), None)
            flash(f'Worker {assigned_worker_name} assigned successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
            logger.error(f"Error assigning worker: {str(e)}")
        return redirect(url_for('admin.unfulfilled_crew_requests'))
    else:
        logger.debug(f"Form errors: {form.errors}")
        logger.debug(f"Field worker: {form.worker.data}")
        logger.debug(f"Field crew_id: {form.crew_id.data}")
        logger.debug(f"Field role: {form.role.data}")

    unfulfilled_crews = [crew for crew in Crew.query.all() if not crew.is_fulfilled]
    workers = Worker.query.all()
    return render_template('admin/admin_unfulfilled_crew_requests.html', form=form, unfulfilled_crews=unfulfilled_crews, workers=workers)
