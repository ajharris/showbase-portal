import os, json
from datetime import datetime, timedelta
import pandas as pd
from flask import current_app, url_for
from .models import Expense, Event, Shift, Worker
from app import db

ROLES = ['TD', 'Video', 'Audio', 'Lighting', 'Staging', 'Stagehand', 'Lift Op', 'Driver']

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}

from sqlalchemy.orm import class_mapper

def backup_database_to_json(file_path):
    try:
        data = {}

        # Loop through all tables
        for table in db.metadata.sorted_tables:
            table_name = table.name
            data[table_name] = []
            model_class = db.Model._decl_class_registry.get(table_name.capitalize())
            if model_class:
                # Query all data from the table
                records = model_class.query.all()
                for record in records:
                    record_dict = {c.key: getattr(record, c.key) for c in class_mapper(model_class).columns}
                    data[table_name].append(record_dict)

        # Write to JSON file
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4, default=str)

        current_app.logger.info(f"Database backup saved to {file_path}")
        return True

    except Exception as e:
        current_app.logger.error(f"Error backing up database: {e}")
        return False
    
def restore_database_from_json(file_path):
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)

        # Disable foreign key checks
        db.engine.execute('SET FOREIGN_KEY_CHECKS=0;')

        # Loop through all tables
        for table_name, records in data.items():
            model_class = db.Model._decl_class_registry.get(table_name.capitalize())
            if model_class:
                # Delete all existing records in the table
                db.session.query(model_class).delete()
                db.session.commit()
                
                # Insert records from JSON
                for record_dict in records:
                    record = model_class(**record_dict)
                    db.session.add(record)
                db.session.commit()

        # Enable foreign key checks
        db.engine.execute('SET FOREIGN_KEY_CHECKS=1;')

        current_app.logger.info(f"Database restored from {file_path}")
        return True

    except Exception as e:
        current_app.logger.error(f"Error restoring database: {e}")
        return False



def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
        current_app.logger.debug(f"Processing expense: {expense}")
        data['Receipt Number'].append(expense.receiptNumber)
        data['Date'].append(expense.date.strftime('%Y-%m-%d') if isinstance(expense.date, datetime) else expense.date)
        data['Show'].append(f'{expense.accountManager}, {expense.showName}/{expense.showNumber}, {expense.details}')
        data['Location'].append(expense.event.location if expense.event else "Unknown location")
        data['Net'].append(expense.net)
        data['HST'].append(expense.hst)
        data['Total'].append(expense.net + expense.hst)

    expensereport = pd.DataFrame(data)
    current_app.logger.debug(f"Expense report DataFrame: {expensereport}")

    try:
        expensereport['Date'] = pd.to_datetime(expensereport['Date'], format='%Y-%m-%d')
    except Exception as e:
        current_app.logger.error(f"Error converting dates: {e}")

    report_html = expensereport.to_html(index=False, classes='table table-striped table-hover')

    return report_html

from flask_wtf.csrf import generate_csrf

def createEventReport(filter_option='all'):
    current_app.logger.debug("Creating event report with filter: %s", filter_option)
    if filter_option == 'active':
        events = Event.query.filter_by(active=True).order_by(Event.showNumber).all()
    else:
        events = Event.query.order_by(Event.showNumber).all()

    current_app.logger.debug("Events fetched: %s", events)

    data = {
        'Show Name': [],
        'Show Number': [],
        'Account Manager': [],
        'Location': [],
        'Status': [],
        'Actions': [],
    }

    for event in events:
        current_app.logger.debug("Processing event: %s", event)
        data['Show Name'].append(event.showName)
        data['Show Number'].append(event.showNumber)
        data['Account Manager'].append(event.accountManager)
        data['Location'].append(event.location)
        data['Status'].append('Active' if event.active else 'Inactive')

        button_html = (f'<button class="btn btn-danger" onclick="setEventStatus({event.id}, \'inactive\')">Set Inactive</button>'
                       if event.active else
                       f'<button class="btn btn-success" onclick="setEventStatus({event.id}, \'active\')">Set Active</button>')
        view_button = f'<a href="{url_for("events.view_event", event_id=event.id)}" class="btn btn-info">View Details</a>'
        edit_button = f'<a href="{url_for("events.edit_event", event_id=event.id)}" class="btn btn-warning">Edit</a>'

        csrf_token = generate_csrf()  # Generate CSRF token for each form
        delete_form = (
            f'<form id="delete-event-form-{event.id}" action="{url_for("events.delete_event", event_id=event.id)}" method="POST" style="display: inline;">'
            f'<input type="hidden" name="csrf_token" value="{csrf_token}">'
            f'<button type="button" class="btn btn-danger" onclick="confirmDelete({event.id})">Delete</button>'
            f'</form>'
        )

        data['Actions'].append(button_html + view_button + edit_button + delete_form)

    event_report = pd.DataFrame(data)
    report_html = event_report.to_html(index=False, classes='table table-bordered table-striped table-hover', escape=False)

    return report_html


def get_pay_periods(start_date, num_periods):
    pay_periods = []
    now = datetime.utcnow()

    # Calculate the current period start that should not be included
    period_start = start_date
    while period_start + timedelta(weeks=2) <= now:
        period_start += timedelta(weeks=2)

    # Calculate the most recent completed period
    last_completed_period_start = period_start - timedelta(weeks=2)

    # Generate pay periods up to the most recent completed period
    for i in range(num_periods):
        period_start = last_completed_period_start - timedelta(weeks=2 * i)
        period_end = period_start + timedelta(weeks=2) - timedelta(seconds=1)
        pay_periods.append((period_start, period_end))

    # Reverse the list to start from the earliest period
    pay_periods.reverse()

    return pay_periods



