from flask import make_response, request, flash, redirect, url_for
import requests

import re
import os
import jwt
import base64
import markdown2
from PIL import Image
from fpdf import FPDF
from io import BytesIO
from functools import wraps


from config import *
from data.__all_models import *
from data.auth_services import *


# Перевод md в html для вывода
def markdown_to_html(text):
    return markdown2.markdown(text, extras=["fenced-code-blocks", "tables", "strike"])


# Конвертирование чекбоксов в нормальный вид
def convert_tasks(text):
    def replace_task(match):
        task_text = match.group(1)
        return f'<input type="checkbox"> {task_text}<br>'
    return re.sub(r'<t>(.*?)</t>', replace_task, text)


# Конвертирование диаграмм в нормальный вид
def convert_diagrams(text):
    def replace_diagram(match):
        chart_params = match.group(1)
        chart_params = re.sub(r'/\*.*?\*/', '', chart_params, flags=re.DOTALL)
        chart_params = ' '.join(chart_params.split())
        try:
            encoded_params = requests.utils.quote(chart_params)
            chart_url = f"https://quickchart.io/chart?width=400&c=   {encoded_params}"
            response = requests.get(chart_url)
            if response.status_code == 200:
                image_data = BytesIO(response.content)
                return f'<img src="data:image/png;base64,{base64.b64encode(image_data.getvalue()).decode("utf-8")}" alt="Chart">'
            else:
                return f'<div class="chart-error">Ошибка в диаграмме: Невозможно загрузить изображение.</div>'
        except Exception as e:
            return f'<div class="chart-error">Ошибка в диаграмме: {str(e)}</div>'
    return re.sub(r'<d>([\s\S]*?)</d>', replace_diagram, text)


# Извлечение диаграмм из текста
def extract_diagrams(text):
    diagram_pattern = r'<d>\s*({[\s\S]*?})\s*</d>'
    diagrams = []
    for match in re.finditer(diagram_pattern, text):
        chart_code = match.group(1)
        try:
            encoded_params = requests.utils.quote(chart_code.strip())
            url = f"https://quickchart.io/chart?width=600&c=    {encoded_params}"
            response = requests.get(url)
            if response.status_code == 200:
                image = Image.open(BytesIO(response.content))
                img_byte_arr = BytesIO()
                image.save(img_byte_arr, format='PNG')
                diagrams.append(img_byte_arr.getvalue())
        except Exception as e:
            print("Ошибка при загрузке диаграммы:", e)
    return diagrams


# Удаление тегов диаграмм из текста
def remove_diagram_tags(text):
    cleaned_text = re.sub(r'<d>[\s\S]*?</d>', '', text)
    return cleaned_text


# Получение пользователя из бд
def get_user():
    user = db.session.get(Users, jwt.decode(request.cookies.get("access_token", None),
                      ACCESS_TOKEN_SECRET_KEY, algorithms=["HS256"])['user_id'])
    return user

# Lекоратор для проверки наличия и актуальности access токена
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