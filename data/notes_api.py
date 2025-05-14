from flask import render_template, request, jsonify, send_file

from reportlab.platypus import Image as RLImage
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import re
import os
from urllib.parse import quote

import markdown2

from config import db
from data.notes import Notes
from data.users import Users
from . import notes_blueprint
from data.notes_access import NotesAccess
from data.utils import markdown_to_html, convert_tasks, convert_diagrams, extract_diagrams, generate_pdf_from_markdown, token_required


# Подключение шрифта для сохранения заметок в pdf формате
try:
    pdfmetrics.getFont('DejaVuSans')
except Exception:
    font_path = 'data/dejavu-sans/DejaVuSans.ttf'
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
    else:
        print("Шрифт не найден:", font_path)


# Страница с заметками
# @app.route('/marks', methods=['GET', 'POST'])
@notes_blueprint.route('/marks', methods=['GET', 'POST'])
@token_required
def marks(user):
    files = Notes.query.filter_by(user_id=user.ID).all()
    notes_accesses = NotesAccess.query.filter_by(user_id=user.ID).all()
    for i in notes_accesses:
        note = Notes.query.filter_by(ID=i.note_id).first()
        if note:
            files.append(note)
    
    text = ''
    html = ''
    if request.method == 'POST':
        text = request.form['text']
        text = convert_tasks(text)
        text = convert_diagrams(text)
        html = markdown2.markdown(text, extras=["fenced-code-blocks", "tables", "strike"])
    print([i.ID for i in files])
    return render_template('editor.html', text=text, html=html, files=files)


# Выдача досутпа к заметке
@notes_blueprint.route('/api/notes/<int:note_id>/access', methods=['GET', 'POST'])
@token_required
def note_access(user, note_id):
    note = Notes.query.filter_by(ID=note_id).first()
    if not note:
        return jsonify({'status': 'error', 'message': 'Заметка не найдена'}), 404
    
    # Проверка, что пользователь - владелец заметки
    if note.user_id != user.ID:
        return jsonify({'status': 'error', 'message': 'Нет прав доступа'}), 403

    if request.method == 'GET':
        # Получаем список пользователей с доступом
        accesses = NotesAccess.query.filter_by(note_id=note_id).all()
        users = []
        for access in accesses:
            user = db.session.get(Users, access.user_id)
            if user:
                users.append({'id': user.ID, 'username': user.username})
        return jsonify({'users': users})
    
    elif request.method == 'POST':
        # Добавляем доступ для пользователя
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'status': 'error', 'message': 'ID пользователя не указан'}), 400
        
        # Проверяем, что пользователь существует
        target_user = db.session.get(Users, user_id)
        if not target_user:
            return jsonify({'status': 'error', 'message': 'Пользователь не найден'}), 404
        
        # Проверяем, что доступ еще не выдан
        existing_access = NotesAccess.query.filter_by(note_id=note_id, user_id=user_id).first()
        if existing_access:
            return jsonify({'status': 'error', 'message': 'Доступ уже предоставлен'}), 400
        
        new_access = NotesAccess(note_id=note_id, user_id=user_id, access_level='admin')
        db.session.add(new_access)
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': 'Доступ предоставлен'})


# Удаление доступа к заметке
@notes_blueprint.route('/api/notes/<int:note_id>/access/<int:user_id>', methods=['DELETE'])
@token_required
def remove_note_access(user, note_id, user_id):
    note = Notes.query.filter_by(ID=note_id).first()
    if not note:
        return jsonify({'status': 'error', 'message': 'Заметка не найдена'}), 404
    
    # Проверка, что пользователь - владелец заметки
    if note.user_id != user.ID:
        return jsonify({'status': 'error', 'message': 'Нет прав доступа'}), 403
    
    access = NotesAccess.query.filter_by(note_id=note_id, user_id=user_id).first()
    if not access:
        return jsonify({'status': 'error', 'message': 'Доступ не найден'}), 404
    
    db.session.delete(access)
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': 'Доступ удален'})

# Функция для кодирования имени файла
def encode_filename(filename):
    safe_filename = re.sub(r'[^\w\.\-\_]', '_', filename)
    return quote(safe_filename)

# Страница заметок
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

# Сохранение файла на компьютер
@notes_blueprint.route('/save', methods=['POST'])
def save_file():
    filename = request.form['filename']
    text = request.form['text']
    if not filename.endswith('.md'):
        filename += '.md'
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(text)
    return jsonify({"message": f"Файл '{filename}' сохранён!"})


# Загрузка файла с диска на сервер
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


# вспомогательная функция взимодействия с заметками
@notes_blueprint.route('/preview', methods=['POST'])
@token_required
def preview(user):
    data = request.get_json()
    text = data.get('text', '')
    processed_text = convert_tasks(text)
    processed_text = convert_diagrams(processed_text)
    html = markdown2.markdown(processed_text, extras=["fenced-code-blocks", "tables", "strike"])
    return jsonify({'html': html})


# Вспомогательная фнкция загрузки заметок из бд
@notes_blueprint.route('/api/notes')
@token_required
def api_notes(user):
    # Собственные заметки пользователя
    notes = Notes.query.filter_by(user_id=user.ID).all()
    
    # Заметки, к которым у пользователя есть доступ
    notes_accesses = NotesAccess.query.filter_by(user_id=user.ID).all()
    for access in notes_accesses:
        note = Notes.query.filter_by(ID=access.note_id).first()
        if note and note not in notes:  # Проверяем, чтобы не было дубликатов
            notes.append(note)
    
    return jsonify({'notes': [{'name': note.name, 'text': note.text, 'id': note.ID} for note in notes]})


# Функция сохранения файлов в бд
@notes_blueprint.route('/save_on_server', methods=['POST'])
@token_required
def save_on_server(user):
    filename = request.form['filename']
    text = request.form['text']
    note_id = request.form.get('note_id')
    existing_note = Notes.query.filter_by(ID=note_id).first()
    
    if existing_note:
        existing_note.text = text
    else:
        new_note = Notes(name=filename, text=text, user_id=user.ID)
        db.session.add(new_note)
    
    try:
        db.session.commit()
        # Возвращаем ID заметки (новой или существующей)
        return jsonify({
            'status': 'success', 
            'message': 'Заметка сохранена',
            'id': existing_note.ID if existing_note else new_note.ID
        }), 200
    except Exception as e:
        print("ERROR", e)
        db.session.rollback()
        return jsonify({'status': 'error', 'message': 'Ошибка сохранения'}), 500


# Функция сохранения в pdf
@notes_blueprint.route('/export_pdf')
@token_required
def export_pdf(user):
    text = request.args.get('text', '')
    if not text:
        return jsonify({"error": "Нет текста для экспорта"}), 400
    diagrams = extract_diagrams(text)
    pdf_path = generate_pdf_from_markdown(text, diagrams)
    return send_file(pdf_path, as_attachment=True, download_name="document.pdf")