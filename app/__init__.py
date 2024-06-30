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

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
bootstrap = Bootstrap()
login_manager = LoginManager()
mail = Mail()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_app(config_class='config.Config'):
    app = Flask(__name__, static_folder='static')
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    bootstrap.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    login_manager.login_view = 'login'
    login_manager.login_message_category = 'info'

    with app.app_context():
        from . import routes, models
        db.create_all()

    return app
