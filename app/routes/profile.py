from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..models import Worker
from ..forms import UpdateProfileForm, UpdatePasswordForm
from .. import db

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')

@profile_bp.route('/update', methods=['GET', 'POST'])
@login_required
def update_profile():
    worker_id = request.args.get('worker_id')
    if current_user.is_admin and worker_id:
        worker = Worker.query.get_or_404(worker_id)
    else:
        worker = current_user

    form = UpdateProfileForm(obj=worker)

    if current_user.is_admin:
        form.worker_select.choices = [(w.id, f"{w.first_name} {w.last_name}") for w in Worker.query.all()]

    if form.validate_on_submit():
        worker.first_name = form.first_name.data
        worker.last_name = form.last_name.data
        worker.email = form.email.data
        worker.phone_number = form.phone_number.data
        if current_user.is_admin:
            worker.is_admin = form.is_admin.data
            worker.is_account_manager = form.is_account_manager.data
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile.update_profile', worker_id=worker.id if current_user.is_admin else None))
    else:
        if form.errors:
            print(form.errors)
    
    return render_template('profile/update_profile.html', form=form, worker=worker)

@profile_bp.route('/update_password', methods=['GET', 'POST'])
@login_required
def update_password():
    worker = Worker.query.get_or_404(current_user.id)
    form = UpdatePasswordForm()
    if form.validate_on_submit():
        worker.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been updated!', 'success')
        return redirect(url_for('profile.update_profile', worker_id=current_user.id))
    return render_template('auth/update_password.html', title='Update Password', form=form, worker=worker)

