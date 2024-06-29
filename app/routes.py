from flask import render_template, redirect, url_for, flash, request, current_app as app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from . import db, login_manager, logger, mail
from .models import Worker, Shift, Event, Expense, Document
from .forms import LoginForm, UpdateWorkerForm, UpdatePasswordForm, RequestResetForm, ResetPasswordForm, EventForm, ExpenseForm, ShiftForm, NoteForm, DocumentForm, SharePointForm, RegistrationForm, AdminCreateWorkerForm
from .utils import allowed_file, createTimeReportCH, createExpenseReportCH, createEventReport
from flask_mail import Message
from werkzeug.security import generate_password_hash

@login_manager.user_loader
def load_user(user_id):
    return Worker.query.get(int(user_id))

@app.route('/admin/create_worker', methods=['GET', 'POST'])
def admin_create_worker():
    form = AdminCreateWorkerForm()
    workers = Worker.query.all()
    if form.validate_on_submit():
        first_name = form.first_name.data
        last_name = form.last_name.data
        is_admin = form.is_admin.data
        is_account_manager = form.is_account_manager.data
        temporary_password = 'TempPassword123'  # You may want to generate a more secure temporary password

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
        return redirect(url_for('admin_create_worker'))  # Change this to the appropriate redirect location

    return render_template('admin_create_worker.html', form=form, workers=workers)

