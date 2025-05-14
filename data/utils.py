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


# Генерация pdf из текста
def generate_pdf_from_markdown(text, diagrams_bytes, filename="output.pdf"):
    text = remove_diagram_tags(text)
    pdf = FPDF()
    pdf.add_font('DejaVu', '', 'data/dejavu-sans/DejaVuSans.ttf', uni=True)
    pdf.set_font('DejaVu', size=12)
    pdf.add_page()
    html_content = markdown2.markdown(text)

    lines = []
    in_tag = False
    current_line = ""
    buffer = ""

    for char in html_content:
        if char == "<":
            in_tag = True
            if current_line.strip():
                lines.append(current_line.strip())
                current_line = ""
        elif char == ">":
            in_tag = False
            continue
        elif not in_tag:
            if char == "\n":
                if current_line.strip():
                    lines.append(current_line.strip())
                    current_line = ""
            else:
                current_line += char
        buffer += char
        if "ul" in buffer or "ol" in buffer or "li" in buffer:
            if current_line.strip():
                lines.append(current_line.strip())
            buffer = ""

    if current_line.strip():
        lines.append(current_line.strip())

    for line in lines:
        if line.startswith("<h1>"):
            pdf.set_font_size(16)
            pdf.cell(0, 10, txt=line[4:-5], ln=1, align='L')
            pdf.set_font_size(12)
        elif line.startswith("<h2>"):
            pdf.set_font_size(14)
            pdf.cell(0, 10, txt=line[4:-5], ln=1, align='L')
            pdf.set_font_size(12)
        elif line.startswith("<h3>"):
            pdf.set_font_size(13)
            pdf.cell(0, 10, txt=line[4:-5], ln=1, align='L')
            pdf.set_font_size(12)
        elif line.startswith("<li>"):
            pdf.cell(0, 10, txt=f"- {line[4:-5]}", ln=1, align='L')
        elif line.strip():
            wrapped_lines = wrap_text(pdf, line, pdf.w - 2 * 20)
            for wl in wrapped_lines:
                pdf.cell(0, 10, txt=wl, ln=1, align='L')

    for img_data in diagrams_bytes:
        pdf.add_page()
        temp_img_path = "temp_chart.png"
        with open(temp_img_path, "wb") as img_file:
            img_file.write(img_data)
        try:
            pdf.image(temp_img_path, x=10, w=180)
        except Exception as e:
            print("Ошибка при добавлении изображения:", e)
        finally:
            os.remove(temp_img_path)

    pdf.output(filename)
    return filename


# Перенос текста по ширине
def wrap_text(pdf, text, max_width):
    words = text.split()
    lines = []
    current_line = ''

    for word in words:
        test_line = f"{current_line} {word}".strip()
        if pdf.get_string_width(test_line) > max_width:
            lines.append(current_line)
            current_line = word
        else:
            current_line = test_line
    if current_line:
        lines.append(current_line)
    return lines


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