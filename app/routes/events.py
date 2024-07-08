# app/routes/events.py

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..models import Event, Crew, Note, Document
from ..forms import NoteForm, DocumentForm, SharePointForm, CrewRequestForm, EventForm
from .. import db
from ..utils import ROLES, createEventReport

events_bp = Blueprint('events', __name__, url_prefix='/events')

@events_bp.route('/create_event', methods=['GET', 'POST'])
@login_required
def create_event():
    event_form = EventForm()
    if event_form.validate_on_submit():
        event = Event(
            showName=event_form.showName.data,
            showNumber=event_form.showNumber.data,
            accountManager=event_form.accountManager.data,
            location=event_form.location.data,
            active=True
        )
        db.session.add(event)
        db.session.commit()
        flash('Event created successfully!', 'success')
        return redirect(url_for('events.create_event'))  # Redirect to the same view to refresh the form

    event_report = createEventReport()  # Generate the event report
    return render_template('events/create_event.html', event_form=event_form, event_report=event_report)

@events_bp.route('/')
@login_required
def events():
    event_report = createEventReport()
    return render_template('events/events.html', event_report=event_report)

@events_bp.route('/delete_crew/<int:crew_id>', methods=['POST'])
@login_required
def delete_crew(crew_id):
    crew = Crew.query.get_or_404(crew_id)
    db.session.delete(crew)
    db.session.commit()
    flash('Crew assignment deleted successfully.', 'success')
    return redirect(url_for('events.view_event', event_id=crew.event_id))

@events_bp.route('/edit_event/<int:event_id>', methods=['GET', 'POST'])
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    form = EventForm(obj=event)

    if form.validate_on_submit():
        form.populate_obj(event)
        db.session.commit()
        flash('Event updated successfully!', 'success')
        return redirect(url_for('events.view_event', event_id=event.id))

    return render_template('events/edit_event.html', form=form, event=event)

@events_bp.route('/delete_event/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted successfully.', 'success')
    return redirect(url_for('events.index'))

@events_bp.route('/view_event/<int:event_id>', methods=['GET', 'POST'])
@login_required
def view_event(event_id):
    event = Event.query.get_or_404(event_id)
    crew_request_form = CrewRequestForm()
    note_form = NoteForm()
    document_form = DocumentForm()
    sharepoint_form = SharePointForm()

    if crew_request_form.validate_on_submit():
        return redirect(url_for('events.request_crew', event_id=event.id))

    if note_form.validate_on_submit():
        note = Note(
            content=note_form.notes.data,
            event_id=event.id,
            worker_id=current_user.id,
            account_manager_only=note_form.account_manager_only.data,
            account_manager_and_td_only=note_form.account_manager_and_td_only.data
        )
        db.session.add(note)
        db.session.commit()
        flash('Note added successfully.', 'success')
        return redirect(url_for('events.view_event', event_id=event.id))

    if document_form.validate_on_submit():
        # Handle document form submission
        flash('Document uploaded successfully.', 'success')
        return redirect(url_for('events.view_event', event_id=event.id))

    if sharepoint_form.validate_on_submit():
        # Handle SharePoint form submission
        flash('SharePoint link added successfully.', 'success')
        return redirect(url_for('events.view_event', event_id=event.id))

    # Fetch crew assignments related to the event
    crew_assignments = []
    for crew in event.crews:
        assignments = {
            "description": crew.description,
            "start_time": crew.start_time,
            "end_time": crew.end_time,
            "shift_type": crew.shift_type,
            "assignments": []
        }
        for assignment in crew.crew_assignments:
            worker = assignment.worker if assignment.worker else None
            assignments["assignments"].append({
                "role": assignment.role,
                "worker": worker,
                "worker_name": f"{worker.first_name} {worker.last_name}" if worker else "Not Yet Assigned",
                "worker_phone": worker.phone_number if worker else "N/A",
                "worker_email": worker.email if worker else "N/A"
            })
        crew_assignments.append(assignments)

    roles = {role: 0 for role in ROLES}  # Initialize roles with 0 counts

    return render_template('events/view_event.html', event=event, crew_request_form=crew_request_form,
                           note_form=note_form, document_form=document_form, sharepoint_form=sharepoint_form,
                           crew_assignments=crew_assignments, roles=roles)
