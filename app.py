from config import *
from data.__all_models import *
from data.users import Users
from data.notes import Notes
from data.notes_access import NotesAccess
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


# Страница с заметками
@app.route('/marks', methods=['GET', 'POST'])
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


@app.route('/api/notes/<int:note_id>/access', methods=['GET', 'POST'])
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

@app.route('/api/notes/<int:note_id>/access/<int:user_id>', methods=['DELETE'])
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


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', ssl_context=('ssl/cert.pem', 'ssl/key.pem'))