from flask import Flask, render_template, session, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import delete
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, FloatField, SelectField, FileField
from wtforms.validators import DataRequired, InputRequired
from flask_wtf.file import FileAllowed
from flask_bootstrap import Bootstrap
from dotenv import load_dotenv
import os
from datetime import datetime
import pandas as pd
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename

import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
bootstrap = Bootstrap(app)

# Configure database
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)

# Configure file upload settings
UPLOAD_FOLDER = 'uploads/receipts'
ALLOWED_EXTENSIONS = {'pdf', 'jpeg', 'jpg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Check if filename extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# List of account managers (you can customize this as needed)
accountManagersList = ['Rob Sandolowich', 'Joel Dubin', 'Corbin Elliott', 'Fox Procenko', 'Dave Lickers']

# Define Flask forms
class ShiftForm(FlaskForm):
    start = StringField('Shift Start:', id='startpick', validators=[InputRequired(), DataRequired()])
    end = StringField('Shift End:', id='endpick', validators=[InputRequired(), DataRequired()])
    showNumber = IntegerField('Event Number:', validators=[InputRequired(), DataRequired()])
    submit = SubmitField('Submit')

class ExpenseForm(FlaskForm):
    receiptNumber = IntegerField('Receipt Number:', validators=[InputRequired(), DataRequired()])
    date = StringField('Date:', id='expdatepick', validators=[InputRequired(), DataRequired()])
    showNumber = IntegerField('Event Number:', validators=[InputRequired(), DataRequired()])
    details = StringField('Expense Details:', validators=[InputRequired(), DataRequired()])
    net = FloatField('Subtotal:', validators=[InputRequired(), DataRequired()])
    hst = FloatField('HST:', validators=[InputRequired(), DataRequired()])
    receipt = FileField('Receipt', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'Images and PDFs only!')])
    submit = SubmitField('Submit')

class EventForm(FlaskForm):
    showName = StringField('Show Name:', validators=[InputRequired(), DataRequired()])
    showNumber = IntegerField('Show Number:', validators=[InputRequired(), DataRequired()])
    accountManager = SelectField('Account Manager:', choices=[], validators=[InputRequired(), DataRequired()])
    location = StringField('Location:', validators=[InputRequired(), DataRequired()])
    submit = SubmitField('Submit')

# Define database models
class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    showName = db.Column(db.String, nullable=False)
    showNumber = db.Column(db.Integer, unique=True, nullable=False)
    accountManager = db.Column(db.String)
    location = db.Column(db.String)

    def __repr__(self):
        return f'<Event {self.showName} - {self.showNumber} - {self.accountManager}>'

class Expense(db.Model):
    __tablename__ = 'expenses'
    id = db.Column(db.Integer, primary_key=True)
    receiptNumber = db.Column(db.Integer)
    date = db.Column(db.DateTime)
    accountManager = db.Column(db.String)
    showName = db.Column(db.String)
    showNumber = db.Column(db.Integer)
    details = db.Column(db.String)
    net = db.Column(db.Float)
    hst = db.Column(db.Float)
    receipt_filename = db.Column(db.String)

    def create(self):
        expense = Expense(
            receiptNumber=session['receiptNumber'],
            date=datetime.strptime(session['date'], '%m/%d/%Y'),
            accountManager=session['accountManager'],
            showName=session['showName'],
            showNumber=session['showNumber'],
            details=session['details'],
            net=session['net'],
            hst=session['hst'],
            receipt_filename=session['receipt_filename']
        )
        db.session.add(expense)
        db.session.commit()

    def __repr__(self):
        return f'<Expense {self.showNumber} - {self.showName} >'

class Shift(db.Model):
    __tablename__ = 'shifts'
    id = db.Column(db.Integer, primary_key=True)
    start = db.Column(db.DateTime)
    end = db.Column(db.DateTime)
    showName = db.Column(db.String)
    showNumber = db.Column(db.Integer)
    accountManager = db.Column(db.String)
    location = db.Column(db.String)

    def create(self):
        shift = Shift(
            start=datetime.strptime(session['start'], '%m/%d/%Y %I:%M %p'),
            end=datetime.strptime(session['end'], '%m/%d/%Y %I:%M %p'),
            showName=session['showName'],
            showNumber=session['showNumber'],
            accountManager=session['accountManager'],
            location=session['location']
        )
        db.session.add(shift)
        db.session.commit()

    def __repr__(self):
        return f'<Shift {self.showNumber} - {self.showName} >'

# Route for index page
@app.route('/')
def index():
    return render_template('index.html')

# Route for creating events
@app.route('/create_event', methods=['GET', 'POST'])
def create_event():
    form = EventForm()
    form.accountManager.choices = [(manager, manager) for manager in accountManagersList]

    if form.validate_on_submit():
        event = Event(
            showName=form.showName.data,
            showNumber=form.showNumber.data,
            accountManager=form.accountManager.data,
            location=form.location.data
        )
        db.session.add(event)
        db.session.commit()
        flash('Event created successfully!', 'success')
        return redirect(url_for('create_event'))
    return render_template('create_event.html', form=form)

