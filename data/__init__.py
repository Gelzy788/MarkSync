from flask import Blueprint

auth_blueprint = Blueprint('auth', __name__, url_prefix='/auth') # Блюпринт системы авторизации
notes_blueprint = Blueprint('main', __name__) # Блюпринт системы заметок


from data.auth_api import *
from data.notes_api import *