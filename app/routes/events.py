from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..models import Event, Shift, Expense, Crew, Worker, Note, CrewAssignment
from ..forms import NoteForm, DocumentForm, SharePointForm, CrewRequestForm, EventForm
from .. import db
from ..utils import ROLES, createEventReport
import logging, json

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

events_bp = Blueprint('events', __name__, url_prefix='/events')

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

    # Pre-fill roles in JSON format
    if request.method == 'GET':
        roles = {role: 0 for role in ROLES}  # Default value for each role
        crew_request_form.roles_json.data = json.dumps(roles)

    roles_dict = json.loads(crew_request_form.roles_json.data) if crew_request_form.roles_json.data else {}

    # Handle crew request form submission
    if crew_request_form.validate_on_submit():
        start_time = crew_request_form.start_time.data
        end_time = crew_request_form.end_time.data
        roles = json.loads(crew_request_form.roles_json.data)
        for role in roles:
            roles[role] = int(request.form.get(role, 1))  # Get the input value from the form
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

    # Handle note form submission
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

    # Get the list of notes, filtered by the current user's permissions
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

    return render_template('events/view_event.html', event=event, shifts=shifts, expenses=expenses, 
                           note_form=note_form, document_form=document_form, 
                           sharepoint_form=sharepoint_form, crew_request_form=crew_request_form, 
                           notes=notes, roles=roles_dict)

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
