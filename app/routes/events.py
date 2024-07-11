import logging
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..models import Event, Location, Crew, Note, Document, Worker
from ..forms import NoteForm, DocumentForm, SharePointForm, CrewRequestForm, EventForm, LocationForm
from .. import db
from ..utils import get_account_managers, get_locations

logger = logging.getLogger(__name__)

events_bp = Blueprint('events', __name__, url_prefix='/events')

@events_bp.route('/events', methods=['GET'])
@login_required
def list_events():
    events = Event.query.all()
    return render_template('events/events.html', events=events)

@events_bp.route('/create_event', methods=['GET', 'POST'])
@login_required
def create_event():
    form = EventForm()
    if form.validate_on_submit():
        show_name = form.show_name.data
        show_number = form.show_number.data
        account_manager_id = form.account_manager.data
        location_id = form.location.data
        sharepoint = form.sharepoint.data
        active = form.active.data

        event = Event(
            show_name=show_name,
            show_number=show_number,
            account_manager_id=account_manager_id,
            location_id=location_id,
            sharepoint=sharepoint,
            active=active
        )

        db.session.add(event)
        db.session.commit()
        flash('Event created successfully', 'success')
        return redirect(url_for('events.create_event'))

    return render_template('events/create_event.html', form=form)

@events_bp.route('/locations/add', methods=['GET', 'POST'])
@login_required
def add_location():
    form = LocationForm()
    if form.validate_on_submit():
        location = Location(
            name=form.name.data,
            address=form.address.data,
            loading_notes=form.loading_notes.data,
            dress_code=form.dress_code.data,
            other_info=form.other_info.data
        )

        db.session.add(location)
        db.session.commit()
        flash('Location added successfully', 'success')
        return redirect(url_for('events.add_location'))

    return render_template('events/add_location.html', form=form)

@events_bp.route('/locations/edit/<int:location_id>', methods=['GET', 'POST'])
@login_required
def edit_location(location_id):
    location = Location.query.get_or_404(location_id)
    form = LocationForm(obj=location)
    
    if form.validate_on_submit():
        form.populate_obj(location)
        db.session.commit()
        flash('Location updated successfully.', 'success')
        return redirect(url_for('events.edit_location', location_id=location_id))

    return render_template('events/edit_location.html', form=form, location=location)



