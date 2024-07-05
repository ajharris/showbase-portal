# routes/events.py

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..models import Event, Shift, Expense, Crew, Worker, Note, CrewAssignment
from ..forms import NoteForm, DocumentForm, SharePointForm, CrewRequestForm, EventForm
from .. import db
from ..utils import ROLES, createEventReport
import json

events_bp = Blueprint('events', __name__, url_prefix='/events')

# events.py

@events_bp.route('/<int:event_id>', methods=['GET', 'POST'])
@login_required
def view_event(event_id):
    event = Event.query.get_or_404(event_id)
    shifts = Shift.query.filter_by(showNumber=event.showNumber).all()
    expenses = Expense.query.filter_by(showNumber=event.showNumber).all()

    note_form = NoteForm()
    document_form = DocumentForm()
    sharepoint_form = SharePointForm()
    crew_request_form = CrewRequestForm()

    if request.method == 'GET':
        roles = {role: 0 for role in ROLES}
        crew_request_form.roles_json.data = json.dumps(roles)

    roles_dict = json.loads(crew_request_form.roles_json.data) if crew_request_form.roles_json.data else {}

    if crew_request_form.validate_on_submit():
        start_time = crew_request_form.start_time.data
        end_time = crew_request_form.end_time.data
        roles = json.loads(crew_request_form.roles_json.data)
        for role in roles:
            roles[role] = int(request.form.get(role, 0))
        shiftType = crew_request_form.shiftType.data
        description = crew_request_form.description.data

        new_crew = Crew(
            event_id=event.id,
            start_time=start_time,
            end_time=end_time,
            roles=json.dumps(roles),
            shift_type=",".join(shiftType),
            description=description
        )

        db.session.add(new_crew)
        db.session.commit()
        flash('Crew request added successfully.', 'success')
        return redirect(url_for('events.view_event', event_id=event.id))

    if note_form.validate_on_submit():
        new_note = Note(
            content=note_form.notes.data,
            worker_id=current_user.id,
            event_id=event.id,
            account_manager_only=note_form.account_manager_only.data,
            account_manager_and_td_only=note_form.account_manager_and_td_only.data
        )
        db.session.add(new_note)
        db.session.commit()
        flash('Note added successfully.', 'success')
        return redirect(url_for('events.view_event', event_id=event.id))

    notes_query = Note.query.filter_by(event_id=event.id)
    if current_user.is_admin:
        notes = notes_query.all()
    elif current_user.is_account_manager:
        notes = notes_query.filter(
            (Note.account_manager_only == False) | 
            (Note.account_manager_only == True)
        ).all()
    else:
        worker_ids = [assignment.worker_id for assignment in CrewAssignment.query.join(Crew).filter(Crew.event_id == event.id).all()]
        if current_user.id in worker_ids:
            notes = notes_query.filter(
                (Note.account_manager_and_td_only == False) |
                ((Note.account_manager_and_td_only == True) & (current_user.id in worker_ids))
            ).all()
        else:
            notes = notes_query.filter_by(account_manager_only=False, account_manager_and_td_only=False).all()

    crews = Crew.query.filter_by(event_id=event.id).all()
    crew_assignments = {}
    for crew in crews:
        requested_roles = json.loads(crew.roles)
        assignments = CrewAssignment.query.filter_by(crew_id=crew.id).all()
        assignment_data = {role: {'name': 'Not Yet Assigned', 'phone': '', 'email': ''} for role in requested_roles if requested_roles[role] > 0}
        for assignment in assignments:
            worker = Worker.query.get(assignment.worker_id)
            if worker:
                assignment_data[assignment.role] = {
                    'name': f'{worker.first_name} {worker.last_name}',
                    'phone': worker.phone_number,
                    'email': worker.email
                }
        crew_assignments[crew.id] = {
            'description': crew.description,
            'start_time': crew.start_time,
            'end_time': crew.end_time,
            'shift_type': crew.shift_type,
            'assignments': assignment_data
        }

    return render_template('events/view_event.html', event=event, shifts=shifts, expenses=expenses, 
                           note_form=note_form, document_form=document_form, 
                           sharepoint_form=sharepoint_form, crew_request_form=crew_request_form, 
                           notes=notes, roles=roles_dict, crew_assignments=crew_assignments)

@events_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_event():
    form = EventForm()
    form.accountManager.choices = [(manager.email, f"{manager.first_name} {manager.last_name}") for manager in Worker.query.filter_by(is_account_manager=True).all()]
    event_report = createEventReport()

    if form.validate_on_submit():
        existing_event = Event.query.filter_by(showNumber=form.showNumber.data).first()
        if existing_event:
            flash('An event with this Show Number already exists.', 'danger')
        else:
            event = Event(
                showName=form.showName.data,
                showNumber=form.showNumber.data,
                accountManager=form.accountManager.data,
                location=form.location.data
            )
            db.session.add(event)
            db.session.commit()
            flash('Event created successfully!', 'success')
            return redirect(url_for('events.create_event'))

    return render_template('events/create_event.html', event_form=form, event_report=event_report)

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
