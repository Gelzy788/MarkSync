from flask import Flask, make_response, request, flash, redirect, url_for, jsonify
from flask_login import current_user

import datetime
from datetime import timedelta
from functools import wraps

from config import *
from models import *

import jwt
import uuid

# Получение пользователя из бд
def get_user():
    user = db.session.get(Users, jwt.decode(request.cookies.get("access_token", None),
                      ACCESS_TOKEN_SECRET_KEY, algorithms=["HS256"])['user_id'])
    return user

# Генерация access token
def generate_access_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRATION_TIME)
    }
    token = jwt.encode(payload, ACCESS_TOKEN_SECRET_KEY, algorithm='HS256')
    return token

# Генерация refresh token
def generate_refresh_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.now() + timedelta(days=REFRESH_TOKEN_EXPIRATION_TIME),  # Refresh token действителен 7 дней
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
        samesite='Strict'   # Защита от CSRF-атак
    )

    response.set_cookie(
        'refresh_token',
        refresh_token,
        httponly=True,  # Куки недоступны через JavaScript
        secure=True,    # Куки передаются только по HTTPS (в production)
        samesite='Strict'   # Защита от CSRF-атак
    )

    print("Токены сохранены!", response)
    return response

# декоратор для проверки наличия и актуальности access токена
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get("access_token")
        if not token:
            flash("Требуется авторизация", "error")
            return redirect(url_for('login'))

        try:
            data = jwt.decode(token, ACCESS_TOKEN_SECRET_KEY, algorithms=["HS256"])  # Проверяет exp автоматически!
            user = Users.query.get(data["user_id"])
            if not user:
                flash("Пользователь не найден", "error")
                return redirect(url_for('login'))
        except jwt.ExpiredSignatureError:
            # Попытка обновить токен через refresh_token
            refresh_token = request.cookies.get("refresh_token")
            
            if refresh_token == Users.get_refresh_token():
                try:
                    refresh_data = jwt.decode(refresh_token, REFRESH_TOKEN_SECRET_KEY, algorithms=["HS256"])
                    new_access_token = generate_access_token(refresh_data["user_id"])
                    response = make_response(redirect(request.url))  # Редирект на ту же страницу
                    save_tokens(response, new_access_token, refresh_token)
                    print("Токен обновлен")
                    return response
                except:
                    pass
            flash("Сессия истекла. Войдите снова", "error")
            return redirect(url_for('login'))
        except jwt.InvalidTokenError:
            flash("Неверный токен", "error")
            return redirect(url_for('login'))

        return f(user, *args, **kwargs)
    return decorated