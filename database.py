from flask import Flask, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user
from autorisation import *
from config import *
from models import *

def add_user(username, email, password):
    hashed_password = generate_password_hash(password)
    new_user = Users(email=email, password=hashed_password, username=username)
    db.session.add(new_user)
    try:
        db.session.commit()
        return 200
    except Exception as e:
        print("ERROR", e)
        return 401

def login_user_db(email, password):
    user = Users.query.filter_by(email=email).first()
    print("Пользователь найден", user)
    if user and check_password_hash(user.password, password):
        login_user(user, remember=True)
        return user.ID, 200
    else:
        return "Пользователь не найден"
