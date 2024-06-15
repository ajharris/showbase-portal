import os
from datetime import datetime
import pandas as pd
from flask import current_app
from .models import Expense, Event, Shift
from . import logger

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def createTimeReportCH(shifts):
    date = []
    show = []
    location = []
    times = []
    hours = []
    workers = []

    for shift in shifts:
        date.append(shift.start.date())
        show.append(f'{shift.showName}/{shift.showNumber}/{shift.accountManager}')
        location.append(shift.location)
        times.append(f'{shift.start.time()} - {shift.end.time()}')
        hours.append(float((shift.end - shift.start).total_seconds() / 3600))
        if shift.worker:
            workers.append(f'{shift.worker.first_name} {shift.worker.last_name}')
        else:
            workers.append('Unassigned')

    timesheet = pd.DataFrame({
        'Date': date,
        'Show': show,
        'Location': location,
        'Times': times,
        'Hours': hours,
        'Worker': workers
    })

    timesheet['Date'] = pd.to_datetime(timesheet['Date'], format='%Y-%m-%d')
    report_html = timesheet.to_html(index=False, classes='table table-striped table-hover')

    return report_html

def createExpenseReportCH(expenses):
    receiptNumber = []
    date = []
    show = []
    location = []
    details = []
    net = []
    hst = []
    total = []

    for expense in expenses:
        logger.debug(f"Processing expense: {expense}")
        receiptNumber.append(expense.receiptNumber)
        if isinstance(expense.date, datetime):
            date_str = expense.date.strftime('%Y-%m-%d')
            date.append(date_str)
            logger.debug(f"Formatted date (datetime): {date_str}")
        elif isinstance(expense.date, str):
            date.append(expense.date)
            logger.debug(f"Date is already a string: {expense.date}")
        else:
            logger.error(f"Unexpected date format: {expense.date}")
            date.append('Invalid date')

        show.append(f'{expense.accountManager}, {expense.showName}/{expense.showNumber}, {expense.details}')
        
        if expense.event:
            logger.debug(f"Found event for expense: {expense.event}")
            location.append(expense.event.location)
        else:
            logger.debug(f"No event found for expense: {expense}")
            location.append("Unknown location")
        
        net.append(expense.net)
        hst.append(expense.hst)
        total.append(expense.net + expense.hst)

    expensereport = pd.DataFrame({
        'Receipt Number': receiptNumber,
        'Date': date,
        'Show': show,
        'Net': net,
        'HST': hst,
        'Total': total
    })

    logger.debug(f"Expense report DataFrame: {expensereport}")

    try:
        expensereport['Date'] = pd.to_datetime(expensereport['Date'], format='%Y-%m-%d')
    except Exception as e:
        logger.error(f"Error converting dates: {e}")

    report_html = expensereport.to_html(index=False, classes='table table-striped table-hover')

    return report_html

def createEventReport(filter_option='all'):
    if filter_option == 'active':
        events = Event.query.filter_by(active=True).order_by(Event.showNumber).all()
    else:
        events = Event.query.order_by(Event.showNumber).all()
    
    show_names = []
    show_numbers = []
    account_managers = []
    locations = []
    statuses = []
    buttons = []

    for event in events:
        show_names.append(event.showName)
        show_numbers.append(event.showNumber)
        account_managers.append(event.accountManager)
        locations.append(event.location)
        statuses.append('Active' if event.active else 'Inactive')

        if event.active:
            button_html = (
                f'<button class="btn btn-danger" onclick="setEventStatus({event.id}, \'inactive\')">Set Inactive</button>'
            )
        else:
            button_html = (
                f'<button class="btn btn-success" onclick="setEventStatus({event.id}, \'active\')">Set Active</button>'
            )

        view_button = f'<a href="{url_for("view_event", event_id=event.id)}" class="btn btn-info">View Details</a>'

        buttons.append(button_html + view_button)

    event_report = pd.DataFrame({
        'Show Name': show_names,
        'Show Number': show_numbers,
        'Account Manager': account_managers,
        'Location': locations,
        'Status': statuses,
        'Actions': buttons
    })

    report_html = event_report.to_html(index=False, classes='table table-striped table-hover', escape=False)

    return report_html
