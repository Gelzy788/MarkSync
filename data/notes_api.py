from flask import render_template, request, jsonify
from reportlab.platypus import Image as RLImage
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
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