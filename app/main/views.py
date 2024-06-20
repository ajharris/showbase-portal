from . import main
from flask import render_template, session, redirect, url_for
from .forms import ShiftForm
from .. import db
from ..models import Worker



@main.route('/')
def index():
    return render_template('index.html')
@main.route('/timesheet', methods=['GET', 'POST'])
def timesheet():
    shift = ShiftForm()
    if shift.validate_on_submit():
        worker = Worker.query.filter_by(worker=shift.worker.data)
        session['start'] = shift.start.data
        session['end'] = shift.end.data
        session['eventName'] = shift.eventName.data
        session['showNumber'] = shift.showNumber.data
        session['accountManager'] = shift.accountManager.data
        session['location'] = shift.location.data
        return redirect(url_for('.timesheet'))
    return render_template('timesheet.html', shift=shift)