import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_mail import Mail
from dotenv import load_dotenv
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
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    from .models import Worker  # Import models after initializing db

    @login_manager.user_loader
    def load_user(user_id):
        return Worker.query.get(int(user_id))

    with app.app_context():
        # Import routes and models to register them with the app
        from .routes.admin import admin_bp
        from .routes.auth import auth_bp
        from .routes.misc import misc_bp
        from .routes.events import events_bp
        from .routes.profile import profile_bp
        from .routes.errorhandlers import error_bp

        app.register_blueprint(admin_bp)
        app.register_blueprint(auth_bp)
        app.register_blueprint(misc_bp)
        app.register_blueprint(events_bp)
        app.register_blueprint(profile_bp)
        app.register_blueprint(error_bp)

        db.create_all()

    return app

# Set up logging
logging.basicConfig(level=logging.DEBUG)
