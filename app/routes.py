from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import pandas as pd
from . import db, login_manager, logger
from .models import Worker, Shift, Event, Expense, Document
from .forms import *
from .utils import allowed_file, createTimeReportCH, createExpenseReportCH, createEventReport

@login_manager.user_loader
def load_user(user_id):
    return Worker.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/update_worker/<int:worker_id>', methods=['GET', 'POST'])
@login_required
def update_worker(worker_id):
    worker = Worker.query.get_or_404(worker_id)
    if worker.id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to update this profile.', 'danger')
        return redirect(url_for('index'))

    form = UpdateWorkerForm(obj=worker)
    if form.validate_on_submit():
        worker.first_name = form.first_name.data
        worker.last_name = form.last_name.data
        worker.email = form.email.data
        worker.phone_number = form.phone_number.data
        if current_user.is_admin:
            worker.is_admin = form.is_admin.data
            worker.is_account_manager = form.is_account_manager.data
        db.session.commit()
        flash('Your profile has been updated.', 'success')
        return redirect(url_for('index'))

    return render_template('update_worker.html', form=form, worker=worker)

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
        flash('Registration successful. You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        worker = Worker.query.filter_by(email=form.email.data).first()
        if worker is None or not worker.check_password(form.password.data):
            flash('Invalid email or password', 'danger')
            return redirect(url_for('login'))
        login_user(worker)
        return redirect(url_for('index'))
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/create_event', methods=['GET', 'POST'])
@login_required
def create_event():
    if not current_user.is_admin and not current_user.is_account_manager:
        flash('You do not have permission to view this page.', 'danger')
        return redirect(url_for('index'))

    form = EventForm()
    form.accountManager.choices = [(manager, manager) for manager in accountManagersList]
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
    if current_user.is_admin:
        shifts = Shift.query.order_by(Shift.start).all()
    elif current_user.is_account_manager:
        shifts = Shift.query.join(Event).filter(Event.accountManager == current_user.email).order_by(Shift.start).all()
    else:
        shifts = Shift.query.filter_by(worker_id=current_user.id).order_by(Shift.start).all()

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

    report = createTimeReportCH(shifts)
    return render_template('timesheet.html', shift=shift_form, report=report)

@app.route('/expenses', methods=['GET', 'POST'])
@login_required
def expenses():
    expense_form = ExpenseForm()
    expense_form.worker.choices = [(worker.id, worker.first_name + " " + worker.last_name) for worker in Worker.query.all()]

    if expense_form.validate_on_submit():
        show_number = expense_form.showNumber.data
        event = Event.query.filter_by(showNumber=show_number).first()

        if event:
            if current_user.is_admin or current_user.is_account_manager and current_user == event.accountManager:
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
                flash('You do not have permission to add an expense for this event.', 'danger')
        else:
            flash('Invalid Event Number', 'danger')

    if current_user.is_admin:
        expenses = Expense.query.all()
    elif current_user.is_account_manager:
        expenses = Expense.query.join(Event).filter(Event.accountManager == current_user.email).all()
    else:
        expenses = Expense.query.filter_by(worker_id=current_user.id).all()

    return render_template('expenses.html', expense_form=expense_form, expenses=expenses)

@app.route('/delete_event/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    event = Event.query.get(event_id)
    if not event:
        flash('Event not found', 'danger')
        return redirect(url_for('create_event'))
    
    Shift.query.filter_by(showNumber=event.showNumber).delete()
    Expense.query.filter_by(showNumber=event.showNumber).delete()
    
    for document in event.documents:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], document.filename))
        except Exception as e:
            logger.error(f"Error deleting file {document.filename}: {e}")
        db.session.delete(document)

    db.session.delete(event)
    db.session.commit()
    
    flash('Event and all associated entries deleted successfully', 'success')
    return redirect(url_for('create_event'))

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
def refresh_expense_display():
    report = createExpenseReportCH()
    return render_template('expenses.html', report=report)

@app.route('/refreshEventDisplay')
def refresh_event_display():
    filter_option = request.args.get('filter', 'all')
    event_report = createEventReport(filter_option)
    return event_report

@app.route('/set_event_status/<int:event_id>/<status>', methods=['POST'])
@login_required
def set_event_status(event_id, status):
    event = Event.query.get(event_id)
    if event:
        event.active = (status == 'active')
        db.session.commit()
        return 'Success', 200
    return 'Event not found', 404

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

### Error handlers ###
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

### Shell context ###
@app.shell_context_processor
def make_shell_context():
    return dict(db=db, Shift=Shift, Event=Event, Expense=Expense)
