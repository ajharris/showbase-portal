from flask import Flask, render_template, session, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import delete
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SubmitField, IntegerField, FloatField, SelectField, FileField
from wtforms.validators import DataRequired, InputRequired
from flask_wtf.file import FileAllowed
from flask_bootstrap import Bootstrap
from dotenv import load_dotenv
import os
from datetime import datetime
import pandas as pd
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename

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

# Ensure the upload directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

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
    date = DateField('Date:', id='expdatepick', format='%Y-%m-%d', validators=[InputRequired(), DataRequired()])
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
    date = db.Column(db.Date)
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
            date=session['date'],
            worker=session['worker'],
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
        return f'<Expense {self.showNumber} - {self.showName} - {self.worker}>'

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
        return f'<Shift {self.showNumber} - {self.showName} - {self.worker}>'

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
    shift = ShiftForm()
    report = createTimeReportCH()

    if shift.validate_on_submit():
        showNumber = shift.showNumber.data
        event = Event.query.filter_by(showNumber=showNumber).first()

        if event:
            session['worker'] = 'worker_name'  # Set the worker session variable appropriately
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
    expense_form = ExpenseForm()
    report = createExpenseReportCH()

    if expense_form.validate_on_submit():
        show_number = expense_form.showNumber.data
        event = Event.query.filter_by(showNumber=show_number).first()

        if event:
            receipt_file = expense_form.receipt.data
            if receipt_file and allowed_file(receipt_file.filename):
                filename = secure_filename(receipt_file.filename)
                receipt_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

 
                new_expense = Expense(
                    receiptNumber=expense_form.receiptNumber.data,
                    date=expense_form.date.data,
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
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# Report functions
def createTimeReportCH():
    # Function to create time report for Corporate Hospitality (stub)
    return "Time Report"

def createExpenseReportCH():
    # Function to create expense report for Corporate Hospitality (stub)
    return "Expense Report"

if __name__ == '__main__':
    app.run(debug=True)
