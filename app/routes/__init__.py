from flask import Blueprint

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
events_bp = Blueprint('events', __name__, url_prefix='/events')
profile_bp = Blueprint('profile', __name__, url_prefix='/profile')
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
misc_bp = Blueprint('misc', __name__)

from .auth import *
from .events import *
from .profile import *
from .admin import *
from .misc import *
