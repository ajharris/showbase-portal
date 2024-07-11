# routes/admin.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from ..models import Crew, Location, Worker, CrewAssignment
from ..forms import AssignWorkerForm, AdminCreateWorkerForm, LocationForm
from .. import db

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

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
    form = AssignWorkerForm()

    if request.method == 'POST':
        crew_id = request.form.get('crew_id')
        role = request.form.get('role')
        worker_id = request.form.get('worker')

        # Find the crew and worker
        crew = Crew.query.get(crew_id)
        worker = Worker.query.get(worker_id)

        if crew and worker:
            # Create a new assignment
            assignment = CrewAssignment(
                crew_id=crew.id,
                worker_id=worker.id,
                role=role,
                status='offered'
            )
            db.session.add(assignment)
            db.session.commit()
            flash('Worker assigned successfully.', 'success')
        else:
            flash('Invalid crew or worker.', 'danger')

        return redirect(url_for('admin.unfulfilled_crew_requests'))

    crews = Crew.query.filter(Crew.id.notin_(db.session.query(CrewAssignment.crew_id))).all()

    workers = Worker.query.all()
    form.worker.choices = [(worker.id, f'{worker.first_name} {worker.last_name}') for worker in workers]

    return render_template('admin/admin_unfulfilled_crew_requests.html', form=form, crews=crews)

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
        worker.set_temp_password(form.temp_password.data)
        try:
            db.session.add(worker)
            db.session.commit()
            flash('Worker created successfully!', 'success')
            return redirect(url_for('admin.create_worker'))
        except IntegrityError:
            db.session.rollback()
            flash('Email already registered. Please use a different email.', 'danger')
    else:
        print(f"Form errors: {form.errors}")  # Debug statement to help identify errors

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
