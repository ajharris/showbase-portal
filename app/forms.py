from flask import redirect, url_for, render_template, flash
from flask_wtf import FlaskForm
from wtforms import FormField, TextAreaField, HiddenField, FieldList, StringField, SubmitField, IntegerField, FloatField, SelectField, FileField, PasswordField, DateTimeField, BooleanField, SelectMultipleField
from wtforms.validators import DataRequired, InputRequired, Optional, Email, EqualTo, URL
from flask_wtf.file import FileAllowed
from wtforms.widgets import ListWidget, CheckboxInput
from .models import Worker
from .utils import ROLES, get_account_managers
from app import db

from flask_wtf import FlaskForm
from wtforms import (
    StringField, SubmitField, IntegerField, DateTimeField, FieldList, FormField, SelectMultipleField
)
from wtforms.validators import DataRequired, InputRequired
from wtforms.widgets import CheckboxInput, ListWidget
from .models import Worker
from .utils import ROLES
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class CrewRequestForm(FlaskForm):
    start_time = DateTimeField('Start Date & Time', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    end_time = DateTimeField('End Date & Time', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    roles_json = HiddenField('Roles JSON', validators=[DataRequired()])
    shiftType = SelectMultipleField('Shift Type', choices=[('setup', 'Setup'), ('show', 'Show'), ('strike', 'Strike')], option_widget=CheckboxInput(), widget=ListWidget(prefix_label=False))
    submit = SubmitField('Add Crew Request')



class EventForm(FlaskForm):
    showName = StringField('Show Name:', validators=[InputRequired(), DataRequired()])
    showNumber = IntegerField('Show Number:', validators=[InputRequired(), DataRequired()])
    accountManager = SelectField('Account Manager:', choices=[], validators=[InputRequired(), DataRequired()])
    location = StringField('Location:', validators=[InputRequired(), DataRequired()])
    sharepoint = StringField('SharePoint Link:', validators=[URL()])
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)
        self.accountManager.choices = [(am.id, f'{am.first_name} {am.last_name}') for am in get_account_managers()]

class AdminCreateWorkerForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    is_admin = SelectField('Admin', choices=[(1, 'Yes'), (0, 'No')], default=0, coerce=int, validators=[InputRequired()])
    is_account_manager = SelectField('Account Manager', choices=[(1, 'Yes'), (0, 'No')], default=0, coerce=int, validators=[InputRequired()])
    submit = SubmitField('Create Worker')

class UpdatePasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('New Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Update Password')

class UpdateProfileForm(FlaskForm):
    worker_select = SelectField('Select Worker', choices=[], coerce=int)
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone_number = StringField('Phone Number')
    is_admin = BooleanField('Admin')
    is_account_manager = BooleanField('Account Manager')
    submit = SubmitField('Update')

    def __init__(self, view_as_employee=False, *args, **kwargs):
        super(UpdateProfileForm, self).__init__(*args, **kwargs)
        if view_as_employee:
            del self.is_admin
            del self.is_account_manager
            del self.worker_select
        else:
            self.worker_select.choices = [(worker.id, f'{worker.first_name} {worker.last_name}') for worker in Worker.query.all()]

class AdminUpdateProfileForm(UpdateProfileForm):
    is_admin = SelectField('Admin', choices=[(1, 'Yes'), (0, 'No')], coerce=int, validators=[Optional()])
    is_account_manager = SelectField('Account Manager', choices=[(1, 'Yes'), (0, 'No')], coerce=int, validators=[Optional()])

class AdminUpdateWorkerForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone_number = StringField('Phone Number')
    is_admin = BooleanField('Admin')
    is_account_manager = BooleanField('Account Manager')
    active = BooleanField('Active')
    submit = SubmitField('Update')

def update_worker(worker_id):
    worker = Worker.query.get_or_404(worker_id)
    form = AdminUpdateWorkerForm(obj=worker)
    if form.validate_on_submit():
        form.populate_obj(worker)
        db.session.commit()
        flash('Worker updated successfully.', 'success')
        return redirect(url_for('admin.manage_workers'))
    return render_template('admin/update_worker.html', form=form)

class ShiftForm(FlaskForm):
    start = StringField('Shift Start:', id='startpick', validators=[InputRequired(), DataRequired()])
    end = StringField('Shift End:', id='endpick', validators=[InputRequired(), DataRequired()])
    showNumber = IntegerField('Event Number:', validators=[InputRequired(), DataRequired()])
    worker = SelectField('Worker:', coerce=int, validators=[InputRequired(), DataRequired()])
    roles = SelectMultipleField('Roles:', choices=[(role, role) for role in ROLES], validators=[InputRequired(), DataRequired()])
    location = StringField('Location:', validators=[InputRequired(), DataRequired()])
    submit = SubmitField('Submit')

class ExpenseForm(FlaskForm):
    receiptNumber = IntegerField('Receipt Number:', validators=[InputRequired(), DataRequired()])
    date = StringField('Date:', id='expdatepick', validators=[InputRequired(), DataRequired()])
    showNumber = IntegerField('Event Number:', validators=[InputRequired(), DataRequired()])
    details = StringField('Expense Details:', validators=[InputRequired(), DataRequired()])
    net = FloatField('Subtotal:', validators=[InputRequired(), DataRequired()])
    hst = FloatField('HST:', validators=[InputRequired(), DataRequired()])
    receipt = FileField('Receipt', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'Images and PDFs only!')])
    worker = SelectField('Worker:', coerce=int, validators=[InputRequired(), DataRequired()])
    submit = SubmitField('Submit')

class NoteForm(FlaskForm):
    notes = StringField('Notes', validators=[DataRequired()])
    submit = SubmitField('Add Notes')

class DocumentForm(FlaskForm):
    document = FileField('Upload Document', validators=[FileAllowed(['pdf', 'jpeg', 'jpg', 'png', 'docx', 'xlsx'], 'Documents only!')])
    submit = SubmitField('Upload Document')

class SharePointForm(FlaskForm):
    sharepoint_link = StringField('SharePoint Link', validators=[DataRequired()])
    submit = SubmitField('Add Link')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), DataRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired(), DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone_number = StringField('Phone Number', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class RequestResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

class NoteForm(FlaskForm):
    notes = TextAreaField('Note Content', validators=[DataRequired()])
    account_manager_only = BooleanField('Visible to Account Managers Only')
    account_manager_and_td_only = BooleanField('Visible to Account Managers and TDs Only')
    submit = SubmitField('Add Note')