from flask import Flask, make_response, request, flash, redirect, url_for, jsonify
from flask_login import current_user
import datetime
from datetime import timedelta
import jwt
from config import *
from models import *
from functools import wraps
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

# обновление access токена при его истечении
def update_access_token():
    refresh_token = request.cookies.get('refresh_token')

    if not refresh_token:
        return jsonify({'message': 'Refresh token is missing!'}), 403

    try:
        data = jwt.decode(refresh_token, ACCESS_TOKEN_SECRET_KEY, algorithms=['HS256'])
        user_id = data['user_id']

        # Генерируем новый access token
        print("Обновляем токен")
        new_access_token = generate_access_token(user_id)
        response = make_response(jsonify({'message': 'Token refreshed successfully!'}))
        return save_tokens(response, new_access_token, refresh_token)

    except:
        return jsonify({'message': 'Refresh token is invalid or expired!'}), 403

def update_access_token():
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        return jsonify({'message': 'Refresh token is missing!'}), 401

    try:
        data = jwt.decode(
            refresh_token, REFRESH_TOKEN_SECRET_KEY, algorithms=["HS256"])
        user_id = data['user_id']
        jti = data['jti']  # Извлечение UUID из токена
        user = Users.query.get(user_id)

        if user and user.refresh_token == refresh_token:
            new_access_token = jwt.encode({
                'user': {'id': user.id, 'email': user.email, 'username': user.username},
                'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRATION_TIME)
            }, ACCESS_TOKEN_SECRET_KEY, algorithm="HS256")

            return jsonify({"access_token": f"{new_access_token}"}), 200
        else:
            return jsonify({'message': 'Invalid refresh token!'}), 401
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Refresh token expired!'}), 401
    except Exception as e:
        return jsonify({'message': 'Invalid refresh token!'}), 401


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