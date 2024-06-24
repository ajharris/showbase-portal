from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, FloatField, SelectField, FileField, PasswordField
from wtforms.validators import DataRequired, InputRequired, Optional, Email, EqualTo
from flask_wtf.file import FileAllowed

class UpdateWorkerForm(FlaskForm):
    first_name = StringField('First Name', validators=[InputRequired(), DataRequired()])
    last_name = StringField('Last Name', validators=[InputRequired(), DataRequired()])
    email = StringField('Email', validators=[InputRequired(), DataRequired(), Email()])
    phone_number = StringField('Phone Number', validators=[Optional()])
    submit = SubmitField('Update')

class AdminUpdateWorkerForm(UpdateWorkerForm):
    is_admin = SelectField('Admin', choices=[(1, 'Yes'), (0, 'No')], coerce=int, validators=[Optional()])
    is_account_manager = SelectField('Account Manager', choices=[(1, 'Yes'), (0, 'No')], coerce=int, validators=[Optional()])

class ShiftForm(FlaskForm):
    start = StringField('Shift Start:', id='startpick', validators=[InputRequired(), DataRequired()])
    end = StringField('Shift End:', id='endpick', validators=[InputRequired(), DataRequired()])
    showNumber = IntegerField('Event Number:', validators=[InputRequired(), DataRequired()])
    worker = SelectField('Worker:', coerce=int, validators=[InputRequired(), DataRequired()])  # New field
    submit = SubmitField('Submit')

class ExpenseForm(FlaskForm):
    receiptNumber = IntegerField('Receipt Number:', validators=[InputRequired(), DataRequired()])
    date = StringField('Date:', id='expdatepick', validators=[InputRequired(), DataRequired()])
    showNumber = IntegerField('Event Number:', validators=[InputRequired(), DataRequired()])
    details = StringField('Expense Details:', validators=[InputRequired(), DataRequired()])
    net = FloatField('Subtotal:', validators=[InputRequired(), DataRequired()])
    hst = FloatField('HST:', validators=[InputRequired(), DataRequired()])
    receipt = FileField('Receipt', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'Images and PDFs only!')])
    worker = SelectField('Worker:', coerce=int, validators=[InputRequired(), DataRequired()])  # New field
    submit = SubmitField('Submit')

class EventForm(FlaskForm):
    showName = StringField('Show Name:', validators=[InputRequired(), DataRequired()])
    showNumber = IntegerField('Show Number:', validators=[InputRequired(), DataRequired()])
    accountManager = SelectField('Account Manager:', choices=[], validators=[InputRequired(), DataRequired()])
    location = StringField('Location:', validators=[InputRequired(), DataRequired()])
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
    first_name = StringField('First Name', validators=[InputRequired(), DataRequired()])
    last_name = StringField('Last Name', validators=[InputRequired(), DataRequired()])
    email = StringField('Email', validators=[InputRequired(), DataRequired(), Email()])
    phone_number = StringField('Phone Number', validators=[Optional()])  # Optional phone number field
    password = PasswordField('Password', validators=[InputRequired(), DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[InputRequired(), DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')
