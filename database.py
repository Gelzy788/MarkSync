import flask_sqlalchemy
from werkzeug.security import generate_password_hash
from config import *
from models import *

def add_user(username, email, password):
    print(0)
    hashed_password = generate_password_hash(password)
    print(1)
    new_user = Users(email=email, password=hashed_password, username=username)
    print(2)
    db.session.add(new_user)
    print(3)
    try:
        db.session.commit()
        return 500
    except Exception as e:
        print("ERROR", e)
        return 401