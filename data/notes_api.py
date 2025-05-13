from flask import Blueprint, render_template, request, jsonify, Response
from reportlab.platypus import Image as RLImage
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import traceback
from urllib.parse import quote
import re
from . import notes_blueprint
from utils import markdown_to_html, convert_tasks, convert_diagrams


try:
    pdfmetrics.getFont('DejaVuSans')
except Exception:
    font_path = 'data/dejavu-sans/DejaVuSans.ttf'
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
    else:
        print("Шрифт не найден:", font_path)

def encode_filename(filename):
    """Кодируем имя файла для заголовка Content-Disposition"""
    safe_filename = re.sub(r'[^\w\.\-\_]', '_', filename)
    return quote(safe_filename)

@notes_blueprint.route('/editor', methods=['GET', 'POST'])
def editor():
    html = ""
    text = ""
    if request.method == 'POST':
        text = request.form['text']
        text = convert_tasks(text)
        text = convert_diagrams(text)
        html = markdown_to_html(text)
    return render_template('editor.html', text=text, html=html)

@notes_blueprint.route('/save', methods=['POST'])
def save_file():
    filename = request.form['filename']
    text = request.form['text']
    if not filename.endswith('.md'):
        filename += '.md'
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(text)
    return jsonify({"message": f"Файл '{filename}' сохранён!"})

@notes_blueprint.route('/load', methods=['POST'])
def load_file():
    filename = request.form['filename']
    if os.path.exists(filename):
        encodings = ['utf-8', 'windows-1251', 'latin1']
        for encoding in encodings:
            try:
                with open(filename, 'r', encoding=encoding) as f:
                    text = f.read()
                return jsonify({"text": text})
            except UnicodeDecodeError:
                continue
        return jsonify({"error": "Не удалось определить кодировку файла."})
    return jsonify({"message": "Файл не найден!"})

@notes_blueprint.route('/list_files', methods=['POST'])
def list_files():
    directory = request.form.get('directory', '.')
    if not os.path.exists(directory):
        return jsonify({"error": "Directory not found"})
    files_and_folders = []
    for item in os.listdir(directory):
        full_path = os.path.join(directory, item)
        if os.path.isdir(full_path):
            files_and_folders.append(f"\\{item}")
        elif item.endswith('.md') or item.endswith('.pdf'):
            files_and_folders.append(item)
    return jsonify({"files": files_and_folders})

@notes_blueprint.route('/delete', methods=['POST'])
def delete_file_or_folder():
    path = request.form['path']
    if os.path.exists(path):
        if os.path.isfile(path):
            os.remove(path)
            return jsonify({"message": f"Файл '{path}' удален!"})
        elif os.path.isdir(path):
            os.rmdir(path)
            return jsonify({"message": f"Папка '{path}' удалена!"})
    return jsonify({"error": f"Путь '{path}' не найден!"})

@notes_blueprint.route('/create_folder', methods=['POST'])
def create_folder():
    folder_name = request.form['folder_name']
    directory = request.form.get('directory', '.')
    full_path = os.path.join(directory, folder_name)
    try:
        os.makedirs(full_path, exist_ok=True)
        return jsonify({"message": f"Папка '{full_path}' создана!"})
    except Exception as e:
        return jsonify({"error": str(e)})