# routes/auth.py

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, login_user, logout_user, current_user
from sqlalchemy.exc import IntegrityError
from ..models import Worker
from ..forms import ChangePasswordForm, LoginForm, RegistrationForm, RequestResetForm
from .. import db, mail
from flask_mail import Message

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash('Your password has been updated!', 'success')
        return redirect(url_for('base.home'))
    return render_template('auth/change_password.html', title='Change Password', form=form)

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('base.home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        logger.debug(f"Form data: {form.data}")
        worker = Worker.query.filter_by(email=form.email.data).first()
        if worker and worker.check_password(form.password.data):
            login_user(worker, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('base.home'))
        else:
            logger.error('Login Unsuccessful. Please check email and password')
            flash('Login Unsuccessful. Please check email and password', 'danger')
    logger.debug(f"Form errors: {form.errors}")
    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        worker = Worker(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            phone_number=form.phone_number.data
        )
        worker.set_password(form.password.data)
        try:
            db.session.add(worker)
            db.session.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        except IntegrityError:
            db.session.rollback()
            flash('Email already registered. Please use a different email.', 'danger')
    return render_template('auth/register.html', form=form)

@auth_bp.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('base.home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = Worker.query.filter_by(email=form.email.data).first()
        if user:
            send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_request.html', form=form)

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='noreply@demo.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('auth.reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)
