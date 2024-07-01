from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required
from ..models import Event, Shift, Expense, Crew, Worker
from ..forms import NoteForm, DocumentForm, SharePointForm, CrewRequestForm, EventForm
from .. import db
from ..utils import ROLES, createEventReport

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

    # Populate roles field
    crew_request_form.roles.choices = [(role, role) for role in ROLES]

    if crew_request_form.validate_on_submit():
        start_time = crew_request_form.start_time.data
        end_time = crew_request_form.end_time.data
        roles = crew_request_form.roles.data
        shiftType = crew_request_form.shiftType.data

        new_crew = Crew(
            event_id=event.id,
            worker_id=crew_request_form.worker.data,
            start_time=start_time,
            end_time=end_time,
            shiftType=','.join(shiftType),  # Join shift types into a comma-separated string
            roles=','.join(roles)  # Join roles list into a comma-separated string
        )

        db.session.add(new_crew)
        db.session.commit()
        flash('Crew request added successfully.', 'success')
        return redirect(url_for('events.view_event', event_id=event.id))

    return render_template('events/view_event.html', event=event, shifts=shifts, expenses=expenses, 
                           note_form=note_form, document_form=document_form, 
                           sharepoint_form=sharepoint_form, crew_request_form=crew_request_form)

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
