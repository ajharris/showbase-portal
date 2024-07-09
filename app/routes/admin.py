# admin.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import current_user, login_required
from werkzeug.security import generate_password_hash
from ..models import Worker, Crew, CrewAssignment, Event
from ..forms import AdminCreateWorkerForm, AssignWorkerForm
from .. import db
import json

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/create_worker', methods=['GET', 'POST'])
@login_required
def admin_create_worker():
    form = AdminCreateWorkerForm()
    workers = Worker.query.all()
    if form.validate_on_submit():
        first_name = form.first_name.data
        last_name = form.last_name.data
        is_admin = form.is_admin.data
        is_account_manager = form.is_account_manager.data
        temporary_password = 'TempPassword123'  # Consider generating a more secure temporary password

        # Generate a temporary email
        temp_email = f'{first_name.lower()}@nationalshowsystems.com'

        new_worker = Worker(
            first_name=first_name,
            last_name=last_name,
            email=temp_email,  # Use the temporary email
            password_hash=generate_password_hash(temporary_password),
            is_admin=is_admin,
            is_account_manager=is_account_manager
        )
        db.session.add(new_worker)
        db.session.commit()
        flash(f'Worker {first_name} {last_name} created with temporary email {temp_email} and temporary password', 'success')
        return redirect(url_for('admin.admin_create_worker'))  # Adjust the redirect as needed

    return render_template('admin/admin_create_worker.html', form=form, workers=workers)

@admin_bp.route('/save_view_mode', methods=['POST'])
@login_required
def save_view_mode():
    data = request.json
    view_as_employee = data.get('viewAsEmployee')
    view_as_manager = data.get('viewAsManager')
    if view_as_employee is not None:
        session['view_as_employee'] = view_as_employee == 'true'
    if view_as_manager is not None:
        session['view_as_manager'] = view_as_manager == 'true' and current_user.is_admin
    return jsonify({'status': 'success'})

@admin_bp.route('/unfulfilled_crew_requests', methods=['GET', 'POST'])
@login_required
def unfulfilled_crew_requests():
    crews = Crew.query.all()
    workers = Worker.query.all()
    form = AssignWorkerForm()

    if request.method == 'POST':
        form_data = request.form
        print("Form data received:", form_data)

        crew_id = form_data.get('crew_id')
        role = form_data.get('role')
        worker_id = form_data.get('worker')

        # Debugging outputs
        print(f"POST request received with crew_id: {crew_id}, role: {role}, worker_id: {worker_id}")

        if not crew_id or not role or not worker_id:
            flash('Missing required form data', 'danger')
            return redirect(url_for('admin.unfulfilled_crew_requests'))

        crew = Crew.query.get(crew_id)
        if not crew:
            flash(f'No crew found with ID {crew_id}', 'danger')
            return redirect(url_for('admin.unfulfilled_crew_requests'))

        roles = crew.get_roles()
        if roles.get(role, 0) > 0:
            crew_assignment = CrewAssignment(
                crew_id=crew_id,
                worker_id=worker_id,
                role=role,
                status='offered'  # Set status to 'offered'
            )
            db.session.add(crew_assignment)
            roles[role] -= 1
            crew.roles = roles
            db.session.commit()
            flash(f'Worker assigned to role: {role}', 'success')

            # Verify the assignment
            assignment = CrewAssignment.query.filter_by(crew_id=crew_id, role=role, worker_id=worker_id).first()
            if assignment:
                print(f"Assignment created: {assignment}")
            else:
                print("Assignment not found in the database after commit.")
        else:
            flash(f'Role {role} is no longer available', 'danger')
        
        return redirect(url_for('admin.unfulfilled_crew_requests'))

    # Filter out roles that have been fully assigned and accepted
    for crew in crews:
        assignments = CrewAssignment.query.filter_by(crew_id=crew.id).all()
        assigned_roles = {assignment.role: 0 for assignment in assignments if assignment.status != 'accepted'}
        for assignment in assignments:
            if assignment.status != 'accepted':
                assigned_roles[assignment.role] += 1
        roles = crew.get_roles()
        for role in roles:
            roles[role] -= assigned_roles.get(role, 0)
        crew.roles = {role: count for role, count in roles.items() if count > 0}

    # Filter out fully assigned crews
    crews = [crew for crew in crews if crew.get_roles()]

    form.worker.choices = [(worker.id, f'{worker.first_name} {worker.last_name}') for worker in workers]

    return render_template('admin/admin_unfulfilled_crew_requests.html', crews=crews, workers=workers, form=form)
