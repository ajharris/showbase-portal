from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, session, jsonify, request
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from ..models import Crew, Location, Worker, CrewAssignment, Event
from ..forms import AssignWorkerForm, AdminCreateWorkerForm, LocationForm
from .. import db

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/edit_worker/<int:worker_id>', methods=['GET', 'POST'])
@login_required
def edit_worker(worker_id):
    worker = Worker.query.get_or_404(worker_id)
    form = AdminCreateWorkerForm(obj=worker)
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
    view_as_employee = data.get('viewAsEmployee')
    view_as_manager = data.get('viewAsManager')

    if view_as_employee is not None:
        session['view_as_employee'] = view_as_employee == 'true'
        session.pop('view_as_account_manager', None)

    if view_as_manager is not None:
        session['view_as_account_manager'] = view_as_manager == 'true'
        session.pop('view_as_employee', None)

    return jsonify({'status': 'success'})


@admin_bp.route('/unfulfilled_crew_requests', methods=['GET', 'POST'])
@login_required
def unfulfilled_crew_requests():
    form = AssignWorkerForm()
    if form.validate_on_submit():
        crew_id = form.crew_id.data
        worker_id = form.worker.data
        role = form.role.data
        try:
            assignment = CrewAssignment(
                crew_id=crew_id,
                worker_id=worker_id,
                role=role,
                status='offered'
            )
            db.session.add(assignment)
            db.session.commit()
            flash('Worker assigned successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('admin.unfulfilled_crew_requests'))

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
        except IntegrityError:
            db.session.rollback()
            flash('Email already registered. Please use a different email.', 'danger')
    else:
        print(f"Form errors: {form.errors}")
        print(f"Form data: {form.data}")

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
    if form.validate_on_submit():
        logger.debug(f"Form data: {form.data}")
        worker_id = form.worker.data
        crew_id = form.crew_id.data
        role = form.role.data

        worker = Worker.query.get(worker_id)
        crew = Crew.query.get(crew_id)

        if not worker or not crew:
            logger.error('Invalid Worker ID or Crew ID.')
            flash('Invalid Worker ID or Crew ID.', 'error')
            return redirect(url_for('admin.unfulfilled_crew_requests'))

        existing_assignment = CrewAssignment.query.filter_by(worker_id=worker_id, crew_id=crew_id).first()
        if existing_assignment:
            logger.error('Worker is already assigned to this crew.')
            flash('Worker is already assigned to this crew.', 'error')
            return redirect(url_for('admin.unfulfilled_crew_requests'))

        crew_assignment = CrewAssignment(worker_id=worker_id, crew_id=crew_id, role=role, status='offered')
        db.session.add(crew_assignment)
        db.session.commit()
        logger.info('Worker assigned successfully.')
        flash('Worker assigned successfully.', 'success')
        return redirect(url_for('admin.unfulfilled_crew_requests'))

    logger.debug(f"Form errors: {form.errors}")
    unfulfilled_crews = [crew for crew in Crew.query.all() if not crew.is_fulfilled]
    workers = Worker.query.all()
    return render_template('admin/admin_unfulfilled_crew_requests.html', form=form, unfulfilled_crews=unfulfilled_crews, workers=workers)

