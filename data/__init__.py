from flask import Blueprint

auth_blueprint = Blueprint('auth', __name__, url_prefix='/auth')
notes_blueprint = Blueprint('main', __name__)

from data.auth_api import *
from data.notes_api import *