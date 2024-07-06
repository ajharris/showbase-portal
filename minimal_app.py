from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config.from_object('config.Config')
DATABASE_URL = app.config['SQLALCHEMY_DATABASE_URI']
db = SQLAlchemy(app)

@app.route('/')
def index():
    try:
        db.session.execute('SELECT 1')
        return "Database connection successful!"
    except Exception as e:
        return f"Error connecting to the database: {e}"

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])
