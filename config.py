import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

def fix_postgres_dialect(url):
    if url and url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url

DATABASE_URL = fix_postgres_dialect(os.getenv("DATABASE_URL"))

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set or is invalid")

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'pdf', 'jpeg', 'jpg', 'png'}
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('EMAIL_USER')
    MAIL_PASSWORD = os.getenv('EMAIL_PASS')
    MAIL_DEFAULT_SENDER = os.getenv('EMAIL_USER')
    DEBUG = True

# Test the database connection
import psycopg2
from psycopg2 import OperationalError

def test_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        print("Database connection successful:", cursor.fetchone())
        print("SQLALCHEMY_DATABASE_URI:", DATABASE_URL)
        conn.close()
    except OperationalError as e:
        print("Database connection failed:", e)

# test_db_connection()
