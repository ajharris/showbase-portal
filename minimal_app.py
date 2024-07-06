from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

@app.route('/')
def index():
    try:
        db.session.execute('SELECT 1')
        return "Database connection successful!"
    except Exception as e:
        return f"Error connecting to the database: {e}"

if __name__ == '__main__':
    app.run(debug=True)
