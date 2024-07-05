# routes/misc.py

import os
from datetime import datetime
from flask import (
    Blueprint, render_template, redirect, url_for, flash, request, 
    session, jsonify, current_app
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import Worker, Event, Shift, Expense
from app.forms import ShiftForm, ExpenseForm
from app.utils import (
    createTimeReportCH, createExpenseReportCH, createEventReport, 
    allowed_file
)

misc_bp = Blueprint('misc', __name__)

@misc_bp.route('/upcoming_shifts')
@login_required
def upcoming_shifts():
    now = datetime.utcnow()
    shifts = Shift.query.filter(Shift.worker_id == current_user.id, Shift.start > now).order_by(Shift.start).all()
    return render_template('upcoming_shifts.html', shifts=shifts)

@misc_bp.route('/save_theme', methods=['POST'])
@login_required
def save_theme():
    data = request.get_json()
    theme = data.get('theme')
    if theme in ['light', 'dark']:
        current_user.theme = theme
        db.session.commit()
        return {'status': 'success'}, 200
    return {'status': 'error'}, 400

@misc_bp.route('/save_view_mode', methods=['POST'])
def save_view_mode():
    data = request.get_json()
    view_as_employee = data.get('viewAsEmployee') == 'true'
    view_as_manager = data.get('viewAsManager') == 'true'
    session['view_as_employee'] = view_as_employee
    session['view_as_account_manager'] = view_as_manager
    return jsonify(success=True)

@misc_bp.route('/timesheet', methods=['GET', 'POST'])
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
            return redirect(url_for('misc.timesheet'))
        else:
            flash('Invalid Event Number', 'danger')

    if current_user.is_admin:
        shifts = Shift.query.order_by(Shift.start).all()
    elif current_user.is_account_manager:
        shifts = Shift.query.join(Event).filter(Event.accountManager == current_user.email).order_by(Shift.start).all()
    else:
        shifts = Shift.query.filter_by(worker_id=current_user.id).order_by(Shift.start).all()

    report = createTimeReportCH(shifts)
    return render_template('misc/timesheet.html', shift=shift_form, report=report)

@misc_bp.route('/expenses', methods=['GET', 'POST'])
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
                receipt_file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))

                date_str = expense_form.date.data
                try:
                    date = datetime.strptime(date_str, '%Y-%m-%d')
                except ValueError:
                    flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
                    return render_template('misc/expenses.html', expense_form=expense_form, expenses=[])

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
                return redirect(url_for('misc.expenses'))
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

    return render_template('misc/expenses.html', expense_form=expense_form, expenses=expenses)

@misc_bp.route('/refreshTimesheetDisplay')
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

@misc_bp.route('/refreshExpenseDisplay')
@login_required
def refresh_expense_display():
    if current_user.is_admin:
        expenses = Expense.query.all()
    elif current_user.is_account_manager:
        expenses = Expense.query.join(Event).filter(Event.accountManager == current_user.email).all()
    else:
        expenses = Expense.query.filter_by(worker_id=current_user.id).all()

    report = createExpenseReportCH(expenses)
    return render_template('misc/expense_report.html', report=report)

@misc_bp.route('/refreshEventDisplay')
@login_required
def refresh_event_display():
    filter_option = request.args.get('filter', 'all')
    event_report = createEventReport(filter_option)
    return event_report

@misc_bp.route('/set_event_status/<int:event_id>/<status>', methods=['POST'])
@login_required
def set_event_status(event_id, status):
    event = Event.query.get(event_id)
    if event:
        event.active = (status == 'active')
        db.session.commit()
        return 'Success', 200
    return 'Event not found', 404
