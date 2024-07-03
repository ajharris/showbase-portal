import click
import json
from datetime import datetime
from flask.cli import with_appcontext
from app import create_app, db
from app.models import Worker, Event, Crew, CrewAssignment, Expense, Shift

@click.command("populate-db")
@click.option('--json-file', type=click.Path(exists=True), help="Path to JSON file with seed data")
@with_appcontext
def populate_database(json_file):
    """Populate the database with sample data."""

    if json_file:
        with open(json_file, 'r') as file:
            data = json.load(file)
            workers_data = data.get('workers', [])
            events_data = data.get('events', [])
            crews_data = data.get('crews', [])
            crew_assignments_data = data.get('crew_assignments', [])
            expenses_data = data.get('expenses', [])
            shifts_data = data.get('shifts', [])
    else:
        # Seed data for Workers
        workers_data = [
            {"first_name": "Andrew", "last_name": "Harris", "email": "andrew.harris.av@gmail.com", "phone_number": "(226) 678-5899", "street_address": "123 Main St", "city": "London", "postal": "N6A 1A1", "is_admin": True, "is_account_manager": False, "password_hash": "hashed_password", "theme": "light", "active": True},
            {"first_name": "Rob", "last_name": "Sandolowich", "email": "rob@nationalshowsystems.com", "phone_number": "0987654321", "street_address": "456 Side St", "city": "Toronto", "postal": "M5V 2B1", "is_admin": False, "is_account_manager": True, "password_hash": "hashed_password", "theme": "light", "active": True},
            # Add more workers as needed
        ]

        # Seed data for Events
        events_data = [
            {"showName": "Concert A", "showNumber": "1001", "accountManager": "rob@nationalshowsystems.com", "location": "Stadium A", "active": True},
            {"showName": "Conference B", "showNumber": "1002", "accountManager": "rob@nationalshowsystems.com", "location": "Convention Center B", "active": True},
            # Add more events as needed
        ]

        # Seed data for Crews
        crews_data = [
            {"event_id": 1, "start_time": datetime(2024, 7, 5, 10, 0), "end_time": datetime(2024, 7, 5, 18, 0), "roles": {"TD": 2, "Audio": 3, "Lighting": 1}, "shift_type": "setup", "description": "Setup for Concert A"},
            {"event_id": 2, "start_time": datetime(2024, 7, 6, 8, 0), "end_time": datetime(2024, 7, 6, 17, 0), "roles": {"Stagehand": 4, "Lift Op": 2}, "shift_type": "show", "description": "Show for Conference B"},
            # Add more crews as needed
        ]

        # Seed data for CrewAssignments
        crew_assignments_data = [
            {"crew_id": 1, "worker_id": 1, "role": "TD", "accepted": True, "assigned_time": datetime(2024, 7, 1, 9, 0)},
            {"crew_id": 2, "worker_id": 2, "role": "Stagehand", "accepted": False, "assigned_time": datetime(2024, 7, 2, 10, 0)},
            # Add more crew assignments as needed
        ]

        # Seed data for Expenses
        expenses_data = [
            {"receiptNumber": "R1001", "date": datetime(2024, 7, 1), "accountManager": "rob@nationalshowsystems.com", "showName": "Concert A", "showNumber": "1001", "details": "Equipment Rental", "net": 1000.00, "hst": 130.00, "receipt_filename": "receipt_1001.pdf", "worker_id": 1},
            {"receiptNumber": "R1002", "date": datetime(2024, 7, 2), "accountManager": "rob@nationalshowsystems.com", "showName": "Conference B", "showNumber": "1002", "details": "Catering", "net": 500.00, "hst": 65.00, "receipt_filename": "receipt_1002.pdf", "worker_id": 2},
            # Add more expenses as needed
        ]

        # Seed data for Shifts
        shifts_data = [
            {"start": datetime(2024, 7, 5, 10, 0), "end": datetime(2024, 7, 5, 18, 0), "showName": "Concert A", "showNumber": "1001", "accountManager": "rob@nationalshowsystems.com", "location": "Stadium A", "worker_id": 1},
            {"start": datetime(2024, 7, 6, 8, 0), "end": datetime(2024, 7, 6, 17, 0), "showName": "Conference B", "showNumber": "1002", "accountManager": "rob@nationalshowsystems.com", "location": "Convention Center B", "worker_id": 2},
            # Add more shifts as needed
        ]

    try:
        # Populate Workers
        for worker_data in workers_data:
            worker = Worker(**worker_data)
            db.session.add(worker)

        # Populate Events
        for event_data in events_data:
            event = Event(**event_data)
            db.session.add(event)

        # Populate Crews
        for crew_data in crews_data:
            crew = Crew(**crew_data)
            db.session.add(crew)

        # Populate CrewAssignments
        for crew_assignment_data in crew_assignments_data:
            crew_assignment = CrewAssignment(**crew_assignment_data)
            db.session.add(crew_assignment)

        # Populate Expenses
        for expense_data in expenses_data:
            expense = Expense(**expense_data)
            db.session.add(expense)

        # Populate Shifts
        for shift_data in shifts_data:
            shift = Shift(**shift_data)
            db.session.add(shift)

        db.session.commit()
        click.echo("Database populated successfully.")
    except Exception as e:
        db.session.rollback()
        click.echo(f"An error occurred while populating the database: {e}")

def register_commands(app):
    app.cli.add_command(populate_database)
