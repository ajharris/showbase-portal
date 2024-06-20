from flask_wtf import FlaskForm
from wtforms import StringField, DateTimeField, SubmitField, IntegerField, RadioField, SelectField
from wtforms.validators import DataRequired, InputRequired

accountManagersList = ['Rob Sandolowich', 'Joel Dubin', 'Corbin Elliott', 'Fox Procenko', 'Dave Lickers']

class ShiftForm(FlaskForm):
    # Date, Event Name, #, Account Manager, Location, Time In, Time Out, Number of Hours
    worker = StringField('Worker Name: ', validators=([InputRequired(), DataRequired()]))
    start = StringField('Shift Start: ', id='startpick', validators=([InputRequired(), DataRequired()]))
    end = StringField('Shift End: ', id='endpick', validators=([InputRequired(), DataRequired()]))
    eventName = StringField('Event Name: ', validators=([InputRequired(), DataRequired()]))
    showNumber = IntegerField('Show Number: ', validators=([InputRequired(), DataRequired()]))
    accountManager = SelectField('Account Manager: ', validators=([InputRequired(), DataRequired()]), choices=accountManagersList)
    location = StringField('Location: ', validators=([InputRequired(), DataRequired()]))

    submit = SubmitField('Submit')