from flask import Flask, make_response, request, flash, redirect, url_for

from functools import wraps

from config import *
from data.__all_models import *

import jwt

from data.auth_services import *

# Получение пользователя из бд
def get_user():
    user = db.session.get(Users, jwt.decode(request.cookies.get("access_token", None),
                      ACCESS_TOKEN_SECRET_KEY, algorithms=["HS256"])['user_id'])
    return user

# декоратор для проверки наличия и актуальности access токена
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get("access_token")
        if not token:
            flash("Требуется авторизация", "error")
            return redirect(url_for('auth.login'))

        try:
            data = jwt.decode(token, ACCESS_TOKEN_SECRET_KEY, algorithms=["HS256"])  # Проверяет exp автоматически!
            user = Users.query.get(data["user_id"])
            if not user:
                flash("Пользователь не найден", "error")
                return redirect(url_for('auth.login'))
        except jwt.ExpiredSignatureError:
            # Попытка обновить токен через refresh_token
            refresh_token = request.cookies.get("refresh_token")
            
            try:
                refresh_data = jwt.decode(refresh_token, REFRESH_TOKEN_SECRET_KEY, algorithms=["HS256"])
                new_access_token = generate_access_token(refresh_data["user_id"])
                response = make_response(redirect(request.url))  # Редирект на ту же страницу
                save_tokens(response, new_access_token, refresh_token)
                print("Токен обновлен")
                return response
            except Exception:
                pass
            flash("Сессия истекла. Войдите снова", "error")
            return redirect(url_for('auth.login'))
        except jwt.InvalidTokenError:
            flash("Неверный токен", "error")
            return redirect(url_for('auth.login'))

        return f(user, *args, **kwargs)
    return decorated