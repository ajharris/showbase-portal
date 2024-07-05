# routes/base.py

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..models import CrewAssignment, Crew, Worker, Expense
from .. import db
from datetime import datetime, timedelta
from ..utils import get_pay_periods, createTimeReportCH, createExpenseReportCH

base_bp = Blueprint('base', __name__)

@base_bp.route('/')
@login_required
def home():
    # Fetch upcoming shifts for the current user
    now = datetime.utcnow()
    upcoming_shifts = CrewAssignment.query.join(Crew).filter(
        CrewAssignment.worker_id == current_user.id,
        CrewAssignment.status == 'offered'
    ).all()

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
    expenses = Expense.query.filter(
        Expense.worker_id == current_user.id,
        Expense.date >= selected_period_start,
        Expense.date <= selected_period_end
    ).all()

    # Generate reports
    shift_report = createTimeReportCH(shifts)
    expense_report = createExpenseReportCH(expenses)

    return render_template('base/home.html', upcoming_shifts=upcoming_shifts, pay_periods=pay_periods, selected_period_start=selected_period_start, shift_report=shift_report, expense_report=expense_report)

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
