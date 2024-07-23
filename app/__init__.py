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
    app = Flask(__name__, static_folder='static')
    app.config.from_object(config_class)

    print(f"SQLALCHEMY_DATABASE_URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"MAIL_USERNAME: {app.config['MAIL_USERNAME']}")
    print(f"MAIL_PASSWORD: {app.config['MAIL_PASSWORD']}")
    print(f"SECRET_KEY: {app.config['SECRET_KEY']}")

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

    with app.app_context():
        # Import models after initializing db
        from .models import Worker

        @login_manager.user_loader
        def load_user(user_id):
            return Worker.query.get(int(user_id))

        # Import routes and register blueprints
        from .routes.admin import admin_bp
        from .routes.auth import auth_bp
        from .routes.misc import misc_bp
        from .routes.events import events_bp
        from .routes.profile import profile_bp
        from .routes.errorhandlers import error_bp
        from .routes.backup_routes import backup_bp
        from .routes.base import base_bp  # Import the base blueprint

        app.register_blueprint(admin_bp)
        app.register_blueprint(auth_bp)
        app.register_blueprint(misc_bp)
        app.register_blueprint(events_bp)
        app.register_blueprint(profile_bp)
        app.register_blueprint(error_bp)
        app.register_blueprint(backup_bp)
        app.register_blueprint(base_bp)  # Register the base blueprint

    # Register CLI commands
    from .update_db import register_commands as update_db_commands
    from .populate_db import register_commands as populate_db_commands
    update_db_commands(app)
    populate_db_commands(app)

    return app

# Set up logging
import logging
logging.basicConfig(level=logging.DEBUG)
