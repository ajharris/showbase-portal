from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import current_user, login_required
from werkzeug.security import generate_password_hash
from ..models import Worker
from ..forms import AdminCreateWorkerForm
from .. import db

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
