from config import *
from data.__all_models import *
from forms.register_form import *
from data import auth_blueprint, notes_blueprint
from data.utils import convert_diagrams, convert_tasks, token_required
import markdown2
from data.utils import extract_diagrams, generate_pdf_from_markdown
from flask import render_template, request, jsonify, send_file

# Загрузка микро-приложений
app.register_blueprint(auth_blueprint)
app.register_blueprint(notes_blueprint)

# Главная страница
@app.route('/')
def main():
    return render_template('main.html', title="Главная страница")

# Страница профиля
@app.route('/profile')
@token_required
def profile(user):
    return render_template('profile.html', username=user.username, email=user.email, title="Профиль")


@app.route('/protected')
@token_required
def protected(user):
    return jsonify({'message': f'Hello, {user.username}! This is a protected API endpoint.'})


# Страница с заметками
@app.route('/marks', methods=['GET', 'POST'])
@token_required
def marks(user):
    files = Notes.query.filter_by(user_id=user.ID).all()
    notes_accesses = NotesAccess.query.filter_by(user_id=user.ID).all()
    for i in notes_accesses:
        # print(Notes.query.filter_by(ID=i.note_id).first())
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


# вспомогательная функция взимодействия с заметками
@app.route('/preview', methods=['POST'])
@token_required
def preview(user):
    data = request.get_json()
    text = data.get('text', '')
    processed_text = convert_tasks(text)
    processed_text = convert_diagrams(processed_text)
    html = markdown2.markdown(processed_text, extras=["fenced-code-blocks", "tables", "strike"])
    return jsonify({'html': html})


# Вспомогательная фнкция загрузки заметок из бд
@app.route('/api/notes')
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
@app.route('/save_on_server', methods=['POST'])
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
@app.route('/export_pdf')
@token_required
def export_pdf(user):
    text = request.args.get('text', '')
    if not text:
        return jsonify({"error": "Нет текста для экспорта"}), 400
    diagrams = extract_diagrams(text)
    pdf_path = generate_pdf_from_markdown(text, diagrams)
    return send_file(pdf_path, as_attachment=True, download_name="document.pdf")
    

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', ssl_context=('ssl/cert.pem', 'ssl/key.pem'))