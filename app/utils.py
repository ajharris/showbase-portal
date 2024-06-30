import os
from datetime import datetime
import pandas as pd
from flask import current_app, url_for
from .models import Expense, Event, Shift, Worker
from . import logger


ROLES = ['TD', 'Video', 'Audio', 'Lighting', 'Staging', 'Stagehand', 'Lift Op']


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def get_account_managers():
    return Worker.query.filter_by(is_account_manager=True).all()


def createTimeReportCH(shifts):
    data = {
        'Date': [],
        'Show': [],
        'Location': [],
        'Times': [],
        'Hours': [],
    }

    for shift in shifts:
        data['Date'].append(shift.start.date())
        data['Show'].append(f'{shift.showName}/{shift.showNumber}/{shift.accountManager}')
        data['Location'].append(shift.location)
        data['Times'].append(f'{shift.start.time()} - {shift.end.time()}')
        data['Hours'].append((shift.end - shift.start).total_seconds() / 3600)

    timesheet = pd.DataFrame(data)
    timesheet['Date'] = pd.to_datetime(timesheet['Date'])
    report_html = timesheet.to_html(index=False, classes='table table-striped table-hover')

    return report_html

def createExpenseReportCH(expenses):
    data = {
        'Receipt Number': [],
        'Date': [],
        'Show': [],
        'Location': [],
        'Net': [],
        'HST': [],
        'Total': [],
    }

    for expense in expenses:
        logger.debug(f"Processing expense: {expense}")
        data['Receipt Number'].append(expense.receiptNumber)
        data['Date'].append(expense.date.strftime('%Y-%m-%d') if isinstance(expense.date, datetime) else expense.date)
        data['Show'].append(f'{expense.accountManager}, {expense.showName}/{expense.showNumber}, {expense.details}')
        data['Location'].append(expense.event.location if expense.event else "Unknown location")
        data['Net'].append(expense.net)
        data['HST'].append(expense.hst)
        data['Total'].append(expense.net + expense.hst)

    expensereport = pd.DataFrame(data)
    logger.debug(f"Expense report DataFrame: {expensereport}")

    try:
        expensereport['Date'] = pd.to_datetime(expensereport['Date'], format='%Y-%m-%d')
    except Exception as e:
        logger.error(f"Error converting dates: {e}")

    report_html = expensereport.to_html(index=False, classes='table table-striped table-hover')

    return report_html

def createEventReport(filter_option='all'):
    query = Event.query.order_by(Event.showNumber)
    events = query.filter_by(active=True).all() if filter_option == 'active' else query.all()

    data = {
        'Show Name': [],
        'Show Number': [],
        'Account Manager': [],
        'Location': [],
        'Status': [],
        'Actions': [],
    }

    for event in events:
        data['Show Name'].append(event.showName)
        data['Show Number'].append(event.showNumber)
        data['Account Manager'].append(event.accountManager)
        data['Location'].append(event.location)
        data['Status'].append('Active' if event.active else 'Inactive')

        button_html = (f'<button class="btn btn-danger" onclick="setEventStatus({event.id}, \'inactive\')">Set Inactive</button>'
                       if event.active else
                       f'<button class="btn btn-success" onclick="setEventStatus({event.id}, \'active\')">Set Active</button>')
        view_button = f'<a href="{url_for("view_event", event_id=event.id)}" class="btn btn-info">View Details</a>'
        data['Actions'].append(button_html + view_button)

    event_report = pd.DataFrame(data)
    report_html = event_report.to_html(index=False, classes='table table-bordered table-striped table-hover', escape=False)

    return report_html