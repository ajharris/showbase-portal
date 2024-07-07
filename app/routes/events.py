from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from ..models import Event, Shift, Expense, Crew, Worker, Note, CrewAssignment
from ..forms import NoteForm, DocumentForm, SharePointForm, CrewRequestForm, EventForm
from .. import db
from ..utils import ROLES, createEventReport
from sqlalchemy.exc import IntegrityError  # Import IntegrityError
import json

events_bp = Blueprint('events', __name__, url_prefix='/events')

@events_bp.route('/create_event', methods=['GET', 'POST'])
@login_required
def create_event():
    event_form = EventForm()
    if event_form.validate_on_submit():
        # Check if an event with the same showNumber already exists
        show_number = event_form.showNumber.data
        existing_event = Event.query.filter_by(showNumber=show_number).first()
        if existing_event:
            flash('An event with this show number already exists. Please use a different show number.', 'danger')
            return redirect(url_for('events.create_event'))

        event = Event(
            showName=event_form.showName.data,
            showNumber=event_form.showNumber.data,
            accountManager=event_form.accountManager.data,
            location=event_form.location.data,
            active=True
        )
        db.session.add(event)
        try:
            db.session.commit()
            flash('Event created successfully!', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('An error occurred while creating the event. Please try again.', 'danger')
        return redirect(url_for('events.create_event'))  # Redirect to the same view to refresh the form

    event_report = createEventReport()  # Generate the event report
    return render_template('events/create_event.html', event_form=event_form, event_report=event_report)

@events_bp.route('/')
@login_required
def events():
    event_report = createEventReport()
    return render_template('events/events.html', event_report=event_report)

@events_bp.route('/view_event/<int:event_id>', methods=['GET', 'POST'])
@login_required
def view_event(event_id):
    event = Event.query.get_or_404(event_id)
    crew_request_form = CrewRequestForm()
    note_form = NoteForm()
    document_form = DocumentForm()
    sharepoint_form = SharePointForm()

    # Example of how to handle form submissions (you need to add the logic here)
    if crew_request_form.validate_on_submit():
        # Handle the crew request form submission
        pass
    if note_form.validate_on_submit():
        # Handle the note form submission
        pass
    if document_form.validate_on_submit():
        # Handle the document form submission
        pass
    if sharepoint_form.validate_on_submit():
        # Handle the SharePoint form submission
        pass

    # Mock data for roles and crew assignments for demonstration purposes
    roles = {role: 0 for role in ROLES}  # Replace with actual data logic
    crew_assignments = {}  # Replace with actual data logic

    return render_template('events/view_event.html', event=event, crew_request_form=crew_request_form, note_form=note_form, document_form=document_form, sharepoint_form=sharepoint_form, roles=roles, crew_assignments=crew_assignments)

@events_bp.route('/delete_crew/<int:crew_id>', methods=['POST'])
@login_required
def delete_crew(crew_id):
    crew = Crew.query.get_or_404(crew_id)
    db.session.delete(crew)
    db.session.commit()
    flash('Crew assignment deleted successfully.', 'success')
    return redirect(url_for('events.view_event', event_id=crew.event_id))

@events_bp.route('/events/edit/<int:event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    form = EventForm(obj=event)

    if form.validate_on_submit():
        form.populate_obj(event)
        db.session.commit()
        flash('Event updated successfully!', 'success')
        return redirect(url_for('events.view_event', event_id=event.id))

    return render_template('events/edit_event.html', form=form, event=event)

@events_bp.route('/events/delete/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted successfully.', 'success')
    return redirect(url_for('events.create_event'))
