import os

def fix_postgres_dialect(url):
    if url and url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url

SQLALCHEMY_DATABASE_URI = fix_postgres_dialect(os.getenv("SQLALCHEMY_DATABASE_URI"))

if not SQLALCHEMY_DATABASE_URI:
    raise ValueError("SQLALCHEMY_DATABASE_URI environment variable is not set or is invalid")

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')  # Provide a default for SECRET_KEY
    
    # Use the fixed SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'uploads/receipts'
    ALLOWED_EXTENSIONS = {'pdf', 'jpeg', 'jpg', 'png'}
    
    # Email settings
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('EMAIL_USER')
    MAIL_PASSWORD = os.getenv('EMAIL_PASS')
    MAIL_DEFAULT_SENDER = os.getenv('EMAIL_USER')
