from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_mail import Mail
from dotenv import load_dotenv
import logging
import os

# Load environment variables from .env file
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
bootstrap = Bootstrap()
login_manager = LoginManager()
mail = Mail()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_app(config_class='config.Config'):
    """
    Factory function to create and configure the Flask application.
    
    :param config_class: The configuration class to use for the application.
    :return: The configured Flask application.
    """
    app = Flask(__name__, static_folder='static')
    app.config.from_object(config_class)

    # Initialize extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    bootstrap.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    # Configure Flask-Login
    login_manager.login_view = 'login'
    login_manager.login_message_category = 'info'

    with app.app_context():
        # Import routes and models to register them with the app
        from . import routes, models
        db.create_all()

    return app
