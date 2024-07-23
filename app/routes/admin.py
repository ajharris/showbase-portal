from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, session, jsonify, request, current_app
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from ..models import Crew, Location, Worker, CrewAssignment, Event, Role
from ..forms import AssignWorkerForm, AdminCreateWorkerForm, EditWorkerForm, LocationForm, RoleForm
from .. import db
from ..utils import ROLES
import json
import logging

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Role management routes
@admin_bp.route('/roles', methods=['GET'])
@login_required
def list_roles():
    roles = Role.query.all()
    return render_template('admin/list_roles.html', roles=roles)

@admin_bp.route('/create_role', methods=['GET', 'POST'])
@login_required
def create_role():
    form = RoleForm()
    if form.validate_on_submit():
        role = Role(name=form.name.data, description=form.description.data)
        db.session.add(role)
        db.session.commit()
        flash('Role created successfully', 'success')
        return redirect(url_for('admin.list_roles'))
    return render_template('admin/create_role.html', form=form)

@admin_bp.route('/edit_role/<int:role_id>', methods=['GET', 'POST'])
@login_required
def edit_role(role_id):
    role = Role.query.get_or_404(role_id)
    form = RoleForm(obj=role)
    if form.validate_on_submit():
        role.name = form.name.data
        role.description = form.description.data
        db.session.commit()
        flash('Role updated successfully', 'success')
        return redirect(url_for('admin.list_roles'))
    return render_template('admin/edit_role.html', form=form)

@admin_bp.route('/delete_role/<int:role_id>', methods=['POST'])
@login_required
def delete_role(role_id):
    role = Role.query.get_or_404(role_id)
    db.session.delete(role)
    db.session.commit()
    flash('Role deleted successfully', 'success')
    return redirect(url_for('admin.list_roles'))

# Worker management routes
@admin_bp.route('/create_worker', methods=['GET', 'POST'])
@login_required
def create_worker():
    form = AdminCreateWorkerForm()
    if form.validate_on_submit():
        role_capabilities = {role.name: form.role_capabilities[i].capability.data for i, role in enumerate(Role.query.all())}
        worker = Worker(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            phone_number=form.phone_number.data,
            is_admin=form.is_admin.data,
            is_account_manager=form.is_account_manager.data,
            role_capabilities=role_capabilities
        )
        worker.set_password(form.temp_password.data)
        db.session.add(worker)
        db.session.commit()
        flash('Worker created successfully', 'success')
        return redirect(url_for('admin.create_worker'))
    workers = Worker.query.all()
    return render_template('admin/admin_create_worker.html', form=form, workers=workers)

@admin_bp.route('/edit_worker/<int:worker_id>', methods=['GET', 'POST'])
@login_required
def edit_worker(worker_id):
    worker = Worker.query.get_or_404(worker_id)
    form = EditWorkerForm(obj=worker)
    if request.method == 'GET':
        form.populate_role_capabilities(worker.role_capabilities)
    if form.validate_on_submit():
        worker.first_name = form.first_name.data
        worker.last_name = form.last_name.data
        worker.email = form.email.data
        worker.phone_number = form.phone_number.data
        worker.is_admin = form.is_admin.data
        worker.is_account_manager = form.is_account_manager.data
        worker.role_capabilities = {role.name: form.role_capabilities[i].capability.data for i, role in enumerate(Role.query.all())}
        db.session.commit()
        flash('Worker updated successfully', 'success')
        return redirect(url_for('admin.edit_worker', worker_id=worker.id))
    return render_template('admin/edit_worker.html', form=form, worker=worker)

# Existing routes for shifts, events, etc. remain unchanged
@admin_bp.route('/view_all_shifts')
@login_required
def view_all_shifts():
    now = datetime.utcnow()
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

def handle_view_modes(view_as_employee=None, view_as_manager=None):
    if view_as_employee is not None:
        session['view_as_employee'] = view_as_employee == 'true'
        session.pop('view_as_account_manager', None)
    if view_as_manager is not None:
        session['view_as_account_manager'] = view_as_manager == 'true'
        session.pop('view_as_employee', None)

@admin_bp.route('/unfulfilled_crew_requests', methods=['GET', 'POST'])
@login_required
def unfulfilled_crew_requests():
    form = AssignWorkerForm()
    form.worker.choices = [(worker.id, f'{worker.first_name} {worker.last_name}') for worker in Worker.query.all()]

    if form.validate_on_submit():
        worker_id = form.worker.data
        crew_id = form.crew_id.data
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
            flash(f'Worker assigned successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')

        return redirect(url_for('admin.unfulfilled_crew_requests'))

    unfulfilled_crews = [crew for crew in Crew.query.all() if not crew.is_fulfilled]
    workers = Worker.query.all()
    return render_template('admin/admin_unfulfilled_crew_requests.html', form=form, unfulfilled_crews=unfulfilled_crews, workers=workers)

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

@admin_bp.route('/assign_worker', methods=['POST'])
@login_required
def assign_worker():
    form = AssignWorkerForm()
    form.worker.choices = [(worker.id, f'{worker.first_name} {worker.last_name}') for worker in Worker.query.all()]

    if form.validate_on_submit():
        worker_id = form.worker.data
        crew_id = form.crew_id.data
        role = form.role.data

        try:
            if CrewAssignment.is_role_fulfilled(crew_id, role):
                flash('This role is already fulfilled.', 'warning')
                return redirect(url_for('admin.unfulfilled_crew_requests'))

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
