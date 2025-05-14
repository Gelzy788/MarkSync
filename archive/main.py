from flask import Blueprint, render_template, request, jsonify
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from bs4 import BeautifulSoup
import os
import base64
import tempfile
import traceback
from io import BytesIO

from data.utils import markdown_to_html, convert_tasks, convert_diagrams

main_blueprint = Blueprint('main', __name__)

pdfmetrics.registerFont(TTFont('DejaVuSans', 'data/dejavu-sans/DejaVuSans.ttf'))

@main_blueprint.route('/editor', methods=['GET', 'POST'])
def editor():
    html = ""
    text = ""
    if request.method == 'POST':
        text = request.form['text']
        text = convert_tasks(text)
        text = convert_diagrams(text)
        html = markdown_to_html(text)
    return render_template('editor.html', text=text, html=html)

@main_blueprint.route('/save', methods=['POST'])
def save_file():
    filename = request.form['filename']
    text = request.form['text']
    if not filename.endswith('.md'):
        filename += '.md'
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(text)
    return jsonify({"message": f"Файл '{filename}' сохранён!"})

@main_blueprint.route('/save_pdf', methods=['POST'])
def save_pdf():
    filename = request.form.get('filename')
    html_content = request.form.get('html')
    if not filename or not html_content:
        return jsonify({"error": "Файл или HTML-контент отсутствует."}), 400
    try:
        pdf_path = filename
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        normal_style = styles['Normal']
        normal_style.fontName = 'DejaVuSans'
        normal_style.fontSize = 12
        story = []
        soup = BeautifulSoup(html_content, 'html.parser')
        for element in soup:
            if element.name == 'img' and element.get('src', '').startswith('data:image'):
                image_data = element['src'].split(',')[1]
                image_bytes = base64.b64decode(image_data)
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                    temp_file.write(image_bytes)
                    temp_file_path = temp_file.name
                story.append(RLImage(temp_file_path, width=400, height=300))
                story.append(Spacer(1, 12))
                os.unlink(temp_file_path)
            elif element.string:
                story.append(Paragraph(element.string.strip(), normal_style))
                story.append(Spacer(1, 12))
        doc.build(story)
        return jsonify({"message": f"Файл '{filename}' успешно сохранён в формате PDF!"})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@main_blueprint.route('/load', methods=['POST'])
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

@main_blueprint.route('/list_files', methods=['POST'])
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

@main_blueprint.route('/delete', methods=['POST'])
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

@main_blueprint.route('/create_folder', methods=['POST'])
def create_folder():
    folder_name = request.form['folder_name']
    directory = request.form.get('directory', '.')
    full_path = os.path.join(directory, folder_name)
    try:
        os.makedirs(full_path, exist_ok=True)
        return jsonify({"message": f"Папка '{full_path}' создана!"})
    except Exception as e:
        return jsonify({"error": str(e)})