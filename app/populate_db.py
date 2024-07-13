import click
import json
from datetime import datetime
from flask.cli import with_appcontext
from app import create_app, db
from app.models import Worker, Event, Crew, CrewAssignment, Expense, Shift, Note, Location

@click.command("populate-db")
@click.option('--json-file', type=click.Path(exists=True), help="Path to JSON file with seed data")
@with_appcontext
def populate_database(json_file):
    """Populate the database with sample data."""
    if not json_file:
        click.echo("Please provide a path to the JSON file with seed data using --json-file option.")
        return

    with open(json_file, 'r') as file:
        data = json.load(file)
        workers_data = data.get('workers', [])
        locations_data = data.get('locations', [])
        events_data = data.get('events', [])
        crews_data = data.get('crews', [])
        crew_assignments_data = data.get('crew_assignments', [])
        expenses_data = data.get('expenses', [])
        shifts_data = data.get('shifts', [])
        notes_data = data.get('notes', [])

    try:
        # Populate Workers
        for worker_data in workers_data:
            worker_data.pop('id', None)  # Remove 'id' to let the database auto-increment it
            worker = Worker(**worker_data)
            db.session.add(worker)

        db.session.commit()  # Commit workers to ensure foreign key references are valid

        # Populate Locations
        for location_data in locations_data:
            location_data.pop('id', None)  # Remove 'id' to let the database auto-increment it
            location = Location(**location_data)
            db.session.add(location)

        db.session.commit()  # Commit locations to ensure foreign key references are valid

        # Populate Events
        for event_data in events_data:
            event_data.pop('id', None)  # Remove 'id' to let the database auto-increment it
            event = Event(**event_data)
            db.session.add(event)

        db.session.commit()  # Commit events to ensure foreign key references are valid

        # Populate Crews
        for crew_data in crews_data:
            crew_data.pop('id', None)  # Remove 'id' to let the database auto-increment it
            crew_data['start_time'] = datetime.fromisoformat(crew_data['start_time'])
            crew_data['end_time'] = datetime.fromisoformat(crew_data['end_time'])
            crew = Crew(**crew_data)
            db.session.add(crew)

        db.session.commit()  # Commit crews to ensure foreign key references are valid

        # Populate CrewAssignments
        for crew_assignment_data in crew_assignments_data:
            crew_assignment_data.pop('id', None)  # Remove 'id' to let the database auto-increment it
            crew_assignment = CrewAssignment(**crew_assignment_data)
            db.session.add(crew_assignment)

        db.session.commit()  # Commit crew assignments to ensure foreign key references are valid

        # Populate Expenses
        for expense_data in expenses_data:
            expense_data.pop('id', None)  # Remove 'id' to let the database auto-increment it
            expense_data['date'] = datetime.fromisoformat(expense_data['date'])
            expense = Expense(**expense_data)
            db.session.add(expense)

        db.session.commit()  # Commit expenses to ensure foreign key references are valid

        # Populate Shifts
        for shift_data in shifts_data:
            shift_data.pop('id', None)  # Remove 'id' to let the database auto-increment it
            shift_data['start'] = datetime.fromisoformat(shift_data['start'])
            shift_data['end'] = datetime.fromisoformat(shift_data['end'])
            shift = Shift(**shift_data)
            db.session.add(shift)

        db.session.commit()  # Commit shifts to ensure foreign key references are valid

        # Populate Notes
        for note_data in notes_data:
            note_data.pop('id', None)  # Remove 'id' to let the database auto-increment it
            note_data['created_at'] = datetime.fromisoformat(note_data['created_at'])
            note = Note(**note_data)
            db.session.add(note)

        db.session.commit()  # Commit notes to ensure foreign key references are valid

        click.echo("Database populated successfully.")
    except Exception as e:
        db.session.rollback()
        click.echo(f"An error occurred while populating the database: {e}")

def register_commands(app):
    app.cli.add_command(populate_database)