# Route for timesheet
@app.route('/timesheet', methods=['GET', 'POST'])
def timesheet():
    report = createTimeReportCH()
    shift = ShiftForm()

    if shift.validate_on_submit():
        showNumber = shift.showNumber.data
        event = Event.query.filter_by(showNumber=showNumber).first()

        if event:
            session['start'] = shift.start.data
            session['end'] = shift.end.data
            session['showName'] = event.showName
            session['showNumber'] = showNumber
            session['accountManager'] = event.accountManager
            session['location'] = event.location

            shift_model = Shift()
            shift_model.create()

            return redirect(url_for('timesheet'))
        else:
            flash('Invalid Event Number', 'danger')

    return render_template('timesheet.html', shift=shift, report=report)

# Route for expenses
@app.route('/expenses', methods=['GET', 'POST'])
def expenses():
    report = createExpenseReportCH()
    expense_form = ExpenseForm()

    if expense_form.validate_on_submit():
        show_number = expense_form.showNumber.data
        event = Event.query.filter_by(showNumber=show_number).first()

        if event:
            # Handle file upload
            receipt_file = expense_form.receipt.data
            if receipt_file and allowed_file(receipt_file.filename):
                filename = secure_filename(receipt_file.filename)
                receipt_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                # Convert the date string to a datetime object
                date_str = expense_form.date.data
                logger.debug(f"Received date string: {date_str}")
                try:
                    date = datetime.strptime(date_str, '%Y-%m-%d')
                except ValueError:
                    flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
                    return render_template('expenses.html', expense_form=expense_form, report=report)

                # Create a new Expense object and populate its attributes
                new_expense = Expense(
                    receiptNumber=expense_form.receiptNumber.data,
                    date=date,
                    accountManager=event.accountManager,
                    showName=event.showName,
                    showNumber=show_number,
                    details=expense_form.details.data,
                    net=expense_form.net.data,
                    hst=expense_form.hst.data,
                    receipt_filename=filename
                )

                db.session.add(new_expense)
                db.session.commit()

                flash('Expense added successfully', 'success')
                return redirect(url_for('expenses'))
            else:
                flash('Invalid file format for receipt (PDF or JPEG required)', 'danger')
        else:
            flash('Invalid Event Number', 'danger')

    return render_template('expenses.html', expense_form=expense_form, report=report)

# Error handlers
# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# Shell context for easy database interaction in Flask shell
@app.shell_context_processor
def make_shell_context():
    return dict(db=db, Shift=Shift, Event=Event, Expense=Expense)

# Refresh timesheet display
@app.route('/refreshTimesheetDisplay')
def refresh_timesheet_display():
    report = createTimeReportCH()
    return render_template('timesheet.html', report=report)

# Refresh expense display
@app.route('/refreshExpenseDisplay')
def refresh_expense_display():
    report = createExpenseReportCH()
    return render_template('expenses.html', report=report)

### Reports ###

# Function to create time report
def createTimeReportCH():
    shifts = Shift.query.all()
    date = []
    show = []
    location = []
    times = []
    hours = []

    for shift in shifts:
        date.append(shift.start.date())
        show.append(f'{shift.showName}/{shift.showNumber}/{shift.accountManager}')
        location.append(shift.location)
        times.append(f'{shift.start.time()}/{shift.end.time()}')
        hours.append(float((shift.end - shift.start).total_seconds() / 3600))

    timesheet = pd.DataFrame({
        'Date': date,
        'Show': show,
        'Location': location,
        'Times': times,
        'Hours': hours
    })

    timesheet['Date'] = pd.to_datetime(timesheet['Date'], format='%Y-%m-%d')

    reportHTML = timesheet.to_html(index=False, classes='table table-striped table-hover')

    return reportHTML

# Function to create expense report
def createExpenseReportCH():
    expenses = Expense.query.all()
    date = []
    show = []
    location = []
    details = []
    total = []

    for expense in expenses:
        logger.debug(f"Processing expense: {expense}")
        if isinstance(expense.date, datetime):
            date_str = expense.date.strftime('%Y-%m-%d')
            date.append(date_str)
            logger.debug(f"Formatted date (datetime): {date_str}")
        elif isinstance(expense.date, str):
            date.append(expense.date)
            logger.debug(f"Date is already a string: {expense.date}")
        else:
            logger.error(f"Unexpected date format: {expense.date}")
            date.append('Invalid date')

        show.append(f'{expense.showName}/{expense.showNumber}/{expense.accountManager}')
        location.append(expense.location)
        details.append(expense.details)
        total.append(expense.net + expense.hst)

    expensereport = pd.DataFrame({
        'Date': date,
        'Show': show,
        'Location': location,
        'Details': details,
        'Total': total
    })

    logger.debug(f"Expense report DataFrame: {expensereport}")

    try:
        expensereport['Date'] = pd.to_datetime(expensereport['Date'], format='%Y-%m-%d')
    except Exception as e:
        logger.error(f"Error converting dates: {e}")

    reportHTML = expensereport.to_html(index=False, classes='table table-striped table-hover')

    return reportHTML

# Main entry point for the application
if __name__ == '__main__':
    app.run(debug=True)


