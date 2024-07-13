from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from ..models import Event, Crew, CrewAssignment, Note, Document
from ..forms import EventForm, CrewRequestForm, NoteForm, DocumentForm, SharePointForm
from .. import db
from .. utils import ROLES

events_bp = Blueprint('events', __name__, url_prefix='/events')

@events_bp.route('/create_event', methods=['GET', 'POST'])
@login_required
def create_event():
    form = EventForm()
    if form.validate_on_submit():
        event = Event(
            show_name=form.show_name.data,
            show_number=form.show_number.data,
            account_manager_id=form.account_manager.data,
            location_id=form.location.data,
            active=form.active.data
        )
        db.session.add(event)
        db.session.commit()
        flash('Event created successfully!', 'success')
        return redirect(url_for('events.create_event'))
    
    events = Event.query.all()
    return render_template('events/create_event.html', form=form, events=events)


@events_bp.route('/list_events')
@login_required
def list_events():
    events = Event.query.all()
    return render_template('events/events.html', events=events)

@events_bp.route('/activate_event/<int:event_id>')
@login_required
def activate_event(event_id):
    event = Event.query.get_or_404(event_id)
    event.active = True
    db.session.commit()
    flash('Event activated successfully.', 'success')
    return redirect(url_for('events.list_events'))

@events_bp.route('/inactivate_event/<int:event_id>')
@login_required
def inactivate_event(event_id):
    event = Event.query.get_or_404(event_id)
    event.active = False
    db.session.commit()
    flash('Event inactivated successfully.', 'success')
    return redirect(url_for('events.list_events'))

import logging
logger = logging.getLogger(__name__)

@events_bp.route('/view_event/<int:event_id>', methods=['GET', 'POST'])
@login_required
def view_event(event_id):
    event = Event.query.get_or_404(event_id)
    crew_request_form = CrewRequestForm()
    note_form = NoteForm()
    document_form = DocumentForm()
    sharepoint_form = SharePointForm()

    if request.method == 'POST':
        if crew_request_form.submit.data and crew_request_form.validate():
            roles_json = crew_request_form.roles_json.data
            try:
                crew = Crew(
                    event_id=event_id,
                    start_time=crew_request_form.start_time.data,
                    end_time=crew_request_form.end_time.data,
                    description=crew_request_form.description.data,
                    roles=roles_json,
                    shift_type=','.join(crew_request_form.shift_type.data)
                )
                db.session.add(crew)
                db.session.commit()
                flash('Crew request added successfully!', 'success')
                return redirect(url_for('events.view_event', event_id=event_id))
            except Exception as e:
                db.session.rollback()
                flash(f'Error: {str(e)}', 'danger')
                logger.error('Error while adding crew request: %s', e)
        elif note_form.submit.data and note_form.validate():
            note = Note(
                event_id=event_id,
                content=note_form.notes.data,
                account_manager_only=note_form.account_manager_only.data,
                account_manager_and_td_only=note_form.account_manager_and_td_only.data,
                worker_id=current_user.id
            )
            db.session.add(note)
            db.session.commit()
            flash('Note added successfully!', 'success')
            return redirect(url_for('events.view_event', event_id=event_id))
        elif document_form.submit.data and document_form.validate():
            # Handle document form submission
            pass
        elif sharepoint_form.submit.data and sharepoint_form.validate():
            event.sharepoint = sharepoint_form.sharepoint_link.data
            db.session.commit()
            flash('SharePoint link updated.', 'success')
            return redirect(url_for('events.view_event', event_id=event_id))

    crews = Crew.query.filter_by(event_id=event_id).all()
    logger.debug('Crews: %s', crews)
    crew_assignments = []
    for crew in crews:
        assignments = CrewAssignment.query.filter_by(crew_id=crew.id).all()
        logger.debug('Assignments for Crew %d: %s', crew.id, assignments)
        crew_assignments.append({
            'crew': crew,
            'assignments': assignments
        })

    return render_template(
        'events/view_event.html',
        event=event,
        crew_request_form=crew_request_form,
        note_form=note_form,
        document_form=document_form,
        sharepoint_form=sharepoint_form,
        crew_assignments=crew_assignments,
        ROLES=ROLES
    )


@events_bp.route('/events/delete_event/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    # Logic to delete event
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted successfully.', 'success')
    return redirect(url_for('events.list_events'))


@events_bp.route('/delete_crew/<int:crew_id>', methods=['POST'])
@login_required
def delete_crew(crew_id):
    crew = Crew.query.get_or_404(crew_id)
    event_id = crew.event_id
    db.session.delete(crew)
    db.session.commit()
    flash('Crew deleted successfully.', 'success')
    return redirect(url_for('events.view_event', event_id=event_id))