@app.route('/update_temp_password', methods=['GET', 'POST'])
@login_required
def update_temp_password():
    form = UpdatePasswordForm()
    if form.validate_on_submit():
        current_user.set_password(form.password.data)
        current_user.email = form.email.data  # If email update is required
        db.session.commit()
        flash('Your password has been updated!', 'success')
        return redirect(url_for('index'))
    return render_template('update_temp_password.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Worker.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            if user.check_password('TempPassword123'):  # Check if the password is the temporary one
                flash('Please update your password and email', 'warning')
                return redirect(url_for('update_temp_password'))
            return redirect(url_for('index'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', form=form)


@app.route('/update_profile', methods=['GET', 'POST'])
@login_required
def update_profile():
    form = UpdateWorkerForm(obj=current_user)
    if form.validate_on_submit():
        current_user.email = form.email.data
        current_user.phone_number = form.phone_number.data
        if form.password.data:
            current_user.set_password(form.password.data)
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('index'))
    return render_template('update_profile.html', form=form)


@app.route('/update_password', methods=['GET', 'POST'])
@login_required
def update_password():
    form = UpdatePasswordForm()
    if form.validate_on_submit():
        current_user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been updated!', 'success')
        return redirect(url_for('index'))
    return render_template('update_password.html', form=form)



@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        worker = Worker(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            phone_number=form.phone_number.data
        )
        worker.set_password(form.password.data)
        db.session.add(worker)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/update_worker/<int:worker_id>', methods=['GET', 'POST'])
@login_required
def update_worker(worker_id):
    worker = Worker.query.get_or_404(worker_id)
    view_as_employee = session.get('view_as_employee', False)
    form = UpdateWorkerForm(view_as_employee=view_as_employee, obj=worker)
    
    if form.validate_on_submit():
        worker.first_name = form.first_name.data
        worker.last_name = form.last_name.data
        worker.email = form.email.data
        worker.phone_number = form.phone_number.data
        if not view_as_employee:
            worker.is_admin = form.is_admin.data
            worker.is_account_manager = form.is_account_manager.data
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('index'))
    return render_template('update_profile.html', form=form)






@app.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = Worker.query.filter_by(email=form.email.data).first()
        if user:
            send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = Worker.verify_reset_token(token)
    if not user:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', form=form)

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='noreply@demo.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)

@app.route('/')
@login_required
def index():
    return render_template('index.html', theme=current_user.theme)

@app.route('/create_event', methods=['GET', 'POST'])
@login_required
def create_event():
    form = EventForm()
    form.accountManager.choices = [(manager.email, f"{manager.first_name} {manager.last_name}") for manager in Worker.query.filter_by(is_account_manager=True).all()]
    event_report = createEventReport()

    if form.validate_on_submit():
        existing_event = Event.query.filter_by(showNumber=form.showNumber.data).first()
        if existing_event:
            flash('An event with this Show Number already exists.', 'danger')
        else:
            event = Event(
                showName=form.showName.data,
                showNumber=form.showNumber.data,
                accountManager=form.accountManager.data,
                location=form.location.data
            )
            db.session.add(event)
            db.session.commit()
            flash('Event created successfully!', 'success')
            return redirect(url_for('create_event'))

    return render_template('create_event.html', form=form, event_report=event_report)

@app.route('/timesheet', methods=['GET', 'POST'])
@login_required
def timesheet():
    shift_form = ShiftForm()
    shift_form.worker.choices = [(worker.id, f"{worker.first_name} {worker.last_name}") for worker in Worker.query.all()]

    if shift_form.validate_on_submit():
        showNumber = shift_form.showNumber.data
        event = Event.query.filter_by(showNumber=showNumber).first()

        if event:
            new_shift = Shift(
                start=datetime.strptime(shift_form.start.data, '%m/%d/%Y %I:%M %p'),
                end=datetime.strptime(shift_form.end.data, '%m/%d/%Y %I:%M %p'),
                showName=event.showName,
                showNumber=showNumber,
                accountManager=event.accountManager,
                location=event.location,
                worker_id=shift_form.worker.data
            )
            db.session.add(new_shift)
            db.session.commit()
            flash('Shift added successfully!', 'success')
            return redirect(url_for('timesheet'))
        else:
            flash('Invalid Event Number', 'danger')

    if current_user.is_admin:
        shifts = Shift.query.order_by(Shift.start).all()
    elif current_user.is_account_manager:
        shifts = Shift.query.join(Event).filter(Event.accountManager == current_user.email).order_by(Shift.start).all()
    else:
        shifts = Shift.query.filter_by(worker_id=current_user.id).order_by(Shift.start).all()

    report = createTimeReportCH(shifts)
    return render_template('timesheet.html', shift=shift_form, report=report)

@app.route('/expenses', methods=['GET', 'POST'])
@login_required
def expenses():
    expense_form = ExpenseForm()
    expense_form.worker.choices = [(worker.id, f"{worker.first_name} {worker.last_name}") for worker in Worker.query.all()]

    if expense_form.validate_on_submit():
        show_number = expense_form.showNumber.data
        event = Event.query.filter_by(showNumber=show_number).first()

        if event:
            receipt_file = expense_form.receipt.data
            if receipt_file and allowed_file(receipt_file.filename):
                filename = secure_filename(receipt_file.filename)
                receipt_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                date_str = expense_form.date.data
                try:
                    date = datetime.strptime(date_str, '%Y-%m-%d')
                except ValueError:
                    flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
                    return render_template('expenses.html', expense_form=expense_form, expenses=[])

                new_expense = Expense(
                    receiptNumber=expense_form.receiptNumber.data,
                    date=date,
                    accountManager=event.accountManager,
                    showName=event.showName,
                    showNumber=show_number,
                    details=expense_form.details.data,
                    net=expense_form.net.data,
                    hst=expense_form.hst.data,
                    receipt_filename=filename,
                    worker_id=expense_form.worker.data
                )

                db.session.add(new_expense)
                db.session.commit()

                flash('Expense added successfully', 'success')
                return redirect(url_for('expenses'))
            else:
                flash('Invalid file format for receipt (PDF or JPEG required)', 'danger')
        else:
            flash('Invalid Event Number', 'danger')

    if current_user.is_admin:
        expenses = Expense.query.all()
    elif current_user.is_account_manager:
        expenses = Expense.query.join(Event).filter(Event.accountManager == current_user.email).all()
    else:
        expenses = Expense.query.filter_by(worker_id=current_user.id).all()

    return render_template('expenses.html', expense_form=expense_form, expenses=expenses)

@app.route('/save_theme', methods=['POST'])
@login_required
def save_theme():
    data = request.get_json()
    theme = data.get('theme')
    if theme in ['light', 'dark']:
        current_user.theme = theme
        db.session.commit()
        return {'status': 'success'}, 200
    return {'status': 'error'}, 400

@app.route('/refreshTimesheetDisplay')
@login_required
def refresh_timesheet_display():
    if current_user.is_admin:
        shifts = Shift.query.order_by(Shift.start).all()
    elif current_user.is_account_manager:
        shifts = Shift.query.join(Event).filter(Event.accountManager == current_user.email).order_by(Shift.start).all()
    else:
        shifts = Shift.query.filter_by(worker_id=current_user.id).order_by(Shift.start).all()

    report = createTimeReportCH(shifts)
    return report

@app.route('/refreshExpenseDisplay')
@login_required
def refresh_expense_display():
    if current_user.is_admin:
        expenses = Expense.query.all()
    elif current_user.is_account_manager:
        expenses = Expense.query.join(Event).filter(Event.accountManager == current_user.email).all()
    else:
        expenses = Expense.query.filter_by(worker_id=current_user.id).all()

    report = createExpenseReportCH(expenses)
    return render_template('expense_report.html', report=report)

@app.route('/refreshEventDisplay')
@login_required
def refresh_event_display():
    filter_option = request.args.get('filter', 'all')
    event_report = createEventReport(filter_option)
    return event_report

from flask import request, jsonify, session

@app.route('/save_view_mode', methods=['POST'])
def save_view_mode():
    data = request.get_json()
    view_as_employee = data.get('viewAsEmployee') == 'true'
    session['view_as_employee'] = view_as_employee
    return jsonify(success=True)


@app.route('/set_event_status/<int:event_id>/<status>', methods=['POST'])
@login_required
def set_event_status(event_id, status):
    event = Event.query.get(event_id)
    if event:
        event.active = (status == 'active')
        db.session.commit()
        return 'Success', 200
    return 'Event not found', 404

@app.route('/events', methods=['GET'])
@login_required
def events():
    event_report = createEventReport()
    return render_template('events.html', event_report=event_report)


@app.route('/event/<int:event_id>', methods=['GET', 'POST'])
@login_required
def view_event(event_id):
    event = Event.query.get(event_id)
    if not event:
        flash('Event not found', 'danger')
        return redirect(url_for('create_event'))
    
    shifts = Shift.query.filter_by(showNumber=event.showNumber).all()
    expenses = Expense.query.filter_by(showNumber=event.showNumber).all()

    note_form = NoteForm()
    document_form = DocumentForm()
    sharepoint_form = SharePointForm()

    if note_form.validate_on_submit() and note_form.submit.data:
        event.notes = note_form.notes.data
        db.session.commit()
        flash('Notes added successfully', 'success')
        return redirect(url_for('view_event', event_id=event.id))

    if document_form.validate_on_submit() and document_form.submit.data:
        if document_form.document.data:
            filename = secure_filename(document_form.document.data.filename)
            document_form.document.data.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            new_document = Document(filename=filename, event_id=event.id)
            db.session.add(new_document)
            db.session.commit()
            flash('Document uploaded successfully', 'success')
            return redirect(url_for('view_event', event_id=event.id))

    if sharepoint_form.validate_on_submit() and sharepoint_form.submit.data:
        event.sharepoint_link = sharepoint_form.sharepoint_link.data
        db.session.commit()
        flash('SharePoint link added successfully', 'success')
        return redirect(url_for('view_event', event_id=event.id))

    return render_template('view_event.html', event=event, shifts=shifts, expenses=expenses, note_form=note_form, document_form=document_form, sharepoint_form=sharepoint_form)
