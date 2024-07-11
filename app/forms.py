import logging
from flask import redirect, url_for, render_template, flash
from flask_wtf import FlaskForm
from wtforms import (
    StringField, SubmitField, IntegerField, FloatField, SelectField, FileField, 
    PasswordField, DateTimeField, BooleanField, SelectMultipleField, TextAreaField, 
    HiddenField
)
from wtforms.validators import DataRequired, InputRequired, Optional, Email, EqualTo, URL
from flask_wtf.file import FileAllowed
from wtforms.widgets import ListWidget, CheckboxInput
from .models import Worker
from .utils import ROLES, get_account_managers, get_locations
from app import db

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class CSRFForm(FlaskForm):
    pass

class DynamicChoicesForm(FlaskForm):
    def update_choices(self, field_name, choices):
        getattr(self, field_name).choices = choices

class CrewRequestForm(DynamicChoicesForm):
    start_time = DateTimeField('Start Date & Time', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    end_time = DateTimeField('End Date & Time', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    roles_json = HiddenField('Roles JSON', validators=[DataRequired()])
    shift_type = SelectMultipleField('Shift Type', choices=[('Setup', 'Setup'), ('Show', 'Show'), ('Strike', 'Strike')], option_widget=CheckboxInput(), widget=ListWidget(prefix_label=False))
    submit = SubmitField('Add Crew Request')


class EventForm(DynamicChoicesForm):
    show_name = StringField('Show Name:', validators=[InputRequired(), DataRequired()])
    show_number = IntegerField('Show Number:', validators=[InputRequired(), DataRequired()])
    account_manager = SelectField('Account Manager:', choices=[], validators=[InputRequired(), DataRequired()])
    location = SelectField('Location:', choices=[], validators=[InputRequired(), DataRequired()])
    sharepoint = StringField('SharePoint Link:')
    active = BooleanField('Active', default=True)
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_choices('account_manager', [(am.id, f'{am.first_name} {am.last_name}') for am in get_account_managers()])
        self.update_choices('location', [(loc.id, loc.name) for loc in get_locations()])

class LocationForm(FlaskForm):
    name = StringField('Location Name', validators=[DataRequired()])
    address = TextAreaField('Address', validators=[DataRequired()])
    loading_notes = TextAreaField('Loading Notes')
    dress_code = TextAreaField('Dress Code')
    other_info = TextAreaField('Other Information')
    submit = SubmitField('Save')

class AdminCreateWorkerForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone_number = StringField('Phone Number')
    temp_password = PasswordField('Temporary Password', validators=[DataRequired(), EqualTo('confirm_temp_password', message='Passwords must match')])
    confirm_temp_password = PasswordField('Confirm Temporary Password', validators=[DataRequired()])
    is_admin = BooleanField('Admin')
    is_account_manager = BooleanField('Account Manager')
    submit = SubmitField('Create Worker')

class ChangePasswordForm(FlaskForm):
    new_password = PasswordField('New Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')

class UpdatePasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('New Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Update Password')

class UpdateProfileForm(DynamicChoicesForm):
    worker_select = SelectField('Select Worker', choices=[], coerce=int)
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone_number = StringField('Phone Number')
    is_admin = BooleanField('Admin')
    is_account_manager = BooleanField('Account Manager')
    submit = SubmitField('Update')

    def __init__(self, view_as_employee=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if view_as_employee:
            del self.is_admin
            del self.is_account_manager
            del self.worker_select
        else:
            self.update_choices('worker_select', [(worker.id, f'{worker.first_name} {worker.last_name}') for worker in Worker.query.all()])

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

class ShiftForm(DynamicChoicesForm):
    start = StringField('Shift Start:', id='shift_start', validators=[InputRequired(), DataRequired()])
    end = StringField('Shift End:', id='shift_end', validators=[InputRequired(), DataRequired()])
    show_number = IntegerField('Show Number:', validators=[InputRequired(), DataRequired()])
    worker = SelectField('Worker:', coerce=int, validators=[InputRequired(), DataRequired()])
    roles = SelectMultipleField('Roles:', choices=[(role, role) for role in ROLES], validators=[InputRequired(), DataRequired()])
    location = SelectField('Location:', choices=[], validators=[InputRequired(), DataRequired()])
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_choices('location', [(loc.id, loc.name) for loc in get_locations()])

class ExpenseForm(DynamicChoicesForm):
    receipt_number = IntegerField('Receipt Number:', validators=[InputRequired(), DataRequired()])
    date = StringField('Date:', id='expdatepick', validators=[InputRequired(), DataRequired()])
    show_number = IntegerField('Event Number:', validators=[InputRequired(), DataRequired()])
    details = StringField('Expense Details:', validators=[InputRequired(), DataRequired()])
    net = FloatField('Subtotal:', validators=[InputRequired(), DataRequired()])
    hst = FloatField('HST:', validators=[InputRequired(), DataRequired()])
    receipt = FileField('Receipt', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'Images and PDFs only!')])
    worker = SelectField('Worker:', coerce=int, validators=[InputRequired(), DataRequired()])
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_choices('worker', [(worker.id, f'{worker.first_name} {worker.last_name}') for worker in Worker.query.all()])

class NoteForm(FlaskForm):
    notes = TextAreaField('Note Content', validators=[DataRequired()])
    account_manager_only = BooleanField('Visible to Account Managers Only')
    account_manager_and_td_only = BooleanField('Visible to Account Managers and TDs Only')
    submit = SubmitField('Add Note')

class DocumentForm(FlaskForm):
    document = FileField('Upload Document', validators=[FileAllowed(['pdf', 'jpeg', 'jpg', 'png', 'docx', 'xlsx'], 'Documents only!')])
    submit = SubmitField('Upload Document')

class SharePointForm(FlaskForm):
    sharepoint_link = StringField('SharePoint Link', validators=[DataRequired(), URL()])
    submit = SubmitField('Update Link')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), DataRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired(), DataRequired()])
    remember = BooleanField('Remember Me')
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

class AssignWorkerForm(DynamicChoicesForm):
    worker = SelectField('Select Worker', choices=[], coerce=int, validators=[DataRequired()])
    role = StringField('Role', validators=[DataRequired()])
    crew_id = HiddenField('Crew ID', validators=[DataRequired()])
    submit = SubmitField('Assign Worker')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_choices('worker', [(worker.id, f'{worker.first_name} {worker.last_name}') for worker in Worker.query.all()])
