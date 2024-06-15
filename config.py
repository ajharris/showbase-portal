import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', '987087412167751b8dd29e01872b1115889cabc8546afccb64c1862c9925abed')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data.sqlite')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'uploads/receipts'
    ALLOWED_EXTENSIONS = {'pdf', 'jpeg', 'jpg', 'png'}
    
    # Email settings
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('EMAIL_USER')
    MAIL_PASSWORD = os.environ.get('EMAIL_PASS')
    MAIL_DEFAULT_SENDER = os.environ.get('EMAIL_USER')
