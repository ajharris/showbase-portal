from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from flask_wtf.csrf import generate_csrf
from ..models import CrewAssignment, Crew, Expense
from ..utils import get_pay_periods, create_time_report_ch, create_expense_report_ch
from .. import db

base_bp = Blueprint('base', __name__)

@base_bp.route('/')
@login_required
def home():
    # Fetch upcoming shifts for the current user
    now = datetime.utcnow()
    upcoming_shifts = CrewAssignment.query.join(Crew).filter(
        CrewAssignment.worker_id == current_user.id,
        CrewAssignment.status.in_(['offered', 'accepted']),
        Crew.start_time >= now
    ).order_by(Crew.start_time).all()
    
    # Debugging: Log the upcoming shifts
    for shift in upcoming_shifts:
        current_app.logger.debug(f'Upcoming Shift: {shift.id} | Role: {shift.role} | Status: {shift.status} | Start: {shift.crew.start_time} | End: {shift.crew.end_time}')
    
    # Generate a limited number of pay periods
    start_date = datetime(2024, 1, 7)
    num_periods = 5  # Adjust as needed
    pay_periods = get_pay_periods(start_date, num_periods)

    selected_period_start = request.args.get('pay_period', default=None)
    if selected_period_start:
        selected_period_start = datetime.strptime(selected_period_start, '%Y-%m-%d %H:%M:%S')
        selected_period_end = selected_period_start + timedelta(weeks=2) - timedelta(seconds=1)
    else:
        selected_period_start, selected_period_end = pay_periods[-1]  # Default to the most recent completed period

    # Query shifts and expenses based on the selected pay period
    shifts = CrewAssignment.query.join(Crew).filter(
        CrewAssignment.worker_id == current_user.id,
        Crew.start_time >= selected_period_start,
        Crew.end_time <= selected_period_end
    ).all()
    
    # Debugging: Log the shifts for the pay period
    for shift in shifts:
        current_app.logger.debug(f'Shift: {shift.id} | Role: {shift.role} | Status: {shift.status} | Start: {shift.crew.start_time} | End: {shift.crew.end_time}')
    
    expenses = Expense.query.filter(
        Expense.worker_id == current_user.id,
        Expense.date >= selected_period_start,
        Expense.date <= selected_period_end
    ).all()
    
    # Generate reports
    shift_report = create_time_report_ch(shifts)
    expense_report = create_expense_report_ch(expenses)
    
    # Generate CSRF token
    csrf = generate_csrf()

    return render_template('base/home.html', upcoming_shifts=upcoming_shifts, pay_periods=pay_periods, selected_period_start=selected_period_start, shift_report=shift_report, expense_report=expense_report, now=now, csrf=csrf)


@base_bp.route('/accept_offer', methods=['POST'])
@login_required
def accept_offer():
    assignment_id = request.form.get('assignment_id')
    assignment = CrewAssignment.query.get(assignment_id)
    if assignment and assignment.worker_id == current_user.id:
        assignment.status = 'accepted'
        db.session.commit()
        flash('You have accepted the offer.', 'success')
    else:
        flash('Invalid assignment.', 'danger')
    return redirect(url_for('base.home'))

@base_bp.route('/reject_offer', methods=['POST'])
@login_required
def reject_offer():
    assignment_id = request.form.get('assignment_id')
    assignment = CrewAssignment.query.get(assignment_id)
    if assignment and assignment.worker_id == current_user.id:
        assignment.status = 'rejected'
        db.session.commit()
        flash('You have rejected the offer.', 'success')
    else:
        flash('Invalid assignment.', 'danger')
    return redirect(url_for('base.home'))
