import datetime
from datetime import timedelta

from config import *
from data.users import Users
from data.notes import Notes
from data.notes_access import NotesAccess

import jwt
import uuid

from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import update


# Добавление пользователя в бд
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

# Получение id пользователя для авторизации 
def login_user_db(email, password):
    user = Users.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
        return user.ID, 200
    else:
        return "Пользователь не найден"

# Генерация access token
def generate_access_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRATION_TIME)
    }
    token = jwt.encode(payload, ACCESS_TOKEN_SECRET_KEY, algorithm='HS256')
    return token

# Генерация refresh token
def generate_refresh_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.now() + timedelta(days=REFRESH_TOKEN_EXPIRATION_TIME),  # Refresh token действителен 7 дней
        'iti': str(uuid.uuid4())
    }
    token = jwt.encode(payload, REFRESH_TOKEN_SECRET_KEY, algorithm='HS256')
    return token

# Сохранение токенов в cookie 
def save_tokens(response, access_token, refresh_token):
    response.set_cookie(
        'access_token',
        access_token,
        httponly=True,  # Куки недоступны через JavaScript
        secure=True,    # Куки передаются только по HTTPS (в production)
        samesite='None'   # Защита от CSRF-атак
    )

    response.set_cookie(
        'refresh_token',
        refresh_token,
        httponly=True,  # Куки недоступны через JavaScript
        secure=True,    # Куки передаются только по HTTPS (в production)
        samesite='None'   # Защита от CSRF-атак
    )

    print("Токены сохранены!", response)
    return response


# Добавление refresh токена в бд
def add_refresh_token_db(email, refresh_token):
    stmt = (
        update(Users)
        # Используем атрибут напрямую
        .where(Users.email == email)
        .values(
            refresh_token = refresh_token
        )
    )

    try:
        db.session.execute(stmt)  # Выполняем запрос
        db.session.commit()  # Зафиксируйте изменения
        return True
    except Exception as e:
        print('ОТКАТЫВАЮ ИЗМЕНЕНИЯ...', e)
        db.session.rollback()  # Откатите изменения в случае ошибки
        return str(e)